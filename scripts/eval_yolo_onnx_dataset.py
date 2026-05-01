"""Evaluate YOLO-style ONNX detector on a YOLO-format dataset split.

Outputs:
  - Per-image CSV with gt/pred count, tp/fp/fn, latency
  - Summary JSON with global metrics and per-class statistics

This script is designed for the current YOLO11 ONNX export:
  input: [1, 3, 640, 640]
  output: [1, C, N]
"""

import argparse
import csv
import json
import math
import statistics
import time
from pathlib import Path
from typing import Any

import cv2
import numpy as np
import onnxruntime as ort
import yaml


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate YOLO ONNX on YOLO-format dataset split"
    )
    parser.add_argument("--dataset-root", required=True, help="Dataset root path")
    parser.add_argument(
        "--split",
        default="test",
        choices=["train", "val", "valid", "test"],
        help="Dataset split name",
    )
    parser.add_argument("--model", required=True, help="ONNX model path")
    parser.add_argument("--data-yaml", default="", help="Optional data.yaml path")
    parser.add_argument("--score-thr", type=float, default=0.45)
    parser.add_argument("--nms-iou", type=float, default=0.45)
    parser.add_argument("--match-iou", type=float, default=0.50)
    parser.add_argument("--input-size", type=int, default=0)
    parser.add_argument("--intra-threads", type=int, default=2)
    parser.add_argument("--inter-threads", type=int, default=1)
    parser.add_argument("--max-images", type=int, default=0)
    parser.add_argument("--out-csv", required=True)
    parser.add_argument("--out-json", required=True)
    return parser.parse_args()


def preprocess(image_bgr: np.ndarray, size: int) -> np.ndarray:
    rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
    img = cv2.resize(rgb, (size, size)).astype("float32") / 255.0
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
    raise RuntimeError(f"Unable to infer model input size from {shape}")


def squeeze_batch(arr: np.ndarray) -> np.ndarray:
    if arr.ndim >= 1 and arr.shape[0] == 1:
        return arr[0]
    return arr


def xywh_to_xyxy(boxes_xywh: np.ndarray) -> np.ndarray:
    boxes = boxes_xywh.astype(np.float32, copy=True)
    cx = boxes[:, 0].copy()
    cy = boxes[:, 1].copy()
    w = boxes[:, 2].copy()
    h = boxes[:, 3].copy()
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


def parse_yolo_outputs(
    outputs: list[np.ndarray], score_thr: float, nms_iou: float
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
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

    keep = scores >= score_thr
    boxes = boxes[keep]
    scores = scores[keep]
    labels = labels[keep]
    if boxes.size == 0:
        return (
            boxes.reshape(0, 4),
            scores.reshape(0),
            labels.reshape(0),
            np.zeros((0,), dtype=np.int64),
        )

    keep_nms = nms_xyxy(boxes, scores, nms_iou)
    return boxes[keep_nms], scores[keep_nms], labels[keep_nms], keep_nms


def scale_boxes_from_input(
    boxes: np.ndarray, src_w: int, src_h: int, input_size: int
) -> np.ndarray:
    scaled = boxes.astype(np.float32, copy=True)
    scaled[:, [0, 2]] *= src_w / float(input_size)
    scaled[:, [1, 3]] *= src_h / float(input_size)
    return scaled


def yolo_txt_to_xyxy(label_path: Path, img_w: int, img_h: int) -> list[dict[str, Any]]:
    if not label_path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in label_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) < 5:
            continue
        cls = int(float(parts[0]))
        cx = float(parts[1]) * img_w
        cy = float(parts[2]) * img_h
        w = float(parts[3]) * img_w
        h = float(parts[4]) * img_h
        rows.append(
            {
                "class_id": cls,
                "box": np.array(
                    [cx - w / 2.0, cy - h / 2.0, cx + w / 2.0, cy + h / 2.0],
                    dtype=np.float32,
                ),
            }
        )
    return rows


def iou_xyxy(a: np.ndarray, b: np.ndarray) -> float:
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


def match_predictions_by_class(
    pred_boxes: np.ndarray,
    pred_scores: np.ndarray,
    pred_labels: np.ndarray,
    gt_items: list[dict[str, Any]],
    match_iou_thr: float,
) -> tuple[int, int, int, dict[int, dict[str, int]], list[float]]:
    gt_used: set[int] = set()
    per_class: dict[int, dict[str, int]] = {}
    matched_ious: list[float] = []

    def ensure(cls: int) -> dict[str, int]:
        if cls not in per_class:
            per_class[cls] = {"tp": 0, "fp": 0, "fn": 0, "gt": 0, "pred": 0}
        return per_class[cls]

    for gt in gt_items:
        ensure(int(gt["class_id"]))["gt"] += 1
    for cls in pred_labels.tolist():
        ensure(int(cls))["pred"] += 1

    order = np.argsort(pred_scores)[::-1]
    tp = 0
    fp = 0
    for idx in order:
        idx = int(idx)
        label = int(pred_labels[idx])
        box = pred_boxes[idx]
        best_gt = -1
        best_iou = 0.0
        for gi, gt in enumerate(gt_items):
            if gi in gt_used:
                continue
            if int(gt["class_id"]) != label:
                continue
            ov = iou_xyxy(box, gt["box"])
            if ov > best_iou:
                best_iou = ov
                best_gt = gi
        cls_stat = ensure(label)
        if best_gt >= 0 and best_iou >= match_iou_thr:
            tp += 1
            cls_stat["tp"] += 1
            gt_used.add(best_gt)
            matched_ious.append(best_iou)
        else:
            fp += 1
            cls_stat["fp"] += 1

    fn = 0
    for gi, gt in enumerate(gt_items):
        if gi not in gt_used:
            fn += 1
            ensure(int(gt["class_id"]))["fn"] += 1

    return tp, fp, fn, per_class, matched_ious


def percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    k = max(0, min(len(values) - 1, int(math.ceil(pct * len(values))) - 1))
    return sorted(values)[k]


def main() -> None:
    args = parse_args()
    root = Path(args.dataset_root)
    model_path = Path(args.model)
    data_yaml = Path(args.data_yaml) if args.data_yaml else root / "data.yaml"
    out_csv = Path(args.out_csv)
    out_json = Path(args.out_json)

    split_name = "val" if args.split == "valid" else args.split
    yolo_images_dir = root / "images" / split_name
    yolo_labels_dir = root / "labels" / split_name
    roboflow_split_dir = root / ("valid" if split_name == "val" else split_name)

    dataset_mode = ""
    images_dir: Path
    labels_dir: Path | None
    if yolo_images_dir.exists() and yolo_labels_dir.exists():
        dataset_mode = "yolo"
        images_dir = yolo_images_dir
        labels_dir = yolo_labels_dir
    elif roboflow_split_dir.exists():
        dataset_mode = "roboflow_coco"
        images_dir = roboflow_split_dir
        labels_dir = None
    else:
        raise FileNotFoundError(
            f"Dataset split not found. Tried YOLO paths {yolo_images_dir} / {yolo_labels_dir} "
            f"and COCO path {roboflow_split_dir}"
        )

    if not model_path.exists():
        raise FileNotFoundError(f"Model file not found: {model_path}")
    if not data_yaml.exists():
        raise FileNotFoundError(f"data.yaml not found: {data_yaml}")

    meta = yaml.safe_load(data_yaml.read_text(encoding="utf-8"))
    class_names = list(meta.get("names", []))

    image_paths = sorted(
        [p for p in images_dir.iterdir() if p.is_file() and p.suffix.lower() in {".jpg", ".jpeg", ".png", ".bmp"}]
    )
    if args.max_images > 0:
        image_paths = image_paths[: args.max_images]

    so = ort.SessionOptions()
    if args.intra_threads > 0:
        so.intra_op_num_threads = args.intra_threads
    if args.inter_threads > 0:
        so.inter_op_num_threads = args.inter_threads
    so.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
    so.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
    session = ort.InferenceSession(
        str(model_path), sess_options=so, providers=["CPUExecutionProvider"]
    )
    input_name = session.get_inputs()[0].name
    input_size = resolve_input_size(
        session, None if args.input_size <= 0 else args.input_size
    )

    rows: list[dict[str, Any]] = []
    latency_ms_values: list[float] = []
    all_match_ious: list[float] = []
    total_tp = 0
    total_fp = 0
    total_fn = 0
    exact_count_matches = 0
    abs_err_sum = 0.0
    sq_err_sum = 0.0
    per_class_total: dict[int, dict[str, int]] = {}

    def ensure_total(cls: int) -> dict[str, int]:
        if cls not in per_class_total:
            per_class_total[cls] = {"tp": 0, "fp": 0, "fn": 0, "gt": 0, "pred": 0}
        return per_class_total[cls]

    for i, img_path in enumerate(image_paths, start=1):
        image = cv2.imread(str(img_path))
        if image is None:
            continue
        h, w = image.shape[:2]
        if dataset_mode == "yolo":
            assert labels_dir is not None
            label_path = labels_dir / f"{img_path.stem}.txt"
            gt_items = yolo_txt_to_xyxy(label_path, img_w=w, img_h=h)
        else:
            ann_path = images_dir / "_annotations.coco.json"
            if not ann_path.exists():
                raise FileNotFoundError(f"COCO annotation file not found: {ann_path}")
            if 'coco_cache' not in locals():
                coco_cache = json.loads(ann_path.read_text(encoding='utf-8'))
                image_to_gt = {}
                images_by_name = {}
                for img in coco_cache.get('images', []):
                    images_by_name[str(img.get('file_name', ''))] = int(img.get('id', -1))
                for ann in coco_cache.get('annotations', []):
                    image_to_gt.setdefault(int(ann.get('image_id', -1)), []).append(ann)
            image_id = images_by_name.get(img_path.name, -1)
            coco_items = image_to_gt.get(image_id, [])
            gt_items = []
            for ann in coco_items:
                x, y, bw, bh = ann.get('bbox', [0, 0, 0, 0])
                gt_items.append(
                    {
                        'class_id': int(ann.get('category_id', 1)) - 1,
                        'box': np.array([x, y, x + bw, y + bh], dtype=np.float32),
                    }
                )

        inp = preprocess(image, input_size)
        t0 = time.perf_counter()
        outputs = session.run(None, {input_name: inp})
        infer_ms = (time.perf_counter() - t0) * 1000.0
        latency_ms_values.append(infer_ms)

        pred_boxes, pred_scores, pred_labels, _ = parse_yolo_outputs(
            outputs, score_thr=args.score_thr, nms_iou=args.nms_iou
        )
        pred_boxes = scale_boxes_from_input(pred_boxes, src_w=w, src_h=h, input_size=input_size)

        tp, fp, fn, per_class, matched_ious = match_predictions_by_class(
            pred_boxes=pred_boxes,
            pred_scores=pred_scores,
            pred_labels=pred_labels,
            gt_items=gt_items,
            match_iou_thr=args.match_iou,
        )
        all_match_ious.extend(matched_ious)
        total_tp += tp
        total_fp += fp
        total_fn += fn
        for cls, stat in per_class.items():
            total = ensure_total(cls)
            for k, v in stat.items():
                total[k] += v

        gt_count = len(gt_items)
        pred_count = int(pred_boxes.shape[0])
        err = pred_count - gt_count
        abs_err_sum += abs(err)
        sq_err_sum += err * err
        if gt_count == pred_count:
            exact_count_matches += 1

        rows.append(
            {
                "index": i,
                "file_name": img_path.name,
                "gt_count": gt_count,
                "pred_count": pred_count,
                "count_error": err,
                "abs_count_error": abs(err),
                "tp": tp,
                "fp": fp,
                "fn": fn,
                "latency_ms": round(infer_ms, 2),
            }
        )

    n = len(rows)
    if n == 0:
        raise RuntimeError("No images evaluated.")

    global_precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0.0
    global_recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0.0
    global_f1 = (
        2 * global_precision * global_recall / (global_precision + global_recall)
        if (global_precision + global_recall) > 0
        else 0.0
    )

    per_class_summary: dict[str, dict[str, Any]] = {}
    for cls, stat in sorted(per_class_total.items()):
        precision = stat["tp"] / (stat["tp"] + stat["fp"]) if (stat["tp"] + stat["fp"]) > 0 else 0.0
        recall = stat["tp"] / (stat["tp"] + stat["fn"]) if (stat["tp"] + stat["fn"]) > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
        name = class_names[cls] if 0 <= cls < len(class_names) else f"class_{cls}"
        per_class_summary[name] = {
            "class_id": cls,
            "gt": stat["gt"],
            "pred": stat["pred"],
            "tp": stat["tp"],
            "fp": stat["fp"],
            "fn": stat["fn"],
            "precision": round(precision, 6),
            "recall": round(recall, 6),
            "f1": round(f1, 6),
        }

    summary = {
        "dataset_root": str(root),
        "dataset_mode": dataset_mode,
        "split": split_name,
        "model": str(model_path),
        "data_yaml": str(data_yaml),
        "class_names": class_names,
        "num_images_evaluated": n,
        "input_size": input_size,
        "score_thr": args.score_thr,
        "nms_iou": args.nms_iou,
        "match_iou": args.match_iou,
        "total_tp": total_tp,
        "total_fp": total_fp,
        "total_fn": total_fn,
        "global_precision": round(global_precision, 6),
        "global_recall": round(global_recall, 6),
        "global_f1": round(global_f1, 6),
        "count_mae": round(abs_err_sum / n, 6),
        "count_rmse": round(math.sqrt(sq_err_sum / n), 6),
        "count_exact_accuracy": round(exact_count_matches / n, 6),
        "latency_ms_mean": round(float(statistics.fmean(latency_ms_values)), 4),
        "latency_ms_p50": round(percentile(latency_ms_values, 0.5), 4),
        "latency_ms_p90": round(percentile(latency_ms_values, 0.9), 4),
        "mean_match_iou": round(float(statistics.fmean(all_match_ious)) if all_match_ious else 0.0, 6),
        "per_class": per_class_summary,
        "out_csv": str(out_csv),
    }

    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "index",
                "file_name",
                "gt_count",
                "pred_count",
                "count_error",
                "abs_count_error",
                "tp",
                "fp",
                "fn",
                "latency_ms",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    print("=== Evaluation Summary ===")
    for k, v in summary.items():
        if k == "per_class":
            print("per_class:")
            for cls_name, cls_stat in v.items():
                print(f"  {cls_name}: {cls_stat}")
        else:
            print(f"{k}: {v}")


if __name__ == "__main__":
    main()
