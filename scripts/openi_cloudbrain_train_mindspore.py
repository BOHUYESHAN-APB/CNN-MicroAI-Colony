from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

from openi_prepare_dataset import prepare_dataset
from openi_cloudbrain_train_pytorch import (
    _build_dataset_hint_dirs,
    _ctx_path,
    _dedupe_non_empty,
    _extract_flag_value_from_unknown,
    _extract_multi_data_container_paths,
    _extract_multi_data_dataset_names,
    _extract_zip_names_from_unknown,
    _load_multi_data_items,
    _module_available,
    _pick_default_extract_dir,
    _prepare_c2net_context,
    _resolve_explicit_zip_path,
    _resolve_profile_zip_names,
    _resolve_train_script_path,
    _summarize_container_paths,
)


def _ensure_mindspore_runtime_dependencies() -> None:
    required_modules = {
        "mindspore": "mindspore",
        "PIL": "Pillow",
        "numpy": "numpy",
        "tqdm": "tqdm",
    }

    missing_pkgs = [
        pkg for module, pkg in required_modules.items() if not _module_available(module)
    ]
    if not missing_pkgs:
        return

    auto_install = os.environ.get("OPENI_AUTO_INSTALL_DEPS", "0").strip().lower()
    if auto_install in {"0", "false", "no", "off"}:
        raise SystemExit(
            "Missing runtime packages: "
            + ", ".join(missing_pkgs)
            + ". Use a MindSpore-compatible image or set OPENI_AUTO_INSTALL_DEPS=1."
        )

    pip_retries = os.environ.get("OPENI_PIP_RETRIES", "6").strip() or "6"
    pip_timeout = os.environ.get("OPENI_PIP_TIMEOUT", "300").strip() or "300"
    install_cmd = [
        sys.executable,
        "-m",
        "pip",
        "install",
        "--retries",
        pip_retries,
        "--timeout",
        pip_timeout,
        *sorted(set(missing_pkgs)),
    ]

    print("Missing runtime packages:", missing_pkgs)
    print("Installing dependencies:", " ".join(install_cmd))
    sys.stdout.flush()
    result = subprocess.run(install_cmd)
    if result.returncode != 0:
        raise SystemExit(
            "Dependency install failed. Use a MindSpore image with built-in dependencies."
        )


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="OpenI CloudBrain entry: prepare dataset and run MindSpore training",
    )
    parser.add_argument(
        "--zip-name",
        action="append",
        default=None,
        help="Dataset zip filename to search for (repeatable). Overrides dataset profile default",
    )
    parser.add_argument(
        "--dataset-profile",
        default=os.environ.get("COLONY_DATASET_PROFILE", "clean"),
        help="Dataset profile: clean|merged|auto (default: env COLONY_DATASET_PROFILE or clean)",
    )
    parser.add_argument(
        "--extract-dir",
        default=None,
        help="Where to extract dataset (default: dataset/cache/tmp path, not output dir)",
    )
    parser.add_argument(
        "--checkpoint-dir",
        default=None,
        help="Where to write checkpoints/logs (default: c2net output/model if exists, else ./model)",
    )
    parser.add_argument(
        "--device",
        default=os.environ.get("COLONY_DEVICE", "npu"),
        help="COLONY_DEVICE override: auto|cpu|gpu|cuda|npu (default: env or npu)",
    )
    parser.add_argument(
        "--train-script",
        default="scripts/mindspore_colony_train.py",
        help="Repo-relative MindSpore training script path",
    )
    parser.add_argument(
        "--num-epochs",
        type=int,
        default=None,
        help="Override COLONY_NUM_EPOCHS",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=None,
        help="Override COLONY_BATCH_SIZE",
    )
    parser.add_argument(
        "--learning-rate",
        type=float,
        default=None,
        help="Override COLONY_LR",
    )
    parser.add_argument(
        "--image-size",
        type=int,
        default=None,
        help="Override COLONY_IMAGE_SIZE",
    )
    parser.add_argument(
        "--num-workers",
        type=int,
        default=None,
        help="Override COLONY_NUM_WORKERS (Ascend long-run stability: recommend <=4)",
    )
    parser.add_argument(
        "--valid-num-workers",
        type=int,
        default=None,
        help="Override COLONY_VALID_NUM_WORKERS (Ascend long-run stability: recommend 1)",
    )
    parser.add_argument(
        "--max-steps-per-epoch",
        type=int,
        default=None,
        help="Override COLONY_MAX_STEPS_PER_EPOCH",
    )
    parser.add_argument(
        "--stop-after-first-epoch",
        default=None,
        help="Override COLONY_STOP_AFTER_FIRST_EPOCH: 1/0, true/false",
    )
    parser.add_argument(
        "--stall-timeout-seconds",
        type=int,
        default=None,
        help="Override COLONY_STALL_TIMEOUT_SECONDS (force exit on long no-progress stall)",
    )
    parser.add_argument(
        "--preprocess-mode",
        choices=["resize", "center_crop_resize"],
        default=None,
        help="Override COLONY_PREPROCESS_MODE to align train/infer geometry",
    )
    parser.add_argument(
        "--use-augment",
        default=None,
        help="Override COLONY_USE_AUGMENT: 1/0, true/false",
    )
    parser.add_argument(
        "--topk",
        type=int,
        default=None,
        help="Override COLONY_TOPK for best-k checkpoint tracking/export",
    )
    parser.add_argument(
        "--model-variant",
        choices=["baseline", "morph_v2"],
        default=None,
        help="Override COLONY_MODEL_VARIANT",
    )
    parser.add_argument(
        "--aux-prior-weight",
        type=float,
        default=None,
        help="Override COLONY_AUX_PRIOR_WEIGHT",
    )
    parser.add_argument(
        "--lr-schedule",
        choices=["constant", "staged_dynamic"],
        default=None,
        help="Override COLONY_LR_SCHEDULE",
    )
    parser.add_argument(
        "--early-feature-lr-scale",
        type=float,
        default=None,
        help="Override COLONY_EARLY_FEATURE_LR_SCALE",
    )
    parser.add_argument(
        "--late-feature-lr-scale",
        type=float,
        default=None,
        help="Override COLONY_LATE_FEATURE_LR_SCALE",
    )
    parser.add_argument(
        "--head-lr-scale",
        type=float,
        default=None,
        help="Override COLONY_HEAD_LR_SCALE",
    )
    parser.add_argument(
        "--head-only-epochs",
        type=int,
        default=None,
        help="Override COLONY_HEAD_ONLY_EPOCHS",
    )
    parser.add_argument(
        "--late-unfreeze-epoch",
        type=int,
        default=None,
        help="Override COLONY_LATE_UNFREEZE_EPOCH",
    )
    parser.add_argument(
        "--dynamic-lr-min-scale",
        type=float,
        default=None,
        help="Override COLONY_DYNAMIC_LR_MIN_SCALE",
    )
    parser.add_argument(
        "--dynamic-lr-max-scale",
        type=float,
        default=None,
        help="Override COLONY_DYNAMIC_LR_MAX_SCALE",
    )
    parser.add_argument(
        "--final-lr-scale",
        type=float,
        default=None,
        help="Override COLONY_FINAL_LR_SCALE",
    )
    parser.add_argument(
        "--grad-clip-norm",
        type=float,
        default=None,
        help="Override COLONY_GRAD_CLIP_NORM",
    )
    parser.add_argument(
        "--enable-loss-jitter-trigger",
        default=None,
        help="Override COLONY_ENABLE_LOSS_JITTER_TRIGGER: 1/0, true/false",
    )
    parser.add_argument(
        "--loss-jitter-window",
        type=int,
        default=None,
        help="Override COLONY_LOSS_JITTER_WINDOW",
    )
    parser.add_argument(
        "--loss-jitter-threshold",
        type=float,
        default=None,
        help="Override COLONY_LOSS_JITTER_THRESHOLD",
    )
    parser.add_argument(
        "--loss-jitter-patience",
        type=int,
        default=None,
        help="Override COLONY_LOSS_JITTER_PATIENCE",
    )
    parser.add_argument(
        "--loss-jitter-boost",
        type=float,
        default=None,
        help="Override COLONY_LOSS_JITTER_BOOST",
    )
    parser.add_argument(
        "--loss-jitter-boost-steps",
        type=int,
        default=None,
        help="Override COLONY_LOSS_JITTER_BOOST_STEPS",
    )
    parser.add_argument(
        "--export-topk-onnx",
        default=None,
        help="Override COLONY_EXPORT_TOPK_ONNX: 1/0, true/false",
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
    args.zip_name = _dedupe_non_empty(
        [*cli_zip_names, *extra_zip_names, *profile_zip_names]
    )

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
        explicit_zip_path = _resolve_explicit_zip_path(dataset_hint_dirs, args.zip_name)
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
            args.checkpoint_dir = "/cache/output/model"

    extract_dir = Path(args.extract_dir)
    ckpt_dir = Path(args.checkpoint_dir)
    ckpt_dir.mkdir(parents=True, exist_ok=True)

    prepared = prepare_dataset(
        zip_path=None,
        zip_names=args.zip_name,
        extract_dir=extract_dir,
    )
    dataset_root = prepared.dataset_root

    env = os.environ.copy()
    env["COLONY_DATASET_ROOT"] = str(dataset_root)
    env["COLONY_CHECKPOINT_DIR"] = str(ckpt_dir)
    env["COLONY_DEVICE"] = str(args.device)

    if args.num_epochs is not None:
        env["COLONY_NUM_EPOCHS"] = str(args.num_epochs)
    if args.batch_size is not None:
        env["COLONY_BATCH_SIZE"] = str(args.batch_size)
    if args.learning_rate is not None:
        env["COLONY_LR"] = str(args.learning_rate)
    if args.image_size is not None:
        env["COLONY_IMAGE_SIZE"] = str(args.image_size)
    if args.num_workers is not None:
        env["COLONY_NUM_WORKERS"] = str(args.num_workers)
    if args.valid_num_workers is not None:
        env["COLONY_VALID_NUM_WORKERS"] = str(args.valid_num_workers)
    if args.max_steps_per_epoch is not None:
        env["COLONY_MAX_STEPS_PER_EPOCH"] = str(args.max_steps_per_epoch)
    if args.stop_after_first_epoch is not None:
        flag = str(args.stop_after_first_epoch).strip().lower()
        env["COLONY_STOP_AFTER_FIRST_EPOCH"] = (
            "1" if flag in {"1", "true", "yes", "on"} else "0"
        )
    if args.stall_timeout_seconds is not None:
        env["COLONY_STALL_TIMEOUT_SECONDS"] = str(args.stall_timeout_seconds)
    if args.preprocess_mode is not None:
        env["COLONY_PREPROCESS_MODE"] = str(args.preprocess_mode)
    if args.use_augment is not None:
        flag = str(args.use_augment).strip().lower()
        env["COLONY_USE_AUGMENT"] = "1" if flag in {"1", "true", "yes", "on"} else "0"
    if args.topk is not None:
        env["COLONY_TOPK"] = str(args.topk)
    if args.model_variant is not None:
        env["COLONY_MODEL_VARIANT"] = str(args.model_variant)
    if args.aux_prior_weight is not None:
        env["COLONY_AUX_PRIOR_WEIGHT"] = str(args.aux_prior_weight)
    if args.lr_schedule is not None:
        env["COLONY_LR_SCHEDULE"] = str(args.lr_schedule)
    if args.early_feature_lr_scale is not None:
        env["COLONY_EARLY_FEATURE_LR_SCALE"] = str(args.early_feature_lr_scale)
    if args.late_feature_lr_scale is not None:
        env["COLONY_LATE_FEATURE_LR_SCALE"] = str(args.late_feature_lr_scale)
    if args.head_lr_scale is not None:
        env["COLONY_HEAD_LR_SCALE"] = str(args.head_lr_scale)
    if args.head_only_epochs is not None:
        env["COLONY_HEAD_ONLY_EPOCHS"] = str(args.head_only_epochs)
    if args.late_unfreeze_epoch is not None:
        env["COLONY_LATE_UNFREEZE_EPOCH"] = str(args.late_unfreeze_epoch)
    if args.dynamic_lr_min_scale is not None:
        env["COLONY_DYNAMIC_LR_MIN_SCALE"] = str(args.dynamic_lr_min_scale)
    if args.dynamic_lr_max_scale is not None:
        env["COLONY_DYNAMIC_LR_MAX_SCALE"] = str(args.dynamic_lr_max_scale)
    if args.final_lr_scale is not None:
        env["COLONY_FINAL_LR_SCALE"] = str(args.final_lr_scale)
    if args.grad_clip_norm is not None:
        env["COLONY_GRAD_CLIP_NORM"] = str(args.grad_clip_norm)
    if args.enable_loss_jitter_trigger is not None:
        flag = str(args.enable_loss_jitter_trigger).strip().lower()
        env["COLONY_ENABLE_LOSS_JITTER_TRIGGER"] = (
            "1" if flag in {"1", "true", "yes", "on"} else "0"
        )
    if args.loss_jitter_window is not None:
        env["COLONY_LOSS_JITTER_WINDOW"] = str(args.loss_jitter_window)
    if args.loss_jitter_threshold is not None:
        env["COLONY_LOSS_JITTER_THRESHOLD"] = str(args.loss_jitter_threshold)
    if args.loss_jitter_patience is not None:
        env["COLONY_LOSS_JITTER_PATIENCE"] = str(args.loss_jitter_patience)
    if args.loss_jitter_boost is not None:
        env["COLONY_LOSS_JITTER_BOOST"] = str(args.loss_jitter_boost)
    if args.loss_jitter_boost_steps is not None:
        env["COLONY_LOSS_JITTER_BOOST_STEPS"] = str(args.loss_jitter_boost_steps)
    if args.export_topk_onnx is not None:
        flag = str(args.export_topk_onnx).strip().lower()
        env["COLONY_EXPORT_TOPK_ONNX"] = (
            "1" if flag in {"1", "true", "yes", "on"} else "0"
        )

    train_script = _resolve_train_script_path(
        args.train_script,
        c2net_code_path,
        code_name,
    )
    if not train_script.exists():
        raise SystemExit(f"MindSpore train script not found: {train_script}")

    _ensure_mindspore_runtime_dependencies()

    cmd = [sys.executable, str(train_script)]
    print("Running:", " ".join(cmd))
    print("COLONY_DATASET_ROOT=", env["COLONY_DATASET_ROOT"])
    print("COLONY_CHECKPOINT_DIR=", env["COLONY_CHECKPOINT_DIR"])
    print("COLONY_DEVICE=", env["COLONY_DEVICE"])
    print("EXTRACT_DIR=", str(extract_dir))
    if "COLONY_PREPROCESS_MODE" in env:
        print("COLONY_PREPROCESS_MODE=", env["COLONY_PREPROCESS_MODE"])
    if "COLONY_USE_AUGMENT" in env:
        print("COLONY_USE_AUGMENT=", env["COLONY_USE_AUGMENT"])
    if "COLONY_TOPK" in env:
        print("COLONY_TOPK=", env["COLONY_TOPK"])
    if "COLONY_MODEL_VARIANT" in env:
        print("COLONY_MODEL_VARIANT=", env["COLONY_MODEL_VARIANT"])
    if "COLONY_AUX_PRIOR_WEIGHT" in env:
        print("COLONY_AUX_PRIOR_WEIGHT=", env["COLONY_AUX_PRIOR_WEIGHT"])
    if "COLONY_LR_SCHEDULE" in env:
        print("COLONY_LR_SCHEDULE=", env["COLONY_LR_SCHEDULE"])
    if "COLONY_HEAD_ONLY_EPOCHS" in env:
        print("COLONY_HEAD_ONLY_EPOCHS=", env["COLONY_HEAD_ONLY_EPOCHS"])
    if "COLONY_LATE_UNFREEZE_EPOCH" in env:
        print("COLONY_LATE_UNFREEZE_EPOCH=", env["COLONY_LATE_UNFREEZE_EPOCH"])
    if "COLONY_ENABLE_LOSS_JITTER_TRIGGER" in env:
        print(
            "COLONY_ENABLE_LOSS_JITTER_TRIGGER=",
            env["COLONY_ENABLE_LOSS_JITTER_TRIGGER"],
        )
    if "COLONY_EXPORT_TOPK_ONNX" in env:
        print("COLONY_EXPORT_TOPK_ONNX=", env["COLONY_EXPORT_TOPK_ONNX"])
    sys.stdout.flush()

    proc = subprocess.run(cmd, env=env)
    return int(proc.returncode)


if __name__ == "__main__":
    raise SystemExit(main())
