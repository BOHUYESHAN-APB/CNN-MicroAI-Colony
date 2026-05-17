"""
从 OpenI 云端克隆旧训练代码到本地子仓库。

使用方法：
  python scripts/clone_openi_repo.py --url <OPENI_GIT_URL>

  例：
  python scripts/clone_openi_repo.py --url ssh://git@openeuler.mindspore.cn:22/microai/colony-counting.git

可选参数：
  --branch <branch>     指定克隆的分支（默认 main 或 master）
  --ssh-key <path>      指定 SSH 私钥路径（默认 .ssh/id_ed25519）
  --dest <dir>          指定克隆目标目录（默认 openi-archive）
  --test-only           只测试连接，不克隆
"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SSH_KEY = REPO_ROOT / ".ssh" / "id_ed25519"


def ssh_cmd(ssh_key: Path) -> str:
    return (
        f'ssh -i "{ssh_key}" -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10'
    )


def test_connection(ssh_key: Path, host: str, port: int = 22) -> bool:
    """Test SSH connection to remote host."""
    cmd = f'ssh -i "{ssh_key}" -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 -p {port} -T git@{host}'
    print(f"Testing connection: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
    # SSH test connections often return non-zero (git-shell denies interactive login)
    # but if there's no timeout/connection error, it's OK
    stderr = result.stderr.lower()
    if (
        "connection refused" in stderr
        or "no route to host" in stderr
        or "could not resolve" in stderr
    ):
        print(f"  FAILED: {result.stderr[:200]}")
        return False
    print(f"  OK (exit code {result.returncode}, stderr: {result.stderr[:100]})")
    return True


def clone_repo(ssh_key: Path, url: str, dest: Path, branch: str = "") -> None:
    """Clone remote repo into local subdirectory."""
    env = os.environ.copy()
    env["GIT_SSH_COMMAND"] = ssh_cmd(ssh_key)

    cmd = ["git", "clone"]
    if branch:
        cmd += ["-b", branch]
    cmd += [url, str(dest)]

    print(f"Cloning: {' '.join(cmd)}")
    result = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=300)
    if result.returncode != 0:
        print(f"ERROR: {result.stderr[:500]}")
        sys.exit(1)

    print(f"Cloned to {dest}")
    # List files
    files = list(dest.rglob("*.py"))
    print(f"\nPython files found: {len(files)}")
    for f in sorted(files)[:30]:
        rel = f.relative_to(dest)
        print(f"  {rel}")
    if len(files) > 30:
        print(f"  ... and {len(files) - 30} more")


def extract_key_scripts(archive_dir: Path) -> None:
    """Copy MindSpore key scripts to scripts/ if found in archive."""
    key_scripts = [
        "mindspore_colony_train.py",
        "openi_cloudbrain_train_mindspore.py",
        "export_mindspore_count_ckpt_to_onnx.py",
        "openi_dataset_upload.py",
    ]
    scripts_dir = REPO_ROOT / "scripts"
    scripts_dir.mkdir(exist_ok=True)

    found = []
    for name in key_scripts:
        # Search in archive
        matches = list(archive_dir.rglob(name))
        if matches:
            src = matches[0]
            dst = scripts_dir / name
            shutil.copy2(src, dst)
            found.append(name)
            print(f"  EXTRACTED: {src.relative_to(archive_dir)} -> scripts/{name}")

    print(f"\nExtracted {len(found)}/{len(key_scripts)} key scripts:")
    for s in found:
        print(f"  ✅ scripts/{s}")
    missing = [n for n in key_scripts if n not in found]
    for m in missing:
        print(f"  ❌ NOT FOUND: {m}")


def main():
    parser = argparse.ArgumentParser(description="Clone OpenI cloud repo")
    parser.add_argument("--url", default="", help="OpenI git clone URL")
    parser.add_argument("--branch", default="", help="Branch to clone")
    parser.add_argument(
        "--ssh-key", default=str(DEFAULT_SSH_KEY), help="SSH private key path"
    )
    parser.add_argument("--dest", default="openi-archive", help="Clone destination")
    parser.add_argument("--test-only", action="store_true", help="Only test connection")
    parser.add_argument(
        "--extract", action="store_true", help="Auto-extract key scripts after clone"
    )
    args = parser.parse_args()

    ssh_key = Path(args.ssh_key)
    if not ssh_key.exists():
        print(f"SSH key not found: {ssh_key}")
        print(f"Key should be at: {DEFAULT_SSH_KEY}")
        sys.exit(1)

    if args.url:
        # Extract host from URL
        url = args.url
        # ssh://git@host:port/path -> host
        import re

        m = re.search(r"@([^:]+)", url)
        host = m.group(1) if m else url.split("/")[-2]

        if args.test_only:
            test_connection(ssh_key, host)
            return

        dest = REPO_ROOT / args.dest
        if dest.exists():
            print(f"Destination exists: {dest}")
            shutil.rmtree(dest)

        clone_repo(ssh_key, url, dest, args.branch)

        if args.extract:
            print("\n--- Extracting key scripts ---")
            extract_key_scripts(dest)
    else:
        print("No --url provided.")
        print(
            "Usage: python scripts/clone_openi_repo.py --url ssh://git@openeuler.mindspore.cn:22/xxx/yyy.git"
        )
        print(f"\nSSH key ready at: {ssh_key}")
        print(
            "Test connection: python scripts/clone_openi_repo.py --url ssh://... --test-only"
        )


if __name__ == "__main__":
    main()
