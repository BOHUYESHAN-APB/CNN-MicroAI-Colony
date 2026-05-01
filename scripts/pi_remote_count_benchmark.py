r"""Pi remote latency benchmark for colony ONNX models.

Deploys an ONNX model + test images to a Raspberry Pi via SSH, runs inference
multiple times (cold start + warm runs), and collects structured latency metrics.

Outputs:
  - Local JSON with p50/p90/p99/mean/std latency, memory info, model metadata

Relationship to existing scripts:
  - scripts/pi_remote_deploy_and_test.py: deployment + FP32/QDQ comparison
  - scripts/pi_remote_count_benchmark.py (this file): focused latency benchmark
  - scripts/eval_count_onnx_subset.py: local accuracy evaluation

Usage:
  # Benchmark single model on Pi
  python scripts/pi_remote_count_benchmark.py ^
    --host 192.168.11.239 ^
    --user bhys ^
    --model "temp\openi_yolo11_eval\yolo11n_advanced\best.onnx" ^
    --warmup 5 --iters 50 ^
    --out-json reports\pi_bench_fp32.json

  # Benchmark QDQ quantized model
  python scripts/pi_remote_count_benchmark.py ^
    --host 192.168.11.239 ^
    --user bhys ^
    --model "onnx model\checkpoint_epoch_31.static_qdq.onnx" ^
    --warmup 5 --iters 50 ^
    --out-json reports\pi_bench_qdq.json
"""

import argparse
import json
import math
import statistics
import time
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


# Benchmark script to run on the Pi
_BENCHMARK_SCRIPT = r"""\
import json
import statistics
import time
import sys

import numpy as np
import onnxruntime as ort

model_path = sys.argv[1]
warmup = int(sys.argv[2])
iters = int(sys.argv[3])
input_size_arg = int(sys.argv[4])
out_json = sys.argv[5]

# Load model
so = ort.SessionOptions()
so.intra_op_num_threads = 2
so.inter_op_num_threads = 1
so.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
so.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL

sess = ort.InferenceSession(model_path, sess_options=so, providers=["CPUExecutionProvider"])
input_name = sess.get_inputs()[0].name
input_shape = sess.get_inputs()[0].shape
if input_size_arg > 0:
    input_size = input_size_arg
else:
    h = input_shape[-2] if len(input_shape) >= 4 else None
    w = input_shape[-1] if len(input_shape) >= 4 else None
    if isinstance(h, int) and isinstance(w, int) and h > 0 and h == w:
        input_size = int(h)
    else:
        raise RuntimeError(f"Unable to infer input size from {input_shape}")

# Random input (simulates preprocessed image)
dummy = np.random.randn(1, 3, input_size, input_size).astype(np.float32)

# Warmup
for _ in range(warmup):
    sess.run(None, {input_name: dummy})

# Benchmark
latencies = []
for i in range(iters):
    t0 = time.perf_counter()
    sess.run(None, {input_name: dummy})
    latencies.append((time.perf_counter() - t0) * 1000.0)

# Memory info
import subprocess
try:
    mem_out = subprocess.check_output(["free", "-m"], text=True)
except Exception:
    mem_out = "N/A"

summary = {
    "model_path": model_path,
    "input_shape": input_shape,
    "input_size": input_size,
    "warmup": warmup,
    "iters": iters,
    "latency_ms_p50": round(sorted(latencies)[len(latencies)//2], 2),
    "latency_ms_p90": round(sorted(latencies)[int(len(latencies)*0.9)], 2),
    "latency_ms_p99": round(sorted(latencies)[int(len(latencies)*0.99)-1], 2),
    "latency_ms_mean": round(statistics.fmean(latencies), 2),
    "latency_ms_std": round(statistics.stdev(latencies), 2),
    "latency_ms_min": round(min(latencies), 2),
    "latency_ms_max": round(max(latencies), 2),
    "throughput_ips": round(1000.0 / statistics.fmean(latencies), 2),
    "memory_info": mem_out.strip(),
    "raw_latencies_ms": [round(x, 2) for x in latencies],
}

with open(out_json, "w") as f:
    json.dump(summary, f, indent=2)

print(json.dumps(summary, indent=2))
"""


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Benchmark ONNX inference latency on Raspberry Pi"
    )
    parser.add_argument("--host", default="192.168.11.239", help="Pi IP address")
    parser.add_argument("--user", default="bhys", help="SSH username")
    parser.add_argument("--model", required=True, help="Local ONNX model path")
    parser.add_argument("--warmup", type=int, default=5, help="Warmup iterations")
    parser.add_argument("--iters", type=int, default=50, help="Benchmark iterations")
    parser.add_argument(
        "--input-size",
        type=int,
        default=0,
        help="Model input size. 0 means auto-detect from ONNX.",
    )
    parser.add_argument("--out-json", required=True, help="Output JSON path")
    parser.add_argument(
        "--dry-run", action="store_true", help="Only print planned actions"
    )
    args = parser.parse_args()

    model_path = Path(args.model)
    if not model_path.exists():
        raise FileNotFoundError(f"Model not found: {model_path}")

    if args.dry_run:
        print(f"Would deploy {model_path} to {args.user}@{args.host}")
        print(f"Warmup={args.warmup}, Iters={args.iters}, Input={args.input_size or 'auto'}")
        print(f"Output: {args.out_json}")
        return

    # Connect
    ssh, pwd = connect_ssh(args.host, args.user)
    print(f"Connected: {args.user}@{args.host}")

    remote_base = f"/home/{args.user}/cnn-bench"
    try:
        # Setup
        run_remote(ssh, f"mkdir -p {remote_base}/models {remote_base}/reports")

        # Install deps if needed
        code, out, _ = run_remote(ssh, "python3 -c 'import onnxruntime'")
        if code != 0:
            print("Installing onnxruntime on Pi...")
            run_remote(
                ssh,
                f"python3 -m pip install --user onnxruntime numpy 2>&1 || true",
            )

        # Upload model + benchmark script
        sftp = ssh.open_sftp()
        try:
            remote_model = f"{remote_base}/models/{model_path.name}"
            sftp_put(sftp, model_path, remote_model)

            # Write benchmark script on Pi
            remote_script = f"{remote_base}/bench.py"
            with sftp.open(remote_script, "w") as f:
                f.write(_BENCHMARK_SCRIPT)
        finally:
            sftp.close()

        # Run benchmark
        remote_json = f"{remote_base}/reports/bench_result.json"
        cmd = (
            f"python3 {remote_script} "
            f"{remote_model} {args.warmup} {args.iters} {args.input_size} {remote_json}"
        )
        print(f"Running benchmark on Pi...")
        code, out, err = run_remote(ssh, cmd)
        if code != 0:
            raise RuntimeError(f"Benchmark failed: {err or out}")

        print(out)

        # Download result
        sftp = ssh.open_sftp()
        try:
            out_json = Path(args.out_json)
            out_json.parent.mkdir(parents=True, exist_ok=True)
            sftp.get(remote_json, str(out_json))
            print(f"Result saved to {out_json}")
        finally:
            sftp.close()

    finally:
        ssh.close()


if __name__ == "__main__":
    main()
