"""Validate MindSpore count-regression ONNX model on local COCO dataset.

This script validates MindSpore-exported ONNX models (count regression, NOT detection)
against COCO-format datasets. It computes MAE/RMSE/latency metrics for comparison
with training-time validation results.

MindSpore models in this project are COUNT REGRESSION models:
  - Input: (1, 3, 384, 384) image tensor
  - Output: (1, 1) scalar count prediction

Usage:
  python scripts/validate_mindspore_onnx.py ^
    --dataset-root temp/dataset/colony_clean_v1 ^
    --split valid ^
    --model temp/training/v1-cleandataset-160ep/models-0/model/mindspore_top1_epoch158_rmse83.6455.onnx ^
    --subset 50 ^
    --out-json temp/validate/v1_top1_valid.json

  # Compare all 3 top models:
  for %m in top1 top2 top3; do
    python scripts/validate_mindspore_onnx.py ^
      --dataset-root temp/dataset/colony_clean_v1 ^
      --split valid ^
      --model "temp/training/v1-cleandataset-160ep/models-0/model/mindspore_%m.onnx" ^
      --subset 0 ^
      --out-json "temp/validate/v1_%m_valid.json"
  done
"""

import argparse
import csv
import json
import math
import random
import statistics
import time
from pathlib import Path
from typing import cast

import cv2
import numpy as np
import onnxruntime as ort


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate MindSpore ONNX count-regression model"
    )
    parser.add_argument(
        "--dataset-root", required=True, help="Dataset root (COCO format)"
    )
    parser.add_argument("--split", default="valid", help="Split name")
    parser.add_argument("--ann-file", default="", help="COCO annotations path")
    parser.add_argument("--images-dir", default="", help="Images directory")
    parser.add_argument("--model", required=True, help="ONNX model path")
    parser.add_argument("--subset", type=int, default=50, help="Subset size (0=all)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--input-size", type=int, default=384, help="Model input size")
    parser.add_argument("--warmup", type=int, default=3, help="Warmup iterations")
    parser.add_argument("--out-json", default="", help="Summary JSON output")
    parser.add_argument("--out-csv", default="", help="Per-image CSV output")
    return parser.parse_args()


def preprocess(image_bgr: np.ndarray, size: int) -> np.ndarray:
    """Center-crop resize preprocessing matching MindSpore training config."""
    rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
    img = cv2.resize(rgb, (size, size)).astype("float32") / 255.0
    # ImageNet normalization (standard for count regression)
    mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
    std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
    img = (img - mean) / std
    img = np.transpose(img, (2, 0, 1))  # HWC -> CHW
    return img[np.newaxis, ...].astype("float32")  # NCHW


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

    if not ann_file.exists():
        raise FileNotFoundError(f"Annotations not found: {ann_file}")
    if not model_path.exists():
        raise FileNotFoundError(f"Model not found: {model_path}")

    # Load COCO annotations
    coco = json.loads(ann_file.read_text(encoding="utf-8"))
    images = coco.get("images", [])
    annotations = coco.get("annotations", [])

    # Build per-image GT count
    count_by_image: dict[int, int] = {}
    for ann in annotations:
        img_id = int(ann.get("image_id", -1))
        count_by_image[img_id] = count_by_image.get(img_id, 0) + 1

    # Subset
    if args.subset > 0 and args.subset < len(images):
        rng = random.Random(args.seed)
        images = rng.sample(images, args.subset)
        print(f"Subset: {len(images)} images (seed={args.seed})")
    else:
        print(f"Evaluating all {len(images)} images")

    # Init ONNX
    so = ort.SessionOptions()
    so.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
    session = ort.InferenceSession(
        str(model_path), sess_options=so, providers=["CPUExecutionProvider"]
    )
    input_name = session.get_inputs()[0].name

    # Verify model type
    dummy = np.zeros((1, 3, args.input_size, args.input_size), dtype=np.float32)
    test_out = session.run(None, {input_name: dummy})
    out_shape = test_out[0].shape
    print(f"Model output shape: {out_shape}")
    if len(out_shape) != 2 or out_shape[1] != 1:
        print(f"WARNING: Expected count regression output (1,1), got {out_shape}")

    # Warmup
    for _ in range(args.warmup):
        session.run(None, {input_name: dummy})

    # Evaluate
    rows = []
    latencies = []
    abs_errors = []
    sq_errors = []

    for i, img_info in enumerate(images, start=1):
        file_name = str(img_info.get("file_name", ""))
        image_id = int(img_info.get("id", -1))

        img_path = split_dir / file_name
        if not img_path.exists():
            img_path = split_dir / Path(file_name).name

        image = cv2.imread(str(img_path))
        if image is None:
            continue

        gt_count = count_by_image.get(image_id, 0)

        inp = preprocess(image, args.input_size)
        t0 = time.perf_counter()
        try:
            out = cast(list[np.ndarray], session.run(None, {input_name: inp}))
            pred_count = max(0, int(round(float(out[0].flatten()[0]))))
        except Exception as e:
            pred_count = 0
            print(f"  Error on {file_name}: {e}")
        latency_ms = (time.perf_counter() - t0) * 1000.0
        latencies.append(latency_ms)

        err = pred_count - gt_count
        abs_errors.append(abs(err))
        sq_errors.append(err * err)

        rows.append(
            {
                "index": i,
                "file_name": file_name,
                "gt_count": gt_count,
                "pred_count": pred_count,
                "error": err,
                "abs_error": abs(err),
                "latency_ms": round(latency_ms, 2),
            }
        )

    n = len(rows)
    if n == 0:
        print("No images evaluated.")
        return

    mae = statistics.fmean(abs_errors)
    rmse = math.sqrt(statistics.fmean(sq_errors))
    exact_match = sum(1 for r in rows if r["error"] == 0)

    summary = {
        "model": str(model_path),
        "dataset_root": str(root),
        "split": args.split,
        "num_images": n,
        "subset_size": args.subset,
        "input_size": args.input_size,
        # Count metrics (training-comparable)
        "count_mae": round(mae, 4),
        "count_rmse": round(rmse, 4),
        "exact_match_rate": round(exact_match / n, 4),
        # Latency
        "latency_ms_p50": round(percentile(latencies, 0.5), 2),
        "latency_ms_p90": round(percentile(latencies, 0.9), 2),
        "latency_ms_mean": round(statistics.fmean(latencies), 2),
        # Per-image detail
        "per_image_csv": args.out_csv,
    }

    # Save JSON
    if args.out_json:
        out_json = Path(args.out_json)
        out_json.parent.mkdir(parents=True, exist_ok=True)
        out_json.write_text(
            json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    # Save CSV
    if args.out_csv:
        out_csv = Path(args.out_csv)
        out_csv.parent.mkdir(parents=True, exist_ok=True)
        with open(out_csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "index",
                    "file_name",
                    "gt_count",
                    "pred_count",
                    "error",
                    "abs_error",
                    "latency_ms",
                ],
            )
            writer.writeheader()
            writer.writerows(rows)

    # Print summary
    print(f"\n=== Validation Results ===")
    print(f"  Model: {model_path.name}")
    print(f"  Images: {n}")
    print(f"  MAE: {mae:.4f}")
    print(f"  RMSE: {rmse:.4f}")
    print(f"  Exact match: {exact_match}/{n} ({exact_match / n:.4f})")
    print(f"  Latency p50: {summary['latency_ms_p50']:.2f}ms")
    print(f"  Latency p90: {summary['latency_ms_p90']:.2f}ms")
    print()

    # Compare with training log results
    if "top1" in model_path.name:
        print("  Training log reported: RMSE 83.65 (epoch 158)")
        print(f"  Local validation RMSE: {rmse:.4f}")
        delta = rmse - 83.65
        print(f"  Delta: {delta:+.4f} ({'better' if delta < 0 else 'worse'})")
    elif "top2" in model_path.name:
        print("  Training log reported: RMSE 83.82 (epoch 146)")
        print(f"  Local validation RMSE: {rmse:.4f}")
    elif "top3" in model_path.name:
        print("  Training log reported: RMSE 83.90 (epoch 157)")
        print(f"  Local validation RMSE: {rmse:.4f}")


if __name__ == "__main__":
    main()
