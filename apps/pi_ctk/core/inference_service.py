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


def preprocess_image(image_bgr: np.ndarray, size: int) -> np.ndarray:
    rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
    resized = cv2.resize(rgb, (size, size), interpolation=cv2.INTER_LINEAR)

    img = resized.astype(np.float32)
    img *= 1.0 / 255.0
    img -= np.array([0.485, 0.456, 0.406], dtype=np.float32)
    img /= np.array([0.229, 0.224, 0.225], dtype=np.float32)

    img = np.transpose(img, (2, 0, 1))
    return np.expand_dims(img, axis=0)


def resolve_input_size(session: ort.InferenceSession) -> int:
    shape = session.get_inputs()[0].shape
    if len(shape) >= 4:
        h = shape[-2]
        w = shape[-1]
        if isinstance(h, int) and isinstance(w, int) and h > 0 and h == w:
            return int(h)
    raise RuntimeError(f"无法从模型输入形状推断尺寸: {shape}")


def squeeze_batch(arr: np.ndarray) -> np.ndarray:
    if arr.ndim >= 1 and arr.shape[0] == 1:
        return arr[0]
    return arr


def xywh_to_xyxy(boxes_xywh: np.ndarray) -> np.ndarray:
    boxes = boxes_xywh.astype(np.float32, copy=True)
    cx = boxes[:, 0]
    cy = boxes[:, 1]
    w = boxes[:, 2]
    h = boxes[:, 3]
    boxes[:, 0] = cx - (w / 2.0)
    boxes[:, 1] = cy - (h / 2.0)
    boxes[:, 2] = cx + (w / 2.0)
    boxes[:, 3] = cy + (h / 2.0)
    return boxes


def nms_xyxy(boxes: np.ndarray, scores: np.ndarray, iou_thr: float) -> np.ndarray:
    if boxes.size == 0 or scores.size == 0:
        return np.zeros((0,), dtype=np.int64)

    x1 = boxes[:, 0]
    y1 = boxes[:, 1]
    x2 = boxes[:, 2]
    y2 = boxes[:, 3]
    areas = np.maximum(0.0, x2 - x1) * np.maximum(0.0, y2 - y1)
    order = scores.argsort()[::-1]
    keep: list[int] = []

    while order.size > 0:
        i = int(order[0])
        keep.append(i)
        if order.size == 1:
            break

        rest = order[1:]
        xx1 = np.maximum(x1[i], x1[rest])
        yy1 = np.maximum(y1[i], y1[rest])
        xx2 = np.minimum(x2[i], x2[rest])
        yy2 = np.minimum(y2[i], y2[rest])

        inter_w = np.maximum(0.0, xx2 - xx1)
        inter_h = np.maximum(0.0, yy2 - yy1)
        inter = inter_w * inter_h
        union = areas[i] + areas[rest] - inter
        iou = np.divide(inter, union, out=np.zeros_like(inter), where=union > 0)
        order = rest[iou <= iou_thr]

    return np.asarray(keep, dtype=np.int64)


def scale_boxes_to_source(
    boxes: np.ndarray, src_w: int, src_h: int, input_size: int
) -> np.ndarray:
    scaled = boxes.astype(np.float32, copy=True)
    scaled[:, [0, 2]] *= src_w / float(input_size)
    scaled[:, [1, 3]] *= src_h / float(input_size)
    scaled[:, [0, 2]] = np.clip(scaled[:, [0, 2]], 0, max(src_w - 1, 0))
    scaled[:, [1, 3]] = np.clip(scaled[:, [1, 3]], 0, max(src_h - 1, 0))
    return scaled


def parse_yolo_outputs(
    outputs: list[np.ndarray], score_thr: float, nms_iou: float
) -> tuple[np.ndarray, np.ndarray]:
    pred = np.asarray(outputs[0], dtype=np.float32)
    pred = squeeze_batch(pred)
    if pred.ndim != 2:
        raise RuntimeError(f"不支持的YOLO输出形状: {outputs[0].shape}")

    if pred.shape[0] < pred.shape[1]:
        pred = pred.T

    if pred.shape[1] < 5:
        raise RuntimeError(f"YOLO输出通道不足: {pred.shape}")

    boxes = xywh_to_xyxy(pred[:, :4])
    class_scores = pred[:, 4:]
    scores = class_scores.max(axis=1).astype(np.float32)

    keep = scores >= score_thr
    boxes = boxes[keep]
    scores = scores[keep]
    if boxes.size == 0:
        return boxes.reshape(0, 4), scores

    keep_nms = nms_xyxy(boxes, scores, nms_iou)
    return boxes[keep_nms], scores[keep_nms]


def parse_fasterrcnn_outputs(
    outputs: list[np.ndarray], score_thr: float
) -> tuple[np.ndarray, np.ndarray]:
    if len(outputs) < 3:
        raise RuntimeError(f"不支持的检测输出数量: {len(outputs)}")

    boxes = np.asarray(squeeze_batch(np.asarray(outputs[0])), dtype=np.float32)
    scores = np.asarray(squeeze_batch(np.asarray(outputs[2])), dtype=np.float32)
    keep = scores >= score_thr
    return boxes[keep], scores[keep]


def parse_model_outputs(
    outputs: list[np.ndarray], score_thr: float, nms_iou: float
) -> tuple[np.ndarray, np.ndarray]:
    if len(outputs) == 1:
        return parse_yolo_outputs(outputs, score_thr=score_thr, nms_iou=nms_iou)
    return parse_fasterrcnn_outputs(outputs, score_thr=score_thr)


def draw_annotated_with_panel(
    src_bgr: np.ndarray,
    boxes_xyxy: np.ndarray,
    scores: np.ndarray,
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

    for i, box in enumerate(boxes_xyxy):
        s = float(scores[i])
        x1 = int(max(0, min(w - 1, box[0])))
        y1 = int(max(0, min(h - 1, box[1])))
        x2 = int(max(0, min(w - 1, box[2])))
        y2 = int(max(0, min(h - 1, box[3])))

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

    avg_score = float(np.mean(scores)) if scores.size > 0 else 0.0

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
        f"Total Colonies: {int(scores.size)}",
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
        f"count={int(scores.size)}, A={high_count}, B={low_count}, "
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
        self._input_size: Optional[int] = None

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

        so.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        so.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL

        self._sess = ort.InferenceSession(
            self.model_path, sess_options=so, providers=["CPUExecutionProvider"]
        )
        self._input_name = self._sess.get_inputs()[0].name
        self._input_size = resolve_input_size(self._sess)
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
        self._input_size = None

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
        assert self._input_size is not None
        while self._running:
            try:
                req = self._requests.get(timeout=0.1)
            except queue.Empty:
                continue
            t0 = time.perf_counter()
            try:
                inp = preprocess_image(req.source_bgr, size=self._input_size)
                outs = cast(
                    list[np.ndarray], self._sess.run(None, {self._input_name: inp})
                )
                boxes, scores = parse_model_outputs(
                    outs, score_thr=req.threshold, nms_iou=req.nms_iou
                )
                h, w = req.source_bgr.shape[:2]
                boxes = scale_boxes_to_source(
                    boxes, src_w=w, src_h=h, input_size=self._input_size
                )
                annotated, high_count, low_count, avg_score, details, summary_text = (
                    draw_annotated_with_panel(
                        src_bgr=req.source_bgr,
                        boxes_xyxy=boxes,
                        scores=scores,
                        high_conf_thr=req.high_conf_thr,
                        model_name=req.model_name,
                        score_thr=req.threshold,
                        nms_iou=req.nms_iou,
                    )
                )
                latency_ms = (time.perf_counter() - t0) * 1000.0
                kept_indices = np.arange(scores.shape[0], dtype=np.int64)
                result = InferenceResult(
                    request_id=req.request_id,
                    source_path=req.source_path,
                    source_type=req.source_type,
                    annotated_bgr=annotated,
                    boxes=boxes,
                    scores=scores,
                    kept_indices=kept_indices,
                    high_count=high_count,
                    low_count=low_count,
                    top_score=float(scores.max() if scores.size > 0 else 0.0),
                    avg_score=avg_score,
                    count=int(scores.shape[0]),
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
