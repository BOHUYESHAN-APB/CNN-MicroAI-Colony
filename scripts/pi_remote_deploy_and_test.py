import argparse
import posixpath
from pathlib import Path

import paramiko


PASSWORDS = ["123456", "12345678"]


def connect_ssh(host: str, user: str, timeout: int = 8):
    last_err = None
    for pwd in PASSWORDS:
        cli = paramiko.SSHClient()
        cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            cli.connect(
                hostname=host,
                username=user,
                password=pwd,
                timeout=timeout,
                banner_timeout=timeout,
                auth_timeout=timeout,
            )
            return cli, pwd
        except Exception as e:
            last_err = e
            try:
                cli.close()
            except Exception:
                pass
    raise RuntimeError(f"SSH connection failed for {user}@{host}: {last_err}")


def run_remote(ssh: paramiko.SSHClient, cmd: str) -> tuple[int, str, str]:
    stdin, stdout, stderr = ssh.exec_command(cmd)
    code = stdout.channel.recv_exit_status()
    return (
        code,
        stdout.read().decode("utf-8", "ignore"),
        stderr.read().decode("utf-8", "ignore"),
    )


def sftp_put(sftp: paramiko.SFTPClient, local_path: Path, remote_path: str) -> None:
    sftp.put(str(local_path), remote_path)


def ensure_remote_dirs(ssh: paramiko.SSHClient, base: str) -> None:
    cmd = (
        f"mkdir -p {base}/models {base}/images {base}/scripts {base}/reports && "
        f"python3 --version"
    )
    code, out, err = run_remote(ssh, cmd)
    if code != 0:
        raise RuntimeError(f"Failed to create remote directories: {err or out}")


def install_deps(ssh: paramiko.SSHClient, base: str) -> None:
    cmd = (
        f"python3 -m venv {base}/.venv && "
        f"{base}/.venv/bin/python -m pip install --upgrade pip && "
        f"{base}/.venv/bin/pip install onnxruntime numpy opencv-python-headless"
    )
    code, out, err = run_remote(ssh, cmd)
    if code != 0:
        raise RuntimeError(f"Dependency installation failed: {err or out}")


def deploy_and_test(host: str, user: str, repo_root: Path, dry_run: bool) -> None:
    local_models = [
        repo_root / "temp" / "openi_yolo11_eval" / "yolo11n_advanced" / "best.onnx",
    ]
    local_images = sorted((repo_root / "test-pic").glob("*.jpg"))
    local_runner = repo_root / "scripts" / "pi_infer_onnx.py"

    for p in local_models + [local_runner]:
        if not p.exists():
            raise FileNotFoundError(f"Missing local file: {p}")
    if not local_images:
        raise FileNotFoundError("No test images found under test-pic/*.jpg")

    if dry_run:
        print("DRY RUN")
        print("host:", host)
        print("user:", user)
        print("models:", [str(p) for p in local_models])
        print("images:", [str(p) for p in local_images])
        print("runner:", local_runner)
        return

    ssh, used_pwd = connect_ssh(host, user)
    print(f"SSH connected: {user}@{host} with password={used_pwd}")
    remote_base = "/home/{}/cnn-microai".format(user)

    try:
        ensure_remote_dirs(ssh, remote_base)
        install_deps(ssh, remote_base)

        sftp = ssh.open_sftp()
        try:
            for model in local_models:
                remote_model = posixpath.join(remote_base, "models", model.name)
                sftp_put(sftp, model, remote_model)
            for img in local_images:
                remote_img = posixpath.join(remote_base, "images", img.name)
                sftp_put(sftp, img, remote_img)
            remote_runner = posixpath.join(remote_base, "scripts", "pi_infer_onnx.py")
            sftp_put(sftp, local_runner, remote_runner)
        finally:
            sftp.close()

        # Run current YOLO11 model
        fp32_cmd = (
            f"{remote_base}/.venv/bin/python {remote_base}/scripts/pi_infer_onnx.py "
            f"--model {remote_base}/models/best.onnx "
            f"--image-dir {remote_base}/images --threshold 0.45 "
            f"--out-csv {remote_base}/reports/fp32_report.csv"
        )
        code, out, err = run_remote(ssh, fp32_cmd)
        if code != 0:
            raise RuntimeError(f"FP32 inference failed: {err or out}")
        print(out)

        mem_cmd = "free -m && uname -a"
        code, out, err = run_remote(ssh, mem_cmd)
        if code == 0:
            print(out)
        else:
            print(err)

        print("Remote reports:")
        print(f"  {remote_base}/reports/fp32_report.csv")
    finally:
        ssh.close()


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Deploy ONNX to Raspberry Pi and run inference checks"
    )
    p.add_argument("--host", default="192.168.11.239", help="Raspberry Pi host")
    p.add_argument("--user", default="bhys", help="SSH username")
    p.add_argument(
        "--repo-root",
        default=str(Path(__file__).resolve().parents[1]),
        help="Repo root",
    )
    p.add_argument("--dry-run", action="store_true", help="Only print actions")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    deploy_and_test(args.host, args.user, Path(args.repo_root), args.dry_run)


if __name__ == "__main__":
    main()
