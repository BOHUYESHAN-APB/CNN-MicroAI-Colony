import argparse
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Upload dataset file/folder to OpenI using openi SDK",
    )
    parser.add_argument(
        "repo_id",
        help="Dataset full name in owner/dataset_name form",
    )
    parser.add_argument(
        "path",
        help="Local file or folder path to upload",
    )
    parser.add_argument(
        "--upload-name",
        dest="upload_name",
        default=None,
        help="Optional remote path/name like subdir/file.zip (only for file upload)",
    )
    parser.add_argument(
        "-w",
        "--max-workers",
        dest="max_workers",
        type=int,
        default=10,
        help="Max parallel workers for upload (default: 10)",
    )
    parser.add_argument(
        "--token",
        dest="token",
        default=None,
        help="Optional OpenI token (otherwise use openi login or OPENI_TOKEN)",
    )
    parser.add_argument(
        "--endpoint",
        dest="endpoint",
        default=None,
        help="Optional OpenI endpoint (default: https://openi.pcl.ac.cn)",
    )
    args = parser.parse_args()

    target = Path(args.path)
    if not target.exists():
        raise SystemExit(f"Path not found: {target}")

    try:
        from openi.refactor.sdk import openi_upload_file
    except Exception as e:
        raise SystemExit(
            "openi SDK is not installed. Install with: python -m pip install openi==3.0.1\n"
            f"Import error: {e}"
        )

    openi_upload_file(
        repo_id=args.repo_id,
        file_or_folder_path=str(target),
        upload_name=args.upload_name,
        repo_type="dataset",
        max_workers=args.max_workers,
        endpoint=args.endpoint,
        token=args.token,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
