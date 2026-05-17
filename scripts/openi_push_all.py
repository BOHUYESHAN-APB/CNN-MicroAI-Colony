"""Push local changes to ALL branches on the OpenI remote.

The OpenI remote has 3 branches (all at 4f2166a historically):
  - cloudbrain
  - main
  - master

After making local changes, push to ALL 3 branches so they stay in sync.

Usage:
  # Push current HEAD to all 3 branches:
  python scripts/openi_push_all.py

  # Dry run (show what would happen):
  python scripts/openi_push_all.py --dry-run

  # Custom remote:
  python scripts/openi_push_all.py --remote origin

  # Push a specific branch:
  python scripts/openi_push_all.py --source feature-branch
"""

import argparse
import subprocess
import sys

OPENI_REMOTE = "openi"
OPENI_URL = "git@openi.pcl.ac.cn:BOHUYESHAN-APB/CNN-MicroAI-Colony.git"
BRANCHES = ["cloudbrain", "main", "master"]


def run_cmd(cmd: list[str], check: bool = True) -> str:
    result = subprocess.run(cmd, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"FAILED: {' '.join(cmd)}", file=sys.stderr)
        print(result.stderr, file=sys.stderr)
        sys.exit(1)
    return result.stdout.strip()


def main() -> None:
    parser = argparse.ArgumentParser(description="Push to all OpenI branches")
    parser.add_argument("--remote", default=OPENI_REMOTE, help="Remote name")
    parser.add_argument("--source", default="", help="Source branch (default: HEAD)")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    # Ensure remote exists
    remotes = run_cmd(["git", "remote", "-v"])
    if args.remote not in remotes:
        print(f"Adding remote '{args.remote}' -> {OPENI_URL}")
        run_cmd(["git", "remote", "add", args.remote, OPENI_URL])

    # Get source ref
    if args.source:
        source = args.source
    else:
        source = run_cmd(["git", "rev-parse", "--abbrev-ref", "HEAD"])

    print(f"Source: {source}")
    print(f"Remote: {args.remote} ({OPENI_URL})")
    print(f"Target branches: {', '.join(BRANCHES)}")
    print()

    for branch in BRANCHES:
        cmd = ["git", "push", args.remote, f"{source}:{branch}", "--force-with-lease"]
        print(f"  {'[DRY] ' if args.dry_run else ''}{' '.join(cmd)}")
        if not args.dry_run:
            out = run_cmd(cmd, check=False)
            if out:
                print(f"    {out}")

    print("\nDone. All 3 branches pushed.")


if __name__ == "__main__":
    main()
