import queue
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, cast

import cv2
import numpy as np
import onnxruntime as ort


@dataclass
class InferenceRequest:
    request_id: str
    source_path: str
    source_type: str
    source_bgr: np.ndarray
    threshold: float
    nms_iou: float
    high_conf_thr: float
    model_name: str


@dataclass
class InferenceResult:
    request_id: str
    source_path: str
    source_type: str
    annotated_bgr: Optional[np.ndarray]
    boxes: np.ndarray
    scores: np.ndarray
    kept_indices: np.ndarray
    high_count: int
    low_count: int
    top_score: float
    avg_score: float
    count: int
    details: list[dict]
    latency_ms: float
    summary_text: str
    error: Optional[str]


def preprocess_image(image_bgr: np.ndarray, size: int = 800) -> np.ndarray:
    rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
    img = cv2.resize(rgb, (size, size)).astype("float32") / 255.0
    mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
    std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
    img = (img - mean) / std
    img = np.transpose(img, (2, 0, 1))
    return img[np.newaxis, ...].astype("float32")


def iou(a: np.ndarray, b: np.ndarray) -> float:
    x1 = max(float(a[0]), float(b[0]))
    y1 = max(float(a[1]), float(b[1]))
    x2 = min(float(a[2]), float(b[2]))
    y2 = min(float(a[3]), float(b[3]))
    iw = max(0.0, x2 - x1)
    ih = max(0.0, y2 - y1)
    inter = iw * ih
    area_a = max(0.0, float(a[2] - a[0])) * max(0.0, float(a[3] - a[1]))
    area_b = max(0.0, float(b[2] - b[0])) * max(0.0, float(b[3] - b[1]))
    denom = area_a + area_b - inter
    return inter / denom if denom > 0 else 0.0


def nms_indices(
    boxes: np.ndarray, scores: np.ndarray, score_thr: float, iou_thr: float
) -> np.ndarray:
    idx = np.where(scores >= score_thr)[0]
    if idx.size == 0:
        return np.array([], dtype=np.int64)
    idx = idx[np.argsort(scores[idx])[::-1]]
    keep = []
    while idx.size > 0:
        cur = idx[0]
        keep.append(int(cur))
        rest = idx[1:]
        filtered = []
        for j in rest:
            if iou(boxes[cur], boxes[j]) <= iou_thr:
                filtered.append(int(j))
        idx = np.array(filtered, dtype=np.int64)
    return np.array(keep, dtype=np.int64)


def draw_annotated_with_panel(
    src_bgr: np.ndarray,
    boxes_800: np.ndarray,
    scores: np.ndarray,
    keep: np.ndarray,
    high_conf_thr: float,
    model_name: str,
    score_thr: float,
    nms_iou: float,
) -> tuple[np.ndarray, int, int, float, list[dict], str]:
    image = src_bgr.copy()
    h, w = image.shape[:2]

    details: list[dict] = []
    high_count = 0
    low_count = 0

    for i in keep:
        b = boxes_800[i]
        s = float(scores[i])
        x1 = int(b[0] * (w / 800.0))
        y1 = int(b[1] * (h / 800.0))
        x2 = int(b[2] * (w / 800.0))
        y2 = int(b[3] * (h / 800.0))

        if s >= high_conf_thr:
            level = "A"
            color = (46, 204, 113)
            high_count += 1
        else:
            level = "B"
            color = (0, 165, 255)
            low_count += 1

        cv2.rectangle(image, (x1, y1), (x2, y2), color, 2)
        cv2.putText(
            image,
            f"{level}:{s:.2f}",
            (x1, max(0, y1 - 8)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            color,
            2,
        )

        details.append(
            {
                "level": level,
                "score": s,
                "box_xyxy": [x1, y1, x2, y2],
            }
        )

    avg_score = float(np.mean(scores[keep])) if keep.size > 0 else 0.0

    panel_w = 460
    canvas = np.full((h, w + panel_w, 3), 255, dtype=np.uint8)
    canvas[:, :w] = image
    cv2.line(canvas, (w, 0), (w, h), (220, 220, 220), 2)

    text_lines = [
        "Image Report",
        f"Model: {model_name}",
        f"Threshold: {score_thr:.2f}",
        f"NMS IoU: {nms_iou:.2f}",
        "",
        f"Total Colonies: {int(keep.size)}",
        f"A (high confidence): {high_count}",
        f"B (regular confidence): {low_count}",
        f"Top score: {float(scores.max() if scores.size > 0 else 0.0):.3f}",
        f"Avg score: {avg_score:.3f}",
        "",
        "Legend:",
        "A >= high-threshold (green)",
        "B >= score-threshold (orange)",
        "",
        "Top detections:",
    ]
    for idx, d in enumerate(details[:10], start=1):
        bx = d["box_xyxy"]
        text_lines.append(
            f"{idx:02d}. {d['level']} s={d['score']:.2f} "
            f"[{bx[0]},{bx[1]},{bx[2]},{bx[3]}]"
        )

    x0 = w + 14
    y = 30
    for line in text_lines:
        cv2.putText(
            canvas,
            line,
            (x0, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.58,
            (40, 40, 40),
            1,
            cv2.LINE_AA,
        )
        y += 26
        if y >= h - 10:
            break

    summary_text = (
        f"count={int(keep.size)}, A={high_count}, B={low_count}, "
        f"top={float(scores.max() if scores.size > 0 else 0.0):.3f}, avg={avg_score:.3f}"
    )
    return canvas, high_count, low_count, avg_score, details, summary_text


class InferenceService:
    def __init__(self, model_path: str, intra_threads: int = 4, inter_threads: int = 1):
        self.model_path = model_path
        self.intra_threads = intra_threads
        self.inter_threads = inter_threads
        self._requests: "queue.Queue[InferenceRequest]" = queue.Queue(maxsize=2)
        self._results: "queue.Queue[InferenceResult]" = queue.Queue(maxsize=6)
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._sess: Optional[ort.InferenceSession] = None
        self._input_name: Optional[str] = None

    def start(self) -> bool:
        if self._running:
            return True
        if not Path(self.model_path).exists():
            return False
        so = ort.SessionOptions()
        if self.intra_threads > 0:
            so.intra_op_num_threads = self.intra_threads
        if self.inter_threads > 0:
            so.inter_op_num_threads = self.inter_threads
        self._sess = ort.InferenceSession(
            self.model_path, sess_options=so, providers=["CPUExecutionProvider"]
        )
        self._input_name = self._sess.get_inputs()[0].name
        self._running = True
        self._thread = threading.Thread(
            target=self._loop, name="inference-loop", daemon=True
        )
        self._thread.start()
        return True

    def stop(self) -> None:
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=1.5)
            self._thread = None
        self._sess = None
        self._input_name = None

    def submit(self, req: InferenceRequest) -> bool:
        if not self._running:
            return False
        try:
            self._requests.put_nowait(req)
            return True
        except queue.Full:
            return False

    def try_get_result(self) -> Optional[InferenceResult]:
        try:
            return self._results.get_nowait()
        except queue.Empty:
            return None

    def _loop(self) -> None:
        assert self._sess is not None
        assert self._input_name is not None
        while self._running:
            try:
                req = self._requests.get(timeout=0.1)
            except queue.Empty:
                continue
            t0 = time.perf_counter()
            try:
                inp = preprocess_image(req.source_bgr)
                outs = cast(
                    list[np.ndarray], self._sess.run(None, {self._input_name: inp})
                )
                boxes = outs[0][0]
                scores = outs[2][0]
                keep = nms_indices(boxes, scores, req.threshold, req.nms_iou)
                annotated, high_count, low_count, avg_score, details, summary_text = (
                    draw_annotated_with_panel(
                        src_bgr=req.source_bgr,
                        boxes_800=boxes,
                        scores=scores,
                        keep=keep,
                        high_conf_thr=req.high_conf_thr,
                        model_name=req.model_name,
                        score_thr=req.threshold,
                        nms_iou=req.nms_iou,
                    )
                )
                latency_ms = (time.perf_counter() - t0) * 1000.0
                result = InferenceResult(
                    request_id=req.request_id,
                    source_path=req.source_path,
                    source_type=req.source_type,
                    annotated_bgr=annotated,
                    boxes=boxes,
                    scores=scores,
                    kept_indices=keep,
                    high_count=high_count,
                    low_count=low_count,
                    top_score=float(scores.max() if scores.size > 0 else 0.0),
                    avg_score=avg_score,
                    count=int(keep.size),
                    details=details,
                    latency_ms=latency_ms,
                    summary_text=summary_text,
                    error=None,
                )
            except Exception as e:
                result = InferenceResult(
                    request_id=req.request_id,
                    source_path=req.source_path,
                    source_type=req.source_type,
                    annotated_bgr=None,
                    boxes=np.zeros((0, 4), dtype=np.float32),
                    scores=np.zeros((0,), dtype=np.float32),
                    kept_indices=np.zeros((0,), dtype=np.int64),
                    high_count=0,
                    low_count=0,
                    top_score=0.0,
                    avg_score=0.0,
                    count=0,
                    details=[],
                    latency_ms=0.0,
                    summary_text="",
                    error=str(e),
                )

            try:
                self._results.put_nowait(result)
            except queue.Full:
                pass
