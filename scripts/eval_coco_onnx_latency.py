import argparse
import csv
import json
import math
import statistics
import time
from pathlib import Path
from typing import Any, cast

import cv2
import numpy as np
import onnxruntime as ort


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate ONNX detector on COCO-style split with per-image latency"
    )
    parser.add_argument("--dataset-root", required=True, help="Dataset root path")
    parser.add_argument("--split", default="test", help="Split name: test/train/valid")
    parser.add_argument("--ann-file", default="", help="COCO annotation json path")
    parser.add_argument("--images-dir", default="", help="Image directory path")
    parser.add_argument("--model", required=True, help="ONNX model path")
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
        "--intra-threads",
        type=int,
        default=2,
        help="ONNX Runtime intra-op threads",
    )
    parser.add_argument(
        "--inter-threads",
        type=int,
        default=1,
        help="ONNX Runtime inter-op threads",
    )
    parser.add_argument(
        "--max-images", type=int, default=0, help="0 means evaluate all"
    )
    parser.add_argument(
        "--source-resize",
        type=int,
        default=0,
        help="Optional square resize of source image before preprocessing (0 means disabled)",
    )
    parser.add_argument(
        "--jpeg-quality",
        type=int,
        default=0,
        help="Optional JPEG re-encode quality [1..100] to simulate compression (0 means disabled)",
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


def parse_outputs(outputs: list[np.ndarray]) -> tuple[np.ndarray, np.ndarray]:
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


def scale_boxes_xyxy(boxes: np.ndarray, scale_x: float, scale_y: float) -> np.ndarray:
    if boxes.size == 0:
        return boxes
    scaled = boxes.copy().astype(np.float32)
    scaled[:, [0, 2]] = scaled[:, [0, 2]] * scale_x
    scaled[:, [1, 3]] = scaled[:, [1, 3]] * scale_y
    return scaled


def maybe_apply_source_transform(
    image: np.ndarray, source_resize: int, jpeg_quality: int
) -> np.ndarray:
    out = image
    if source_resize > 0:
        out = cv2.resize(
            out, (source_resize, source_resize), interpolation=cv2.INTER_AREA
        )
    if 1 <= jpeg_quality <= 100:
        ok, enc = cv2.imencode(
            ".jpg",
            out,
            [int(cv2.IMWRITE_JPEG_QUALITY), int(jpeg_quality)],
        )
        if ok:
            dec = cv2.imdecode(enc, cv2.IMREAD_COLOR)
            if dec is not None:
                out = dec
    return out


def coco_bbox_xywh_to_xyxy(box_xywh: list[float]) -> np.ndarray:
    x, y, w, h = box_xywh
    return np.array([x, y, x + w, y + h], dtype=np.float32)


def match_predictions(
    pred_boxes: np.ndarray,
    pred_scores: np.ndarray,
    gt_boxes: np.ndarray,
    match_iou_thr: float,
) -> tuple[int, int, int, list[float]]:
    if pred_boxes.size == 0:
        return 0, 0, int(gt_boxes.shape[0]), []

    order = np.argsort(pred_scores)[::-1]
    used_gt: set[int] = set()
    tp = 0
    fp = 0
    matched_ious: list[float] = []

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
            matched_ious.append(best_iou)
        else:
            fp += 1

    fn = int(gt_boxes.shape[0]) - tp
    return tp, fp, fn, matched_ious


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
    categories = coco.get("categories", [])

    ann_by_image: dict[int, list[dict[str, Any]]] = {}
    for ann in annotations:
        ann_by_image.setdefault(int(ann.get("image_id", -1)), []).append(ann)

    if args.max_images > 0:
        images = images[: args.max_images]

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

    rows: list[dict[str, Any]] = []
    failed_images = 0
    latency_ms_values: list[float] = []
    preprocess_ms_values: list[float] = []
    postprocess_ms_values: list[float] = []
    pipeline_ms_values: list[float] = []
    all_match_ious: list[float] = []
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

        t_pipeline0 = time.perf_counter()
        image = cv2.imread(str(img_path))
        if image is None:
            continue
        image = maybe_apply_source_transform(
            image=image,
            source_resize=args.source_resize,
            jpeg_quality=args.jpeg_quality,
        )

        gt_ann = ann_by_image.get(image_id, [])
        gt_boxes = np.array(
            [coco_bbox_xywh_to_xyxy(a.get("bbox", [0, 0, 0, 0])) for a in gt_ann],
            dtype=np.float32,
        )
        if gt_boxes.size == 0:
            gt_boxes = np.zeros((0, 4), dtype=np.float32)

        ann_w = float(img_info.get("width", image.shape[1]))
        ann_h = float(img_info.get("height", image.shape[0]))
        cur_h, cur_w = image.shape[:2]
        sx = float(cur_w) / ann_w if ann_w > 0 else 1.0
        sy = float(cur_h) / ann_h if ann_h > 0 else 1.0
        if abs(sx - 1.0) > 1e-6 or abs(sy - 1.0) > 1e-6:
            gt_boxes = scale_boxes_xyxy(gt_boxes, sx, sy)

        t_pre0 = time.perf_counter()
        inp = preprocess(image, args.input_size)
        preprocess_ms = (time.perf_counter() - t_pre0) * 1000.0

        t_inf0 = time.perf_counter()
        try:
            outputs = cast(list[np.ndarray], session.run(None, {input_name: inp}))
            infer_ms = (time.perf_counter() - t_inf0) * 1000.0
        except Exception as e:
            failed_images += 1
            gt_count_fail = int(gt_boxes.shape[0])
            pipeline_ms_fail = (time.perf_counter() - t_pipeline0) * 1000.0
            rows.append(
                {
                    "index": i,
                    "image_id": image_id,
                    "file_name": file_name,
                    "gt_count": gt_count_fail,
                    "pred_count": 0,
                    "count_error": -gt_count_fail,
                    "abs_count_error": gt_count_fail,
                    "tp": 0,
                    "fp": 0,
                    "fn": gt_count_fail,
                    "precision": 0.0,
                    "recall": 0.0,
                    "f1": 0.0,
                    "top_score": 0.0,
                    "preprocess_ms": preprocess_ms,
                    "infer_ms": 0.0,
                    "postprocess_ms": 0.0,
                    "pipeline_ms": pipeline_ms_fail,
                    "mean_match_iou": 0.0,
                    "error": str(e),
                }
            )
            total_fn += gt_count_fail
            abs_err_sum += gt_count_fail
            sq_err_sum += gt_count_fail * gt_count_fail
            preprocess_ms_values.append(preprocess_ms)
            postprocess_ms_values.append(0.0)
            pipeline_ms_values.append(pipeline_ms_fail)
            continue

        t_post0 = time.perf_counter()
        boxes_input, scores = parse_outputs(outputs)
        keep = nms_indices(boxes_input, scores, args.score_thr, args.nms_iou)

        pred_boxes = (
            boxes_input[keep] if keep.size > 0 else np.zeros((0, 4), dtype=np.float32)
        )
        pred_scores = (
            scores[keep] if keep.size > 0 else np.zeros((0,), dtype=np.float32)
        )
        h, w = image.shape[:2]
        pred_boxes = scale_boxes_from_input(
            pred_boxes, src_w=w, src_h=h, input_size=args.input_size
        )

        tp, fp, fn, ious = match_predictions(
            pred_boxes=pred_boxes,
            pred_scores=pred_scores,
            gt_boxes=gt_boxes,
            match_iou_thr=args.match_iou,
        )
        postprocess_ms = (time.perf_counter() - t_post0) * 1000.0
        pipeline_ms = (time.perf_counter() - t_pipeline0) * 1000.0

        gt_count = int(gt_boxes.shape[0])
        pred_count = int(pred_boxes.shape[0])
        err = pred_count - gt_count

        precision_i = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall_i = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1_i = (
            2 * precision_i * recall_i / (precision_i + recall_i)
            if (precision_i + recall_i) > 0
            else 0.0
        )

        rows.append(
            {
                "index": i,
                "image_id": image_id,
                "file_name": file_name,
                "gt_count": gt_count,
                "pred_count": pred_count,
                "count_error": err,
                "abs_count_error": abs(err),
                "tp": tp,
                "fp": fp,
                "fn": fn,
                "precision": round(precision_i, 6),
                "recall": round(recall_i, 6),
                "f1": round(f1_i, 6),
                "top_score": float(pred_scores.max() if pred_scores.size > 0 else 0.0),
                "preprocess_ms": preprocess_ms,
                "infer_ms": infer_ms,
                "postprocess_ms": postprocess_ms,
                "pipeline_ms": pipeline_ms,
                "mean_match_iou": float(statistics.fmean(ious)) if ious else 0.0,
                "error": "",
            }
        )

        total_tp += tp
        total_fp += fp
        total_fn += fn
        abs_err_sum += abs(err)
        sq_err_sum += err * err
        if pred_count == gt_count:
            exact_count_matches += 1

        latency_ms_values.append(infer_ms)
        preprocess_ms_values.append(preprocess_ms)
        postprocess_ms_values.append(postprocess_ms)
        pipeline_ms_values.append(pipeline_ms)
        all_match_ious.extend(ious)

    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "index",
                "image_id",
                "file_name",
                "gt_count",
                "pred_count",
                "count_error",
                "abs_count_error",
                "tp",
                "fp",
                "fn",
                "precision",
                "recall",
                "f1",
                "top_score",
                "preprocess_ms",
                "infer_ms",
                "postprocess_ms",
                "pipeline_ms",
                "mean_match_iou",
                "error",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    n = len(rows)
    global_precision = (
        total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0.0
    )
    global_recall = (
        total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0.0
    )
    global_f1 = (
        2 * global_precision * global_recall / (global_precision + global_recall)
        if (global_precision + global_recall) > 0
        else 0.0
    )

    summary = {
        "dataset_root": str(root),
        "split": args.split,
        "annotation_file": str(ann_file),
        "images_dir": str(split_dir),
        "model": str(model_path),
        "input_size": args.input_size,
        "intra_threads": args.intra_threads,
        "inter_threads": args.inter_threads,
        "score_thr": args.score_thr,
        "nms_iou": args.nms_iou,
        "match_iou": args.match_iou,
        "source_resize": args.source_resize,
        "jpeg_quality": args.jpeg_quality,
        "num_images_evaluated": n,
        "failed_images": failed_images,
        "num_categories": len(categories),
        "total_tp": total_tp,
        "total_fp": total_fp,
        "total_fn": total_fn,
        "global_precision": global_precision,
        "global_recall": global_recall,
        "global_f1": global_f1,
        "count_mae": (abs_err_sum / n) if n > 0 else 0.0,
        "count_rmse": math.sqrt(sq_err_sum / n) if n > 0 else 0.0,
        "count_exact_accuracy": (exact_count_matches / n) if n > 0 else 0.0,
        "latency_ms_mean": float(statistics.fmean(latency_ms_values))
        if latency_ms_values
        else 0.0,
        "latency_ms_min": float(min(latency_ms_values)) if latency_ms_values else 0.0,
        "latency_ms_max": float(max(latency_ms_values)) if latency_ms_values else 0.0,
        "latency_ms_p50": percentile(latency_ms_values, 0.5),
        "latency_ms_p90": percentile(latency_ms_values, 0.9),
        "preprocess_ms_mean": float(statistics.fmean(preprocess_ms_values))
        if preprocess_ms_values
        else 0.0,
        "postprocess_ms_mean": float(statistics.fmean(postprocess_ms_values))
        if postprocess_ms_values
        else 0.0,
        "pipeline_ms_mean": float(statistics.fmean(pipeline_ms_values))
        if pipeline_ms_values
        else 0.0,
        "pipeline_ms_p90": percentile(pipeline_ms_values, 0.9),
        "mean_match_iou": float(statistics.fmean(all_match_ious))
        if all_match_ious
        else 0.0,
        "per_image_csv": str(out_csv),
    }

    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    print("=== Evaluation Summary ===")
    for k, v in summary.items():
        print(f"{k}: {v}")


if __name__ == "__main__":
    main()
