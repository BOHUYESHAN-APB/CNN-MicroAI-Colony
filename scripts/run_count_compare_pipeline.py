"""Compare pipeline: evaluate multiple ONNX models and produce a comparison report.

Runs eval_count_onnx_subset.py on each model, collects metrics, and writes
a side-by-side comparison CSV/JSON. Supports local + optional Pi benchmark.

This replaces the historical run_count_compare_pipeline.py which was
bound to the MindSpore/OpenI stack. Current version works with
PyTorch/ORT detector ONNX models.

Usage:
  # Compare FP32 vs QDQ on subset-10:
  python scripts/run_count_compare_pipeline.py ^
    --dataset-root merged_dataset ^
    --split test ^
    --models "onnx model\checkpoint_epoch_31.onnx" "onnx model\checkpoint_epoch_31.static_qdq.onnx" ^
    --labels fp32 qdq ^
    --subset 10 ^
    --out-csv reports\compare_subset10.csv ^
    --out-json reports\compare_subset10.json

  # Compare with Pi benchmark (requires SSH):
  python scripts/run_count_compare_pipeline.py ^
    --dataset-root merged_dataset ^
    --split test ^
    --models "onnx model\checkpoint_epoch_31.onnx" "onnx model\checkpoint_epoch_31.static_qdq.onnx" ^
    --labels fp32 qdq ^
    --subset 10 ^
    --pi-host 192.168.11.239 ^
    --pi-user pi ^
    --out-csv reports\compare_full.csv ^
    --out-json reports\compare_full.json
"""

import argparse
import csv
import json
import subprocess
import sys
import tempfile
from pathlib import Path


def run_eval(
    dataset_root: str,
    split: str,
    model: str,
    label: str,
    subset: int,
    score_thr: float,
    nms_iou: float,
    match_iou: float,
    input_size: int,
    work_dir: Path,
) -> dict:
    """Run eval_count_onnx_subset.py for one model and return summary dict."""
    out_csv = work_dir / f"{label}_eval.csv"
    out_json = work_dir / f"{label}_eval.json"

    cmd = [
        sys.executable,
        "scripts/eval_count_onnx_subset.py",
        "--dataset-root",
        dataset_root,
        "--split",
        split,
        "--model",
        model,
        "--subset",
        str(subset),
        "--seed",
        "42",
        "--score-thr",
        str(score_thr),
        "--nms-iou",
        str(nms_iou),
        "--match-iou",
        str(match_iou),
        "--input-size",
        str(input_size),
        "--out-csv",
        str(out_csv),
        "--out-json",
        str(out_json),
    ]

    print(f"\n--- Evaluating: {label} ({model}) ---")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  FAILED: {result.stderr[:500]}")
        return {"label": label, "model": model, "error": result.stderr[:200]}

    summary = json.loads(out_json.read_text(encoding="utf-8"))
    summary["label"] = label
    print(
        f"  MAE={summary['count_mae']:.2f}  RMSE={summary['count_rmse']:.2f}  "
        f"p50={summary['latency_ms_p50']:.1f}ms  p90={summary['latency_ms_p90']:.1f}ms"
    )
    return summary


def run_pi_benchmark(
    host: str, user: str, model: str, label: str, work_dir: Path
) -> dict:
    """Run pi_remote_count_benchmark.py for one model and return result dict."""
    out_json = work_dir / f"{label}_pi_bench.json"

    cmd = [
        sys.executable,
        "scripts/pi_remote_count_benchmark.py",
        "--host",
        host,
        "--user",
        user,
        "--model",
        model,
        "--warmup",
        "5",
        "--iters",
        "50",
        "--out-json",
        str(out_json),
    ]

    print(f"\n--- Pi benchmark: {label} ({model}) on {user}@{host} ---")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  FAILED: {result.stderr[:500]}")
        return {"label": label, "pi_error": result.stderr[:200]}

    bench = json.loads(out_json.read_text(encoding="utf-8"))
    bench["label"] = label
    print(
        f"  Pi p50={bench['latency_ms_p50']:.1f}ms  p90={bench['latency_ms_p90']:.1f}ms"
    )
    return bench


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare multiple ONNX colony models")
    parser.add_argument("--dataset-root", required=True)
    parser.add_argument("--split", default="test")
    parser.add_argument("--models", nargs="+", required=True, help="ONNX model paths")
    parser.add_argument(
        "--labels", nargs="+", required=True, help="Labels for each model"
    )
    parser.add_argument("--subset", type=int, default=10, help="Subset size (0=all)")
    parser.add_argument("--score-thr", type=float, default=0.45)
    parser.add_argument("--nms-iou", type=float, default=0.30)
    parser.add_argument("--match-iou", type=float, default=0.50)
    parser.add_argument("--input-size", type=int, default=800)
    parser.add_argument("--pi-host", default="", help="Pi IP for remote benchmark")
    parser.add_argument("--pi-user", default="pi")
    parser.add_argument("--out-csv", required=True)
    parser.add_argument("--out-json", required=True)
    args = parser.parse_args()

    if len(args.models) != len(args.labels):
        raise ValueError(
            f"models ({len(args.models)}) and labels ({len(args.labels)}) count mismatch"
        )

    work_dir = Path(tempfile.mkdtemp(prefix="colony_compare_"))
    print(f"Work dir: {work_dir}")

    # Local evaluation
    results = []
    for model, label in zip(args.models, args.labels):
        r = run_eval(
            dataset_root=args.dataset_root,
            split=args.split,
            model=model,
            label=label,
            subset=args.subset,
            score_thr=args.score_thr,
            nms_iou=args.nms_iou,
            match_iou=args.match_iou,
            input_size=args.input_size,
            work_dir=work_dir,
        )
        # Optional Pi benchmark
        if args.pi_host:
            pi = run_pi_benchmark(
                host=args.pi_host,
                user=args.pi_user,
                model=model,
                label=label,
                work_dir=work_dir,
            )
            r["pi_latency_ms_p50"] = pi.get("latency_ms_p50", None)
            r["pi_latency_ms_p90"] = pi.get("latency_ms_p90", None)
            r["pi_latency_ms_mean"] = pi.get("latency_ms_mean", None)
        results.append(r)

    # Comparison table
    key_cols = [
        "label",
        "model",
        "num_images",
        "count_mae",
        "count_rmse",
        "detection_rate_proxy",
        "precision",
        "recall",
        "f1",
        "latency_ms_p50",
        "latency_ms_p90",
        "latency_ms_mean",
    ]
    if args.pi_host:
        key_cols += ["pi_latency_ms_p50", "pi_latency_ms_p90", "pi_latency_ms_mean"]

    out_csv = Path(args.out_csv)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=key_cols, extrasaction="ignore")
        writer.writeheader()
        for r in results:
            writer.writerow(r)

    out_json = Path(args.out_json)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(
        json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    print(f"\n=== Comparison ===")
    print(f"CSV: {out_csv}")
    print(f"JSON: {out_json}")
    print()
    # Print table
    header = f"{'label':<12} {'MAE':>8} {'RMSE':>8} {'det_rate':>9} {'p50ms':>8} {'p90ms':>8}"
    if args.pi_host:
        header += f" {'pi_p50':>8} {'pi_p90':>8}"
    print(header)
    print("-" * len(header))
    for r in results:
        row = (
            f"{r.get('label', '?'):<12} "
            f"{r.get('count_mae', 0):>8.2f} "
            f"{r.get('count_rmse', 0):>8.2f} "
            f"{r.get('detection_rate_proxy', 0):>9.4f} "
            f"{r.get('latency_ms_p50', 0):>8.1f} "
            f"{r.get('latency_ms_p90', 0):>8.1f}"
        )
        if args.pi_host:
            row += (
                f" {r.get('pi_latency_ms_p50', 0) or 0:>8.1f} "
                f"{r.get('pi_latency_ms_p90', 0) or 0:>8.1f}"
            )
        print(row)


if __name__ == "__main__":
    main()
