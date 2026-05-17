"""Build a .deb package for the Pi CTk colony counting app.

Packages apps/pi_ctk/ into a Debian package suitable for Raspberry Pi
ARM64 (Ubuntu/Debian). Optionally deploys to a remote Pi via SSH.

The .deb installs:
  - /opt/cnn-microai-pi/  — application code
  - /usr/local/bin/cnn-microai-pi — launcher script
  - systemd service (optional)

Usage:
  # Build .deb locally:
  python scripts/build_pi_ctk_deb.py --version 0.1.0

  # Build + deploy to Pi:
  python scripts/build_pi_ctk_deb.py --version 0.1.0 ^
    --host 192.168.11.239 --user pi --install

  # Dry run:
  python scripts/build_pi_ctk_deb.py --version 0.1.0 --dry-run
"""

import argparse
import os
import shutil
import stat
import subprocess
import tempfile
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
    raise RuntimeError(f"SSH failed for {user}@{host}: {last_err}")


def run_remote(ssh, cmd):
    stdin, stdout, stderr = ssh.exec_command(cmd)
    code = stdout.channel.recv_exit_status()
    return (
        code,
        stdout.read().decode("utf-8", "ignore"),
        stderr.read().decode("utf-8", "ignore"),
    )


def build_deb(repo_root: Path, version: str, output_dir: Path) -> Path:
    """Build a .deb package from apps/pi_ctk/."""
    pkg_name = "cnn-microai-pi"
    arch = "arm64"
    work = Path(tempfile.mkdtemp(prefix=f"{pkg_name}_deb_"))
    pkg_dir = work / pkg_name

    # Create directory structure
    install_dir = pkg_dir / "opt" / "cnn-microai-pi"
    bin_dir = pkg_dir / "usr" / "local" / "bin"
    deb_dir = pkg_dir / "DEBIAN"
    systemd_dir = pkg_dir / "lib" / "systemd" / "system"

    for d in [install_dir, bin_dir, deb_dir, systemd_dir]:
        d.mkdir(parents=True, exist_ok=True)

    # Copy application code
    app_src = repo_root / "apps" / "pi_ctk"
    if not app_src.exists():
        raise FileNotFoundError(f"pi_ctk app not found: {app_src}")

    for item in app_src.iterdir():
        dst = install_dir / item.name
        if item.is_dir():
            shutil.copytree(item, dst)
        else:
            shutil.copy2(item, dst)

    # Copy ONNX model (if exists)
    model_src = repo_root / "onnx model"
    if model_src.exists():
        model_dst = install_dir / "onnx_model"
        model_dst.mkdir(exist_ok=True)
        for f in model_src.glob("*.onnx"):
            shutil.copy2(f, model_dst / f.name)

    # Create launcher script
    launcher = bin_dir / "cnn-microai-pi"
    launcher.write_text(
        '#!/bin/bash\ncd /opt/cnn-microai-pi\nexec python3 -m apps.pi_ctk.main "$@"\n',
        encoding="utf-8",
    )
    launcher.chmod(launcher.stat().st_mode | stat.S_IEXEC)

    # Create DEBIAN/control
    control = (
        f"Package: {pkg_name}\n"
        f"Version: {version}\n"
        f"Section: science\n"
        f"Priority: optional\n"
        f"Architecture: {arch}\n"
        f"Depends: python3 (>= 3.9), python3-pip, python3-venv\n"
        f"Maintainer: CNN-MicroAI Team <project@example.com>\n"
        f"Description: Colony counting Pi CTk application\n"
        f" Raspberry Pi colony counting application with CTk UI,\n"
        f" ONNX inference, and batch processing capabilities.\n"
    )
    (deb_dir / "control").write_text(control, encoding="utf-8")

    # Create postinst (install deps)
    postinst = deb_dir / "postinst"
    postinst.write_text(
        "#!/bin/bash\n"
        "set -e\n"
        "cd /opt/cnn-microai-pi\n"
        "python3 -m venv /opt/cnn-microai-pi/.venv || true\n"
        "/opt/cnn-microai-pi/.venv/bin/pip install --upgrade pip\n"
        "/opt/cnn-microai-pi/.venv/bin/pip install -r requirements.txt\n"
        "echo 'CNN-MicroAI Pi installed. Run: cnn-microai-pi'\n",
        encoding="utf-8",
    )
    postinst.chmod(postinst.stat().st_mode | stat.S_IEXEC)

    # Build .deb
    output_dir.mkdir(parents=True, exist_ok=True)
    deb_filename = f"{pkg_name}_{version}_{arch}.deb"
    deb_path = output_dir / deb_filename

    result = subprocess.run(
        ["dpkg-deb", "--build", str(pkg_dir), str(deb_path)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"dpkg-deb failed: {result.stderr}")

    print(f"Built: {deb_path} ({deb_path.stat().st_size / 1024:.0f} KB)")

    # Cleanup
    shutil.rmtree(work)
    return deb_path


def deploy_and_install(deb_path: Path, host: str, user: str) -> None:
    """Upload and install .deb on remote Pi."""
    ssh, pwd = connect_ssh(host, user)
    print(f"Connected: {user}@{host}")

    try:
        remote_deb = f"/tmp/{deb_path.name}"
        sftp = ssh.open_sftp()
        try:
            sftp.put(str(deb_path), remote_deb)
            print(f"Uploaded: {remote_deb}")
        finally:
            sftp.close()

        print("Installing on Pi...")
        code, out, err = run_remote(ssh, f"sudo dpkg -i {remote_deb}")
        if code != 0:
            print(f"dpkg -i output: {err or out}")
            print("Trying apt-get -f install...")
            run_remote(ssh, "sudo apt-get install -f -y")

        code, out, err = run_remote(
            ssh, f"dpkg -s cnn-microai-pi 2>/dev/null | head -5"
        )
        if code == 0:
            print(f"Package status:\n{out}")
        else:
            print("Warning: could not verify package status")

        print(f"\nDone. Run on Pi: cnn-microai-pi")
    finally:
        ssh.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Pi CTk .deb package")
    parser.add_argument("--version", default="0.1.0", help="Package version")
    parser.add_argument(
        "--output-dir", default="dist", help="Output directory for .deb"
    )
    parser.add_argument("--host", default="", help="Pi IP for remote install")
    parser.add_argument("--user", default="pi", help="SSH username")
    parser.add_argument(
        "--install", action="store_true", help="Install on Pi after build"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Only print planned actions"
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    output_dir = repo_root / args.output_dir

    if args.dry_run:
        print(f"Would build .deb version={args.version}")
        print(f"Output: {output_dir}")
        if args.host and args.install:
            print(f"Would install on {args.user}@{args.host}")
        return

    deb_path = build_deb(repo_root, args.version, output_dir)

    if args.host and args.install:
        deploy_and_install(deb_path, args.host, args.user)
    elif args.host:
        print(
            f"To install: python scripts/build_pi_ctk_deb.py --version {args.version} --host {args.host} --install"
        )


if __name__ == "__main__":
    main()
