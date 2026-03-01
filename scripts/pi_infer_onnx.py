import argparse
import csv
import time
from pathlib import Path
from typing import cast

import cv2
import numpy as np
import onnxruntime as ort


def preprocess_image(image_bgr: np.ndarray, size: int = 800) -> np.ndarray:
    rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
    img = cv2.resize(rgb, (size, size)).astype("float32") / 255.0
    mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
    std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
    img = (img - mean) / std
    img = np.transpose(img, (2, 0, 1))
    return img[np.newaxis, ...].astype("float32")


def run_folder(
    model_path: Path,
    image_dir: Path,
    threshold: float,
    out_csv: Path,
    intra_threads: int,
    inter_threads: int,
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

    rows = []
    total_ms = 0.0
    count = 0

    for p in sorted(image_dir.glob("*.jpg")):
        image = cv2.imread(str(p))
        if image is None:
            continue
        inp = preprocess_image(image)
        t0 = time.perf_counter()
        outs = cast(list[np.ndarray], sess.run(None, {inp_name: inp}))
        dt_ms = (time.perf_counter() - t0) * 1000.0
        boxes = outs[0][0]
        scores = outs[2][0]
        det_count = int((scores >= threshold).sum())
        top_score = float(scores.max() if scores.size > 0 else 0.0)
        rows.append((p.name, det_count, top_score, dt_ms, int(boxes.shape[0])))
        total_ms += dt_ms
        count += 1

    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            ["image", "count_ge_thr", "top_score", "latency_ms", "raw_boxes"]
        )
        writer.writerows(rows)

    avg = total_ms / count if count else 0.0
    print(f"model={model_path}")
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
    p.add_argument("--out-csv", required=True, help="Output CSV path")
    p.add_argument(
        "--intra-threads", type=int, default=0, help="ORT intra-op threads, 0=default"
    )
    p.add_argument(
        "--inter-threads", type=int, default=0, help="ORT inter-op threads, 0=default"
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()
    run_folder(
        Path(args.model),
        Path(args.image_dir),
        args.threshold,
        Path(args.out_csv),
        args.intra_threads,
        args.inter_threads,
    )


if __name__ == "__main__":
    main()
