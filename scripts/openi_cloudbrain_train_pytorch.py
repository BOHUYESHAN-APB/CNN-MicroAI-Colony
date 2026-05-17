from __future__ import annotations

import argparse
import importlib
from importlib import util as importlib_util
import json
import os
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Any, Optional

from openi_prepare_dataset import prepare_dataset


DATASET_PROFILE_TO_ZIPS = {
    "clean": ["colony_clean_v1.zip"],
    "merged": ["merged_dataset.zip"],
    "auto": ["colony_clean_v1.zip", "merged_dataset.zip"],
}


def _prepare_c2net_context() -> Optional[Any]:
    try:
        context_mod = importlib.import_module("c2net.context")
        prepare_fn = getattr(context_mod, "prepare", None)
        if callable(prepare_fn):
            return prepare_fn()
        return None
    except Exception as ex:
        print("c2net prepare unavailable:", ex)
        return None


def _ctx_path(ctx: Any, name: str) -> Optional[Path]:
    if ctx is None:
        return None
    value = getattr(ctx, name, None)
    if not value:
        return None
    try:
        return Path(str(value))
    except Exception:
        return None


def _split_shell_like(value: str) -> list[str]:
    try:
        return shlex.split(value)
    except ValueError:
        return [value]


def _normalize_cli_token(token: str) -> str:
    normalized = token.strip()
    if normalized.startswith("---"):
        dash_count = len(normalized) - len(normalized.lstrip("-"))
        normalized = "--" + normalized[dash_count:]
    return normalized


def _dedupe_non_empty(values: list[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for value in values:
        normalized = value.strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        out.append(normalized)
    return out


def _extract_zip_names_from_unknown(unknown_args: list[str]) -> list[str]:
    token_pool: list[str] = []
    for arg in unknown_args:
        normalized_arg = _normalize_cli_token(arg)
        token_pool.append(normalized_arg)
        if "=" not in normalized_arg:
            continue
        _, rhs = normalized_arg.split("=", 1)
        if rhs:
            token_pool.extend(_normalize_cli_token(t) for t in _split_shell_like(rhs))

    extracted: list[str] = []
    i = 0
    while i < len(token_pool):
        token = token_pool[i]
        if token == "--zip-name":
            if i + 1 < len(token_pool):
                value = token_pool[i + 1].strip()
                if value and not value.startswith("--"):
                    extracted.append(value)
            i += 2
            continue

        if token.startswith("--zip-name="):
            value = token.split("=", 1)[1].strip()
            if value:
                extracted.append(value)

        i += 1

    return _dedupe_non_empty(extracted)


def _extract_flag_value_from_unknown(
    unknown_args: list[str],
    flag_names: tuple[str, ...],
) -> Optional[str]:
    token_pool: list[str] = []
    for arg in unknown_args:
        normalized_arg = _normalize_cli_token(arg)
        token_pool.append(normalized_arg)
        if "=" not in normalized_arg:
            continue
        _, rhs = normalized_arg.split("=", 1)
        if rhs:
            token_pool.extend(_normalize_cli_token(t) for t in _split_shell_like(rhs))

    i = 0
    while i < len(token_pool):
        token = token_pool[i]
        for flag in flag_names:
            if token == flag:
                if i + 1 < len(token_pool):
                    value = token_pool[i + 1].strip()
                    if value and not value.startswith("--"):
                        return value
            if token.startswith(f"{flag}="):
                value = token.split("=", 1)[1].strip()
                if value:
                    return value
        i += 1
    return None


def _resolve_profile_zip_names(profile: str) -> list[str]:
    normalized = (profile or "auto").strip().lower()
    return DATASET_PROFILE_TO_ZIPS.get(normalized, DATASET_PROFILE_TO_ZIPS["auto"])


def _load_multi_data_items(unknown_args: list[str]) -> list[dict[str, Any]]:
    raw_value = _extract_flag_value_from_unknown(unknown_args, ("--multi_data_url",))
    if not raw_value:
        return []

    try:
        parsed = json.loads(raw_value)
    except Exception:
        return []

    if isinstance(parsed, dict):
        parsed = [parsed]

    out: list[dict[str, Any]] = []
    if isinstance(parsed, list):
        for item in parsed:
            if isinstance(item, dict):
                out.append(item)
    return out


def _extract_multi_data_container_paths(items: list[dict[str, Any]]) -> list[str]:
    out: list[str] = []
    for item in items:
        value = item.get("containerPath")
        if isinstance(value, str) and value.strip():
            out.append(value.strip())

    return _dedupe_non_empty(out)


def _extract_multi_data_dataset_names(items: list[dict[str, Any]]) -> list[str]:
    out: list[str] = []
    for item in items:
        value = item.get("dataset_name")
        if isinstance(value, str) and value.strip():
            out.append(value.strip())

    return _dedupe_non_empty(out)


def _build_dataset_hint_dirs(
    c2net_dataset_path: Optional[Path],
    dataset_names: list[str],
    container_paths: list[str],
) -> list[str]:
    hint_dirs: list[str] = []
    if c2net_dataset_path is not None:
        hint_dirs.append(str(c2net_dataset_path))
        for name in dataset_names:
            hint_dirs.append(str(c2net_dataset_path / name))

    hint_dirs.extend(container_paths)

    existing = []
    for path in _dedupe_non_empty(hint_dirs):
        p = Path(path)
        if p.exists() and p.is_dir():
            existing.append(str(p))

    return _dedupe_non_empty(existing)


def _resolve_explicit_zip_path(
    container_paths: list[str],
    zip_names: list[str],
) -> Optional[Path]:
    preferred = [n.lower() for n in zip_names]
    preferred_set = set(preferred)
    fallback_zips: list[Path] = []

    for container_path in container_paths:
        base = Path(container_path)
        if not base.exists() or not base.is_dir():
            continue

        for zip_name in zip_names:
            exact = base / zip_name
            if exact.exists() and exact.is_file():
                return exact

        try:
            children = list(base.iterdir())
        except Exception:
            continue

        lowered = {name.lower() for name in zip_names}
        for child in children:
            if child.is_file() and child.name.lower() in lowered:
                return child

        stack: list[tuple[Path, int]] = [(base, 0)]
        scanned_dirs = 0
        matched_preferred: dict[str, Path] = {}
        while stack:
            current, depth = stack.pop()
            if depth > 4:
                continue

            try:
                nested = list(current.iterdir())
            except Exception:
                continue

            for entry in nested:
                if entry.is_file() and entry.suffix.lower() == ".zip":
                    entry_name = entry.name.lower()
                    if (
                        entry_name in preferred_set
                        and entry_name not in matched_preferred
                    ):
                        matched_preferred[entry_name] = entry
                    fallback_zips.append(entry)
                elif entry.is_dir():
                    if entry.name in {".git", "__pycache__", "node_modules"}:
                        continue
                    if scanned_dirs >= 3000:
                        continue
                    scanned_dirs += 1
                    stack.append((entry, depth + 1))

        for preferred_name in preferred:
            if preferred_name in matched_preferred:
                return matched_preferred[preferred_name]

    if fallback_zips:
        try:
            fallback_zips.sort(key=lambda p: p.stat().st_size, reverse=True)
        except Exception:
            pass
        return fallback_zips[0]

    return None


def _summarize_container_paths(container_paths: list[str]) -> list[str]:
    summaries: list[str] = []
    for value in container_paths:
        p = Path(value)
        if not p.exists():
            summaries.append(f"{value} missing")
            continue
        if not p.is_dir():
            summaries.append(f"{value} exists but is not a directory")
            continue

        try:
            entries = sorted((child.name for child in p.iterdir()))
        except Exception as ex:
            summaries.append(f"{value} unreadable ({ex})")
            continue

        sample = entries[:8]
        sample_text = ", ".join(sample) if sample else "<empty>"
        summaries.append(f"{value} entries={len(entries)} sample=[{sample_text}]")

    return summaries


def _resolve_train_script_path(
    train_script: str,
    c2net_code_path: Optional[Path],
    code_name: Optional[str],
) -> Path:
    relative = Path(train_script)
    candidates: list[Path] = [relative]

    if c2net_code_path is not None:
        if code_name:
            candidates.append(c2net_code_path / code_name / relative)
            candidates.append(c2net_code_path / code_name.lower() / relative)
        candidates.append(c2net_code_path / relative)

        try:
            child_dirs = sorted(
                [p for p in c2net_code_path.iterdir() if p.is_dir()],
                key=lambda p: p.name,
            )
        except Exception:
            child_dirs = []

        for child in child_dirs:
            candidates.append(child / relative)

    deduped: list[Path] = []
    seen: set[str] = set()
    for candidate in candidates:
        key = str(candidate)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(candidate)

    for candidate in deduped:
        if candidate.exists():
            return candidate

    return deduped[0]


def _is_writable_dir(path: Path) -> bool:
    try:
        path.mkdir(parents=True, exist_ok=True)
        probe = path / ".openi_write_probe"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
        return True
    except Exception:
        return False


def _pick_default_extract_dir(c2net_dataset_path: Optional[Path]) -> Path:
    candidates: list[Path] = []
    if c2net_dataset_path is not None:
        candidates.append(c2net_dataset_path / "data_extracted")
    candidates.extend(
        [
            Path("/cache/dataset/data_extracted"),
            Path("/tmp/data_extracted"),
            Path("_data"),
        ]
    )

    for candidate in candidates:
        if _is_writable_dir(candidate):
            return candidate

    return Path("_data")


def _module_available(module_name: str) -> bool:
    try:
        return importlib_util.find_spec(module_name) is not None
    except Exception:
        return False


def _pick_requirements_file(train_script: Path) -> Optional[Path]:
    candidates = [
        train_script.parent / "requirements.txt",
        train_script.parent.parent / "requirements.txt",
    ]
    for candidate in candidates:
        if candidate.exists() and candidate.is_file():
            return candidate
    return None


def _parse_torch_major_minor() -> Optional[tuple[int, int]]:
    try:
        import torch

        version = str(getattr(torch, "__version__", ""))
        if not version:
            return None
        core = version.split("+", 1)[0]
        parts = core.split(".")
        if len(parts) < 2:
            return None
        return int(parts[0]), int(parts[1])
    except Exception:
        return None


def _resolve_torchvision_spec() -> str:
    explicit = os.environ.get("OPENI_TORCHVISION_SPEC", "").strip()
    if explicit:
        return explicit

    mapping = {
        (2, 0): "torchvision==0.15.*",
        (2, 1): "torchvision==0.16.*",
        (2, 2): "torchvision==0.17.*",
        (2, 3): "torchvision==0.18.*",
        (2, 4): "torchvision==0.19.*",
    }
    mm = _parse_torch_major_minor()
    if mm in mapping:
        return mapping[mm]
    return "torchvision"


def _torchvision_custom_ops_ok() -> bool:
    try:
        import torch
        import torchvision
        from torchvision.ops import nms

        boxes = torch.tensor(
            [[0.0, 0.0, 2.0, 2.0], [0.0, 0.0, 2.0, 2.0]],
            dtype=torch.float32,
        )
        scores = torch.tensor([0.9, 0.8], dtype=torch.float32)
        _ = nms(boxes, scores, 0.5)
        _ = torchvision.__version__
        return True
    except Exception:
        return False


def _ensure_runtime_dependencies(train_script: Path) -> None:
    required_modules = {
        "torch": "torch",
        "torchvision": "torchvision",
        "PIL": "Pillow",
        "numpy": "numpy",
        "tqdm": "tqdm",
    }

    missing_pkgs = [
        pkg for module, pkg in required_modules.items() if not _module_available(module)
    ]
    torchvision_broken = False
    if (
        not missing_pkgs
        and _module_available("torch")
        and _module_available("torchvision")
    ):
        torchvision_broken = not _torchvision_custom_ops_ok()
        if torchvision_broken:
            missing_pkgs = ["torchvision"]

    if not missing_pkgs:
        return

    auto_install = os.environ.get("OPENI_AUTO_INSTALL_DEPS", "1").strip().lower()
    if auto_install in {"0", "false", "no", "off"}:
        raise SystemExit(
            "Missing runtime packages: "
            + ", ".join(missing_pkgs)
            + ". Set OPENI_AUTO_INSTALL_DEPS=1 or use a PyTorch-compatible image."
        )

    req_file = _pick_requirements_file(train_script)
    install_from_requirements = os.environ.get("OPENI_INSTALL_FROM_REQUIREMENTS", "0")
    missing_set = set(missing_pkgs)
    pip_cmd = [sys.executable, "-m", "pip", "install"]
    if missing_set == {"torchvision"} and _module_available("torch"):
        reinstall_flags = ["--no-deps"]
        if torchvision_broken or os.environ.get(
            "OPENI_FORCE_REINSTALL_TORCHVISION", ""
        ).strip().lower() in {
            "1",
            "true",
            "yes",
            "on",
        }:
            reinstall_flags = ["--force-reinstall", "--no-deps"]
        install_cmd = [*pip_cmd, *reinstall_flags, _resolve_torchvision_spec()]
    elif missing_set.issubset({"torch", "torchvision"}):
        targets = sorted(missing_set)
        if "torchvision" in targets:
            targets = [
                _resolve_torchvision_spec() if item == "torchvision" else item
                for item in targets
            ]
        install_cmd = [*pip_cmd, *targets]
    elif req_file is not None and install_from_requirements.strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }:
        install_cmd = [*pip_cmd, "-r", str(req_file)]
    else:
        install_cmd = [
            *pip_cmd,
            *sorted(set(missing_pkgs)),
        ]

    print("Missing runtime packages:", missing_pkgs)
    print("Installing dependencies:", " ".join(install_cmd))
    sys.stdout.flush()
    result = subprocess.run(install_cmd)
    if result.returncode != 0:
        raise SystemExit(
            "Dependency install failed. Consider switching to a PyTorch-compatible image."
        )


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="OpenI CloudBrain entry: unzip dataset and run PyTorch training",
    )
    parser.add_argument(
        "--zip-name",
        action="append",
        default=None,
        help="Dataset zip filename to search for (repeatable). Overrides dataset profile default",
    )
    parser.add_argument(
        "--dataset-profile",
        default=os.environ.get("COLONY_DATASET_PROFILE", "auto"),
        help="Dataset profile: clean|merged|auto (default: env COLONY_DATASET_PROFILE or auto)",
    )
    parser.add_argument(
        "--extract-dir",
        default=None,
        help="Where to extract dataset (default: dataset/cache/tmp path, not output dir)",
    )
    parser.add_argument(
        "--checkpoint-dir",
        default=None,
        help="Where to write checkpoints/logs (default: /model if exists, else ./model)",
    )
    parser.add_argument(
        "--device",
        default=os.environ.get("COLONY_DEVICE", "auto"),
        help="COLONY_DEVICE override: auto|cpu|cuda|npu (default: env or auto)",
    )
    parser.add_argument(
        "--train-script",
        default="models-colony-counting/in-use/main_models_train/train.py",
        help="Repo-relative training script path",
    )
    args, unknown_args = parser.parse_known_args(argv)
    cli_zip_names = list(args.zip_name or [])

    extra_zip_names = _extract_zip_names_from_unknown(unknown_args)

    profile_from_unknown = _extract_flag_value_from_unknown(
        unknown_args,
        ("--dataset-profile", "--dataset_profile"),
    )
    if profile_from_unknown:
        args.dataset_profile = profile_from_unknown

    profile_zip_names = _resolve_profile_zip_names(args.dataset_profile)
    combined_zip_names = _dedupe_non_empty(
        [*cli_zip_names, *extra_zip_names, *profile_zip_names]
    )
    args.zip_name = combined_zip_names

    c2net_ctx = _prepare_c2net_context()
    c2net_code_path = _ctx_path(c2net_ctx, "code_path")
    c2net_dataset_path = _ctx_path(c2net_ctx, "dataset_path")
    c2net_output_path = _ctx_path(c2net_ctx, "output_path")

    code_name = _extract_flag_value_from_unknown(unknown_args, ("--code_name",))

    multi_data_items = _load_multi_data_items(unknown_args)
    dataset_container_paths = _extract_multi_data_container_paths(multi_data_items)
    dataset_names = _extract_multi_data_dataset_names(multi_data_items)
    dataset_hint_dirs = _build_dataset_hint_dirs(
        c2net_dataset_path,
        dataset_names,
        dataset_container_paths,
    )

    if c2net_dataset_path is not None:
        os.environ["OPENI_C2NET_DATASET_PATH"] = str(c2net_dataset_path)
    if dataset_names:
        os.environ["OPENI_DATASET_NAMES"] = ";".join(dataset_names)
    if dataset_hint_dirs:
        os.environ["OPENI_DATASET_HINT_DIRS"] = ";".join(dataset_hint_dirs)
        explicit_zip_path = _resolve_explicit_zip_path(
            dataset_hint_dirs,
            args.zip_name,
        )
        if explicit_zip_path is not None:
            os.environ["OPENI_DATASET_ZIP"] = str(explicit_zip_path)

    if unknown_args:
        print("Ignoring platform-injected args:", " ".join(unknown_args))
    if c2net_code_path is not None:
        print("C2NET_CODE_PATH=", str(c2net_code_path))
    if c2net_dataset_path is not None:
        print("C2NET_DATASET_PATH=", str(c2net_dataset_path))
    if c2net_output_path is not None:
        print("C2NET_OUTPUT_PATH=", str(c2net_output_path))
    print("DATASET_PROFILE=", args.dataset_profile)
    print("ZIP_CANDIDATES=", args.zip_name)
    if dataset_names:
        print("DATASET_NAMES=", dataset_names)
    if dataset_hint_dirs:
        print("DATASET_HINT_DIRS=", dataset_hint_dirs)
        for item in _summarize_container_paths(dataset_hint_dirs):
            print("DATASET_CONTAINER_INFO=", item)
    if os.environ.get("OPENI_DATASET_ZIP"):
        print("OPENI_DATASET_ZIP=", os.environ["OPENI_DATASET_ZIP"])

    if args.extract_dir is None:
        args.extract_dir = str(_pick_default_extract_dir(c2net_dataset_path))

    if args.checkpoint_dir is None:
        if c2net_output_path is not None:
            args.checkpoint_dir = str(c2net_output_path / "model")
        else:
            args.checkpoint_dir = "/model" if Path("/model").exists() else "model"

    extract_dir = Path(args.extract_dir)
    ckpt_dir = Path(args.checkpoint_dir)
    ckpt_dir.mkdir(parents=True, exist_ok=True)

    prepared = prepare_dataset(
        zip_path=None, zip_names=args.zip_name, extract_dir=extract_dir
    )
    dataset_root = prepared.dataset_root

    env = os.environ.copy()
    env["COLONY_DATASET_ROOT"] = str(dataset_root)
    env["COLONY_CHECKPOINT_DIR"] = str(ckpt_dir)
    env["COLONY_DEVICE"] = str(args.device)

    train_script = _resolve_train_script_path(
        args.train_script,
        c2net_code_path,
        code_name,
    )
    if not train_script.exists():
        raise SystemExit(f"Train script not found: {train_script}")

    _ensure_runtime_dependencies(train_script)

    cmd = [sys.executable, str(train_script)]
    print("Running:", " ".join(cmd))
    print("COLONY_DATASET_ROOT=", env["COLONY_DATASET_ROOT"])
    print("COLONY_CHECKPOINT_DIR=", env["COLONY_CHECKPOINT_DIR"])
    print("COLONY_DEVICE=", env["COLONY_DEVICE"])
    print("EXTRACT_DIR=", str(extract_dir))
    sys.stdout.flush()

    p = subprocess.run(cmd, env=env)
    return int(p.returncode)


if __name__ == "__main__":
    raise SystemExit(main())
