"""Subset ONNX evaluation for colony detection/counting models.

Evaluates an ONNX model on a random subset of a COCO-format dataset.
Supports both detector (multi-output) and count-regression (single-output) models.

Outputs:
  - Per-image CSV with gt_count, pred_count, tp/fp/fn, latency
  - Summary JSON with MAE, RMSE, detection_rate_proxy, latency p50/p90

This script replaces the historical MindSpore eval pipeline with a
PyTorch/ORT-compatible implementation. The "detection_rate_proxy" metric
was defined in the handoff doc as: count_exact_match_rate (pred==gt).

Usage:
  python scripts/eval_count_onnx_subset.py ^
    --dataset-root merged_dataset ^
    --split test ^
    --model "onnx model/checkpoint_epoch_31.onnx" ^
    --subset 10 ^
    --out-csv reports/subset10_eval.csv ^
    --out-json reports/subset10_eval.json

  # Full test set:
  python scripts/eval_count_onnx_subset.py ^
    --dataset-root merged_dataset ^
    --split test ^
    --model "onnx model/checkpoint_epoch_31.static_qdq.onnx" ^
    --subset 0 ^
    --out-csv reports/full_eval.csv ^
    --out-json reports/full_eval.json
"""

import argparse
import csv
import json
import math
import random
import statistics
import time
from pathlib import Path
from typing import Any, cast

import cv2
import numpy as np
import onnxruntime as ort


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Subset ONNX evaluation for colony counting/detection"
    )
    parser.add_argument("--dataset-root", required=True, help="Dataset root path")
    parser.add_argument("--split", default="test", help="Split name: test/train/valid")
    parser.add_argument("--ann-file", default="", help="COCO annotation json path")
    parser.add_argument("--images-dir", default="", help="Image directory path")
    parser.add_argument("--model", required=True, help="ONNX model path")
    parser.add_argument(
        "--subset",
        type=int,
        default=10,
        help="Number of random images to evaluate (0 = all)",
    )
    parser.add_argument("--seed", type=int, default=42, help="Random seed for subset")
    parser.add_argument("--score-thr", type=float, default=0.45, help="Score threshold")
    parser.add_argument("--nms-iou", type=float, default=0.30, help="NMS IoU threshold")
    parser.add_argument(
        "--match-iou",
        type=float,
        default=0.50,
        help="IoU threshold for TP matching against GT",
    )
    parser.add_argument("--input-size", type=int, default=800, help="Model input size")
    parser.add_argument(
        "--intra-threads", type=int, default=2, help="ONNX Runtime intra-op threads"
    )
    parser.add_argument(
        "--inter-threads", type=int, default=1, help="ONNX Runtime inter-op threads"
    )
    parser.add_argument("--out-csv", required=True, help="Per-image metrics CSV output")
    parser.add_argument("--out-json", required=True, help="Summary JSON output")
    return parser.parse_args()


def preprocess(image_bgr: np.ndarray, size: int) -> np.ndarray:
    rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
    img = cv2.resize(rgb, (size, size)).astype("float32") / 255.0
    mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
    std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
    img = (img - mean) / std
    img = np.transpose(img, (2, 0, 1))
    return img[np.newaxis, ...].astype("float32")


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


def nms_indices(
    boxes: np.ndarray, scores: np.ndarray, score_thr: float, iou_thr: float
) -> np.ndarray:
    idx = np.where(scores >= score_thr)[0]
    if idx.size == 0:
        return np.array([], dtype=np.int64)
    idx = idx[np.argsort(scores[idx])[::-1]]
    keep: list[int] = []
    while idx.size > 0:
        cur = int(idx[0])
        keep.append(cur)
        rest = idx[1:]
        filtered: list[int] = []
        for j in rest:
            if iou_xyxy(boxes[cur], boxes[int(j)]) <= iou_thr:
                filtered.append(int(j))
        idx = np.array(filtered, dtype=np.int64)
    return np.array(keep, dtype=np.int64)


def parse_detector_outputs(
    outputs: list[np.ndarray],
) -> tuple[np.ndarray, np.ndarray]:
    """Parse ONNX outputs for detector model (>=2 outputs)."""
    if len(outputs) >= 3:
        boxes = np.asarray(outputs[0])[0]
        scores = np.asarray(outputs[2])[0]
        return boxes.astype(np.float32), scores.astype(np.float32)
    if len(outputs) == 2:
        boxes = np.asarray(outputs[0])[0]
        scores = np.asarray(outputs[1])[0]
        return boxes.astype(np.float32), scores.astype(np.float32)
    raise RuntimeError(f"Unexpected ONNX outputs length: {len(outputs)}")


def scale_boxes_from_input(
    boxes: np.ndarray, src_w: int, src_h: int, input_size: int
) -> np.ndarray:
    scaled = boxes.copy().astype(np.float32)
    scaled[:, [0, 2]] = scaled[:, [0, 2]] * (src_w / float(input_size))
    scaled[:, [1, 3]] = scaled[:, [1, 3]] * (src_h / float(input_size))
    return scaled


def coco_bbox_xywh_to_xyxy(box_xywh: list[float]) -> np.ndarray:
    x, y, w, h = box_xywh
    return np.array([x, y, x + w, y + h], dtype=np.float32)


def match_predictions(
    pred_boxes: np.ndarray,
    pred_scores: np.ndarray,
    gt_boxes: np.ndarray,
    match_iou_thr: float,
) -> tuple[int, int, int]:
    if pred_boxes.size == 0:
        return 0, 0, int(gt_boxes.shape[0])
    order = np.argsort(pred_scores)[::-1]
    used_gt: set[int] = set()
    tp = 0
    fp = 0
    for idx in order:
        p = pred_boxes[int(idx)]
        best_gt = -1
        best_iou = 0.0
        for gi, gt in enumerate(gt_boxes):
            if gi in used_gt:
                continue
            ov = iou_xyxy(p, gt)
            if ov > best_iou:
                best_iou = ov
                best_gt = gi
        if best_gt >= 0 and best_iou >= match_iou_thr:
            tp += 1
            used_gt.add(best_gt)
        else:
            fp += 1
    fn = int(gt_boxes.shape[0]) - tp
    return tp, fp, fn


def percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    k = max(0, min(len(values) - 1, int(math.ceil(pct * len(values))) - 1))
    return sorted(values)[k]


def main() -> None:
    args = parse_args()

    root = Path(args.dataset_root)
    split_dir = Path(args.images_dir) if args.images_dir else root / args.split
    ann_file = (
        Path(args.ann_file) if args.ann_file else split_dir / "_annotations.coco.json"
    )
    model_path = Path(args.model)
    out_csv = Path(args.out_csv)
    out_json = Path(args.out_json)

    if not split_dir.exists():
        raise FileNotFoundError(f"Split dir not found: {split_dir}")
    if not ann_file.exists():
        raise FileNotFoundError(f"Annotation file not found: {ann_file}")
    if not model_path.exists():
        raise FileNotFoundError(f"Model file not found: {model_path}")

    coco = json.loads(ann_file.read_text(encoding="utf-8"))
    images = coco.get("images", [])
    annotations = coco.get("annotations", [])

    # Build per-image ground truth
    ann_by_image: dict[int, list[dict[str, Any]]] = {}
    for ann in annotations:
        ann_by_image.setdefault(int(ann.get("image_id", -1)), []).append(ann)

    # Subset sampling
    if args.subset > 0 and args.subset < len(images):
        rng = random.Random(args.seed)
        images = rng.sample(images, args.subset)
        print(f"Subset: {len(images)} images (seed={args.seed})")
    else:
        print(f"Evaluating all {len(images)} images")

    # Init ONNX session
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

    # Detect model type from output count
    dummy = np.zeros((1, 3, args.input_size, args.input_size), dtype=np.float32)
    test_outs = session.run(None, {input_name: dummy})
    is_detector = len(test_outs) >= 2
    print(
        f"Model outputs: {len(test_outs)} -> {'detector' if is_detector else 'regression'}"
    )

    rows: list[dict[str, Any]] = []
    latency_ms_values: list[float] = []
    total_tp = 0
    total_fp = 0
    total_fn = 0
    abs_err_sum = 0.0
    sq_err_sum = 0.0
    exact_count_matches = 0

    for i, img_info in enumerate(images, start=1):
        file_name = str(img_info.get("file_name", ""))
        image_id = int(img_info.get("id", -1))

        img_path = split_dir / file_name
        if not img_path.exists():
            img_path = split_dir / Path(file_name).name

        image = cv2.imread(str(img_path))
        if image is None:
            continue

        # Ground truth
        gt_ann = ann_by_image.get(image_id, [])
        gt_boxes = np.array(
            [coco_bbox_xywh_to_xyxy(a.get("bbox", [0, 0, 0, 0])) for a in gt_ann],
            dtype=np.float32,
        )
        if gt_boxes.size == 0:
            gt_boxes = np.zeros((0, 4), dtype=np.float32)
        gt_count = int(gt_boxes.shape[0])

        # Inference
        inp = preprocess(image, args.input_size)
        t0 = time.perf_counter()
        try:
            outs = cast(list[np.ndarray], session.run(None, {input_name: inp}))
        except Exception as e:
            rows.append(
                {
                    "index": i,
                    "file_name": file_name,
                    "gt_count": gt_count,
                    "pred_count": 0,
                    "count_error": -gt_count,
                    "abs_count_error": gt_count,
                    "tp": 0,
                    "fp": 0,
                    "fn": gt_count,
                    "latency_ms": 0.0,
                    "error": str(e),
                }
            )
            abs_err_sum += gt_count
            sq_err_sum += gt_count * gt_count
            total_fn += gt_count
            continue
        latency_ms = (time.perf_counter() - t0) * 1000.0
        latency_ms_values.append(latency_ms)

        if is_detector:
            boxes_input, scores = parse_detector_outputs(outs)
            keep = nms_indices(boxes_input, scores, args.score_thr, args.nms_iou)
            pred_count = int(keep.size)
            pred_boxes = (
                boxes_input[keep]
                if keep.size > 0
                else np.zeros((0, 4), dtype=np.float32)
            )
            pred_scores = (
                scores[keep] if keep.size > 0 else np.zeros((0,), dtype=np.float32)
            )
            # Scale boxes to source image coordinates
            h, w = image.shape[:2]
            pred_boxes = scale_boxes_from_input(pred_boxes, w, h, args.input_size)
            tp, fp, fn = match_predictions(
                pred_boxes, pred_scores, gt_boxes, args.match_iou
            )
        else:
            # Count regression: single scalar output
            pred_count = int(round(float(outs[0].flatten()[0])))
            tp, fp, fn = 0, 0, 0  # N/A for regression

        err = pred_count - gt_count
        abs_err_sum += abs(err)
        sq_err_sum += err * err
        if pred_count == gt_count:
            exact_count_matches += 1
        total_tp += tp
        total_fp += fp
        total_fn += fn

        rows.append(
            {
                "index": i,
                "file_name": file_name,
                "gt_count": gt_count,
                "pred_count": pred_count,
                "count_error": err,
                "abs_count_error": abs(err),
                "tp": tp,
                "fp": fp,
                "fn": fn,
                "latency_ms": round(latency_ms, 2),
                "error": "",
            }
        )

    n = len(rows)
    if n == 0:
        print("No images evaluated.")
        return

    mae = abs_err_sum / n
    rmse = math.sqrt(sq_err_sum / n)
    detection_rate_proxy = exact_count_matches / n  # pred==gt exact match rate
    precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0.0
    recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0.0
    f1 = (
        2 * precision * recall / (precision + recall)
        if (precision + recall) > 0
        else 0.0
    )

    summary = {
        "model": str(model_path),
        "dataset_root": str(root),
        "split": args.split,
        "num_images": n,
        "subset_size": args.subset,
        "seed": args.seed,
        "score_thr": args.score_thr,
        "nms_iou": args.nms_iou,
        "match_iou": args.match_iou,
        "input_size": args.input_size,
        "model_type": "detector" if is_detector else "regression",
        # Count metrics (compatible with handoff doc terminology)
        "count_mae": round(mae, 4),
        "count_rmse": round(rmse, 4),
        "detection_rate_proxy": round(detection_rate_proxy, 4),
        # Detection metrics (only meaningful for detector models)
        "total_tp": total_tp,
        "total_fp": total_fp,
        "total_fn": total_fn,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        # Latency
        "latency_ms_p50": round(percentile(latency_ms_values, 0.5), 2),
        "latency_ms_p90": round(percentile(latency_ms_values, 0.9), 2),
        "latency_ms_mean": round(statistics.fmean(latency_ms_values), 2),
        "latency_ms_min": round(min(latency_ms_values), 2),
        "latency_ms_max": round(max(latency_ms_values), 2),
        # Files
        "out_csv": str(out_csv),
    }

    # Write CSV
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
                "error",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    # Write JSON
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    print("\n=== Subset Evaluation Summary ===")
    for k, v in summary.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
