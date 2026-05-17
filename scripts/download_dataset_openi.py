"""Download dataset from OpenI CloudBrain.

Usage:
  python scripts/download_dataset_openi.py
  python scripts/download_dataset_openi.py --target-dir temp/dataset --workers 10

Requires: pip install openi
"""

import argparse
import os
import shutil
import sys
from pathlib import Path


def download_dataset(target_dir: Path, workers: int = 10) -> None:
    try:
        from openi import openi_download_file
    except ImportError:
        print("ERROR: 'openi' package not installed.")
        print("Run: pip install openi")
        print()
        print("Alternative: manually download from OpenI web UI:")
        print("  1. Go to https://openi.pcl.ac.cn/datasets/bhys/mic")
        print("  2. Download colony_clean_v1.zip")
        print(f"  3. Extract to {target_dir}/")
        sys.exit(1)

    target_dir.mkdir(parents=True, exist_ok=True)
    print(f"Downloading dataset to {target_dir} (workers={workers})...")

    # Download from OpenI dataset repo
    openi_download_file(
        "bhys/mic",
        repo_type="dataset",
        local_dir=str(target_dir),
        max_workers=workers,
    )
    print(f"Done. Files saved to {target_dir}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Download colony dataset from OpenI")
    parser.add_argument(
        "--target-dir",
        default="temp/dataset",
        help="Local directory to save dataset (default: temp/dataset)",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=10,
        help="Number of download workers (default: 10)",
    )
    args = parser.parse_args()

    target = Path(args.target_dir)
    download_dataset(target, args.workers)


if __name__ == "__main__":
    main()
