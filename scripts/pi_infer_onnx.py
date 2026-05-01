import argparse
import csv
import time
from pathlib import Path
from typing import cast

import cv2
import numpy as np
import onnxruntime as ort


def preprocess_image(image_bgr: np.ndarray, size: int) -> np.ndarray:
    rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
    img = cv2.resize(rgb, (size, size)).astype("float32") / 255.0
    mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
    std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
    img = (img - mean) / std
    img = np.transpose(img, (2, 0, 1))
    return img[np.newaxis, ...].astype("float32")


def resolve_input_size(
    session: ort.InferenceSession, input_size_override: int | None
) -> int:
    shape = session.get_inputs()[0].shape
    if len(shape) >= 4:
        h = shape[-2]
        w = shape[-1]
        if isinstance(h, int) and isinstance(w, int) and h > 0 and h == w:
            return int(h)
    if input_size_override is not None and input_size_override > 0:
        return int(input_size_override)
    raise RuntimeError(
        f"Unable to infer model input size from shape {shape}. "
        "Pass --input-size explicitly."
    )


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
) -> tuple[np.ndarray, np.ndarray, np.ndarray, int]:
    pred = np.asarray(outputs[0], dtype=np.float32)
    pred = squeeze_batch(pred)
    if pred.ndim != 2:
        raise RuntimeError(f"Unsupported YOLO output shape: {outputs[0].shape}")

    if pred.shape[0] < pred.shape[1]:
        pred = pred.T

    if pred.shape[1] < 5:
        raise RuntimeError(f"YOLO output has too few channels: {pred.shape}")

    boxes = xywh_to_xyxy(pred[:, :4])
    class_scores = pred[:, 4:]
    labels = class_scores.argmax(axis=1).astype(np.int64)
    scores = class_scores.max(axis=1).astype(np.float32)
    raw_count = int(boxes.shape[0])

    keep = scores >= score_thr
    boxes = boxes[keep]
    scores = scores[keep]
    labels = labels[keep]
    if boxes.size == 0:
        return boxes.reshape(0, 4), scores, labels, raw_count

    keep_nms = nms_xyxy(boxes, scores, nms_iou)
    return boxes[keep_nms], scores[keep_nms], labels[keep_nms], raw_count


def parse_fasterrcnn_outputs(
    outputs: list[np.ndarray], score_thr: float
) -> tuple[np.ndarray, np.ndarray, np.ndarray, int]:
    if len(outputs) < 3:
        raise RuntimeError(
            f"Unsupported detection outputs: expected >=3 tensors, got {len(outputs)}"
        )

    boxes = np.asarray(squeeze_batch(np.asarray(outputs[0])), dtype=np.float32)
    labels = np.asarray(squeeze_batch(np.asarray(outputs[1])), dtype=np.int64)
    scores = np.asarray(squeeze_batch(np.asarray(outputs[2])), dtype=np.float32)
    raw_count = int(boxes.shape[0])

    keep = scores >= score_thr
    return boxes[keep], scores[keep], labels[keep], raw_count


def parse_model_outputs(
    outputs: list[np.ndarray], score_thr: float, nms_iou: float
) -> tuple[str, np.ndarray, np.ndarray, np.ndarray, int]:
    if len(outputs) == 1:
        boxes, scores, labels, raw_count = parse_yolo_outputs(
            outputs, score_thr=score_thr, nms_iou=nms_iou
        )
        return "yolo", boxes, scores, labels, raw_count

    boxes, scores, labels, raw_count = parse_fasterrcnn_outputs(
        outputs, score_thr=score_thr
    )
    return "fasterrcnn", boxes, scores, labels, raw_count


def run_folder(
    model_path: Path,
    image_dir: Path,
    threshold: float,
    nms_iou: float,
    out_csv: Path,
    intra_threads: int,
    inter_threads: int,
    input_size_override: int | None,
) -> None:
    so = ort.SessionOptions()
    if intra_threads > 0:
        so.intra_op_num_threads = intra_threads
    if inter_threads > 0:
        so.inter_op_num_threads = inter_threads
    sess = ort.InferenceSession(
        str(model_path), sess_options=so, providers=["CPUExecutionProvider"]
    )
    inp_name = sess.get_inputs()[0].name
    input_size = resolve_input_size(sess, input_size_override)

    rows = []
    total_ms = 0.0
    count = 0
    model_kind = "unknown"

    image_paths = []
    for pattern in ("*.jpg", "*.jpeg", "*.png", "*.bmp"):
        image_paths.extend(sorted(image_dir.glob(pattern)))

    for p in image_paths:
        image = cv2.imread(str(p))
        if image is None:
            continue
        inp = preprocess_image(image, size=input_size)
        t0 = time.perf_counter()
        outs = cast(list[np.ndarray], sess.run(None, {inp_name: inp}))
        dt_ms = (time.perf_counter() - t0) * 1000.0
        model_kind, boxes, scores, labels, raw_count = parse_model_outputs(
            outs, score_thr=threshold, nms_iou=nms_iou
        )
        h, w = image.shape[:2]
        boxes = scale_boxes_to_source(boxes, src_w=w, src_h=h, input_size=input_size)
        det_count = int(scores.shape[0])
        top_score = float(scores.max() if scores.size > 0 else 0.0)
        top_label = int(labels[scores.argmax()]) if scores.size > 0 else -1
        rows.append((p.name, det_count, top_score, top_label, dt_ms, raw_count))
        total_ms += dt_ms
        count += 1

    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "image",
                "count_ge_thr",
                "top_score",
                "top_label",
                "latency_ms",
                "raw_boxes",
            ]
        )
        writer.writerows(rows)

    avg = total_ms / count if count else 0.0
    print(f"model={model_path}")
    print(f"model_kind={model_kind}")
    print(f"input_size={input_size}")
    print(f"images={count}")
    print(f"avg_latency_ms={avg:.2f}")
    print(f"intra_threads={intra_threads}")
    print(f"inter_threads={inter_threads}")
    print(f"report={out_csv}")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run ONNX inference on image folder")
    p.add_argument("--model", required=True, help="Path to ONNX model")
    p.add_argument(
        "--image-dir", required=True, help="Directory containing .jpg images"
    )
    p.add_argument("--threshold", type=float, default=0.45, help="Score threshold")
    p.add_argument("--nms-iou", type=float, default=0.45, help="NMS IoU threshold")
    p.add_argument("--out-csv", required=True, help="Output CSV path")
    p.add_argument(
        "--intra-threads", type=int, default=0, help="ORT intra-op threads, 0=default"
    )
    p.add_argument(
        "--inter-threads", type=int, default=0, help="ORT inter-op threads, 0=default"
    )
    p.add_argument(
        "--input-size",
        type=int,
        default=0,
        help="Override model input size. 0 means auto-detect from ONNX.",
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()
    run_folder(
        Path(args.model),
        Path(args.image_dir),
        args.threshold,
        args.nms_iou,
        Path(args.out_csv),
        args.intra_threads,
        args.inter_threads,
        None if args.input_size <= 0 else args.input_size,
    )


if __name__ == "__main__":
    main()
