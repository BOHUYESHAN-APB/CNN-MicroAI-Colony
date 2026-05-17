from __future__ import annotations

import json
import math
import os
import re
import shutil
import time
import threading
from pathlib import Path
from typing import Optional

import mindspore as ms
import mindspore.dataset as ds
import numpy as np
from PIL import Image
from mindspore import Tensor, nn, ops
from tqdm import tqdm


DEFAULT_DATASET_ROOT = Path(os.environ.get("COLONY_DATASET_ROOT", "/cache/dataset"))
DEFAULT_CHECKPOINT_DIR = Path(
    os.environ.get("COLONY_CHECKPOINT_DIR", "/cache/output/model")
)


def _env_int(name: str, default: int, min_value: int = 0) -> int:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        value = int(raw)
    except Exception:
        return default
    if value < min_value:
        return default
    return value


def _env_float(name: str, default: float, min_value: float = 0.0) -> float:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        value = float(raw)
    except Exception:
        return default
    if value < min_value:
        return default
    return value


def _env_flag(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name, "").strip().lower()
    if not raw:
        return default
    return raw in {"1", "true", "yes", "on"}


def _env_text(name: str, default: str) -> str:
    raw = os.environ.get(name, "")
    if not raw:
        return default
    return raw.strip()


def _resolve_device_target(preference: str) -> str:
    normalized = (preference or "auto").strip().lower()
    if normalized in {"npu", "ascend", "auto"}:
        return "Ascend"
    if normalized in {"cuda", "gpu"}:
        return "GPU"
    return "CPU"


def _format_seconds(total_seconds: float) -> str:
    seconds = max(0, int(total_seconds))
    hours, rem = divmod(seconds, 3600)
    minutes, secs = divmod(rem, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def _normalize_preprocess_mode(mode: str) -> str:
    normalized = (mode or "resize").strip().lower()
    if normalized in {"resize", "center_crop_resize"}:
        return normalized
    return "resize"


def _center_crop_square(image: Image.Image) -> Image.Image:
    width, height = image.size
    side = min(width, height)
    left = (width - side) // 2
    top = (height - side) // 2
    return image.crop((left, top, left + side, top + side))


def _start_stall_watchdog(
    timeout_seconds: int,
    progress: dict[str, object],
    stop_event: threading.Event,
    ckpt_dir: Path,
) -> None:
    if timeout_seconds <= 0:
        return

    check_interval = max(
        10, min(60, timeout_seconds // 12 if timeout_seconds > 0 else 30)
    )

    def _runner() -> None:
        while not stop_event.wait(check_interval):
            raw_progress_ts = progress.get("ts", time.time())
            if isinstance(raw_progress_ts, (int, float)):
                last_progress_ts = float(raw_progress_ts)
            else:
                last_progress_ts = time.time()
            idle_seconds = time.time() - last_progress_ts
            if idle_seconds <= timeout_seconds:
                continue

            stage = str(progress.get("stage", "unknown"))
            message = (
                "[watchdog] Detected training stall: "
                f"no progress for {idle_seconds:.1f}s (> {timeout_seconds}s), stage={stage}. "
                "Force exiting to avoid infinite hang."
            )
            print(message)

            report = {
                "status": "stalled",
                "stage": stage,
                "idle_seconds": idle_seconds,
                "timeout_seconds": timeout_seconds,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
            }
            try:
                (ckpt_dir / "mindspore_stall_report.json").write_text(
                    json.dumps(report, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
            except Exception:
                pass

            os._exit(124)

    thread = threading.Thread(
        target=_runner, name="mindspore-stall-watchdog", daemon=True
    )
    thread.start()


class CocoCountDataset:
    def __init__(
        self,
        image_root: Path,
        ann_file: Path,
        image_size: int,
        preprocess_mode: str = "resize",
        augment: bool = False,
    ) -> None:
        self.image_root = image_root
        self.image_size = image_size
        self.preprocess_mode = _normalize_preprocess_mode(preprocess_mode)
        self.augment = augment

        if not ann_file.exists():
            raise FileNotFoundError(f"Annotation file not found: {ann_file}")

        with ann_file.open("r", encoding="utf-8") as fp:
            coco = json.load(fp)

        images = {int(item["id"]): item for item in coco.get("images", [])}
        counts: dict[int, int] = {image_id: 0 for image_id in images}

        for ann in tqdm(coco.get("annotations", []), desc=f"Parsing {ann_file.name}"):
            image_id = int(ann.get("image_id", -1))
            bbox = ann.get("bbox", [0, 0, 0, 0])
            if image_id not in counts:
                continue
            if len(bbox) != 4:
                continue
            width = float(bbox[2])
            height = float(bbox[3])
            if width > 0 and height > 0:
                counts[image_id] += 1

        self._mean = np.array([0.485, 0.456, 0.406], dtype=np.float32).reshape(3, 1, 1)
        self._std = np.array([0.229, 0.224, 0.225], dtype=np.float32).reshape(3, 1, 1)
        self.samples: list[tuple[str, np.ndarray]] = []
        missing = 0

        for image_id, image_meta in images.items():
            file_name = image_meta.get("file_name")
            if not isinstance(file_name, str) or not file_name:
                continue
            image_path = image_root / file_name
            if not image_path.exists():
                missing += 1
                continue
            target_count = np.array([float(counts.get(image_id, 0))], dtype=np.float32)
            self.samples.append((str(image_path), target_count))

        if not self.samples:
            raise RuntimeError(f"No valid images found under {image_root}")

        print(
            f"Loaded {len(self.samples)} samples from {image_root} "
            f"(missing files ignored: {missing})"
        )

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, index: int) -> tuple[np.ndarray, np.ndarray]:
        image_path, target_count = self.samples[index]
        bilinear_mode = getattr(getattr(Image, "Resampling", Image), "BILINEAR")
        transpose_mode = getattr(Image, "Transpose", Image)
        flip_left_right = getattr(transpose_mode, "FLIP_LEFT_RIGHT")
        flip_top_bottom = getattr(transpose_mode, "FLIP_TOP_BOTTOM")
        image = Image.open(image_path).convert("RGB")

        if self.preprocess_mode == "center_crop_resize":
            image = _center_crop_square(image)

        if self.augment:
            if float(np.random.rand()) < 0.5:
                image = image.transpose(flip_left_right)
            if float(np.random.rand()) < 0.2:
                image = image.transpose(flip_top_bottom)

        image = image.resize((self.image_size, self.image_size), bilinear_mode)

        arr = np.asarray(image, dtype=np.float32) / 255.0
        arr = np.transpose(arr, (2, 0, 1))
        arr = (arr - self._mean) / self._std
        return arr.astype(np.float32), target_count.astype(np.float32)


class ColonyCountNet(nn.Cell):
    def __init__(self) -> None:
        super().__init__()
        self.features = nn.SequentialCell(
            [
                nn.Conv2d(3, 32, kernel_size=3, stride=1, pad_mode="pad", padding=1),
                nn.ReLU(),
                nn.MaxPool2d(kernel_size=2, stride=2),
                nn.Conv2d(32, 64, kernel_size=3, stride=1, pad_mode="pad", padding=1),
                nn.ReLU(),
                nn.MaxPool2d(kernel_size=2, stride=2),
                nn.Conv2d(64, 128, kernel_size=3, stride=1, pad_mode="pad", padding=1),
                nn.ReLU(),
                nn.MaxPool2d(kernel_size=2, stride=2),
                nn.Conv2d(128, 256, kernel_size=3, stride=1, pad_mode="pad", padding=1),
                nn.ReLU(),
            ]
        )
        self.head = nn.SequentialCell(
            [
                nn.Dense(256, 128),
                nn.ReLU(),
                nn.Dense(128, 1),
            ]
        )

    def construct(self, x: Tensor) -> Tensor:
        x = self.features(x)
        x = ops.mean(x, axis=(2, 3))
        return self.head(x)


class DepthwiseResidualBlock(nn.Cell):
    def __init__(self, in_channels: int, out_channels: int) -> None:
        super().__init__()
        self.depthwise = nn.Conv2d(
            in_channels,
            in_channels,
            kernel_size=3,
            stride=1,
            pad_mode="pad",
            padding=1,
            group=in_channels,
        )
        self.pointwise = nn.Conv2d(
            in_channels, out_channels, kernel_size=1, stride=1, pad_mode="valid"
        )
        self.act = nn.ReLU()
        self.proj = (
            nn.Conv2d(
                in_channels, out_channels, kernel_size=1, stride=1, pad_mode="valid"
            )
            if in_channels != out_channels
            else None
        )

    def construct(self, x: Tensor) -> Tensor:
        residual = x if self.proj is None else self.proj(x)
        out = self.depthwise(x)
        out = self.pointwise(out)
        out = self.act(out)
        return self.act(out + residual)


class ColonyCountNetMorphV2(nn.Cell):
    def __init__(self, fusion_alpha: float = 0.25) -> None:
        super().__init__()
        self.fusion_alpha = float(max(0.0, fusion_alpha))
        self.features = nn.SequentialCell(
            [
                nn.Conv2d(3, 32, kernel_size=3, stride=1, pad_mode="pad", padding=1),
                nn.ReLU(),
                DepthwiseResidualBlock(32, 32),
                nn.MaxPool2d(kernel_size=2, stride=2),
                DepthwiseResidualBlock(32, 64),
                nn.MaxPool2d(kernel_size=2, stride=2),
                DepthwiseResidualBlock(64, 128),
                nn.MaxPool2d(kernel_size=2, stride=2),
                DepthwiseResidualBlock(128, 256),
            ]
        )
        self.head = nn.SequentialCell(
            [
                nn.Dense(256, 160),
                nn.ReLU(),
                nn.Dense(160, 1),
            ]
        )
        self.prior_head = nn.SequentialCell(
            [
                nn.Conv2d(3, 16, kernel_size=3, stride=1, pad_mode="pad", padding=1),
                nn.ReLU(),
                nn.Conv2d(16, 16, kernel_size=3, stride=1, pad_mode="pad", padding=1),
                nn.ReLU(),
                nn.Conv2d(16, 1, kernel_size=1, stride=1, pad_mode="valid"),
            ]
        )
        self.prior_pool = nn.AvgPool2d(kernel_size=8, stride=8)

    def _encode(self, x: Tensor) -> tuple[Tensor, Tensor]:
        prior_logits = self.prior_head(x)
        gate = ops.sigmoid(self.prior_pool(prior_logits))
        features = self.features(x)
        features = features * (1.0 + gate * self.fusion_alpha)
        return features, prior_logits

    def forward_with_aux(self, x: Tensor) -> tuple[Tensor, Tensor]:
        features, prior_logits = self._encode(x)
        pooled = ops.mean(features, axis=(2, 3))
        return self.head(pooled), prior_logits

    def construct(self, x: Tensor) -> Tensor:
        count, _ = self.forward_with_aux(x)
        return count


def _build_input_morph_prior(images: Tensor) -> Tensor:
    gray = (
        images[:, 0:1, :, :] * 0.2989
        + images[:, 1:2, :, :] * 0.5870
        + images[:, 2:3, :, :] * 0.1140
    )
    dx = ops.abs(gray[:, :, :, 1:] - gray[:, :, :, :-1])
    dy = ops.abs(gray[:, :, 1:, :] - gray[:, :, :-1, :])
    zeros_x = ops.zeros_like(gray[:, :, :, :1])
    zeros_y = ops.zeros_like(gray[:, :, :1, :])
    dx = ops.concat((dx, zeros_x), axis=3)
    dy = ops.concat((dy, zeros_y), axis=2)
    edge = dx + dy
    reduce_max = ops.ReduceMax(keep_dims=True)
    edge_max = reduce_max(edge, (2, 3))
    edge = edge / ops.maximum(edge_max, Tensor(1e-6, dtype=edge.dtype))
    return ops.stop_gradient(edge)


def _checkpoint_epoch_key(path: Path) -> tuple[int, str]:
    match = re.search(r"epoch(\d+)", path.stem)
    if match:
        return int(match.group(1)), path.name
    return -1, path.name


def _parameter_group_name(param_name: str) -> str:
    if param_name.startswith("head."):
        return "head"
    if param_name.startswith("features."):
        parts = param_name.split(".")
        if len(parts) >= 2:
            try:
                layer_idx = int(parts[1])
            except ValueError:
                layer_idx = -1
            if layer_idx in {0, 3}:
                return "features_early"
            if layer_idx in {6, 9}:
                return "features_late"
    return "head"


def _schedule_boundaries(num_epochs: int) -> tuple[int, int, int, int]:
    stage1 = max(1, int(round(num_epochs * 0.10)))
    stage2 = max(stage1 + 1, int(round(num_epochs * 0.30)))
    stage3 = max(stage2 + 1, int(round(num_epochs * 0.70)))
    stage4 = max(stage3 + 1, int(round(num_epochs * 0.90)))
    stage4 = min(stage4, num_epochs)
    return stage1, min(stage2, num_epochs), min(stage3, num_epochs), stage4


def _linear_interp(start: float, end: float, progress: float) -> float:
    bounded = max(0.0, min(1.0, progress))
    return start + (end - start) * bounded


def _cyclical_linear(progress: float, cycles: int = 4) -> float:
    bounded = max(0.0, min(1.0, progress))
    if cycles <= 0:
        return bounded
    position = bounded * float(cycles)
    fraction = position - math.floor(position)
    phase = int(math.floor(position))
    if phase % 2 == 0:
        return fraction
    return 1.0 - fraction


def _base_lr_scale_for_epoch(
    epoch: int,
    num_epochs: int,
    schedule_name: str,
    dynamic_lr_min_scale: float,
    dynamic_lr_max_scale: float,
    final_lr_scale: float,
) -> float:
    if schedule_name == "constant":
        return 1.0

    stage1, stage2, stage3, stage4 = _schedule_boundaries(num_epochs)
    if epoch <= stage1:
        return 1.0
    if epoch <= stage2:
        progress = (epoch - stage1) / max(1, stage2 - stage1)
        return _linear_interp(1.0, 0.30, progress)
    if epoch <= stage3:
        progress = (epoch - stage2) / max(1, stage3 - stage2)
        return _linear_interp(
            dynamic_lr_min_scale,
            dynamic_lr_max_scale,
            _cyclical_linear(progress, cycles=4),
        )
    if epoch <= stage4:
        progress = (epoch - stage3) / max(1, stage4 - stage3)
        return _linear_interp(dynamic_lr_min_scale, 0.10, progress)
    progress = (epoch - stage4) / max(1, num_epochs - stage4)
    return _linear_interp(0.10, final_lr_scale, progress)


def _group_activation_scales(
    epoch: int,
    head_only_epochs: int,
    late_unfreeze_epoch: int,
) -> dict[str, float]:
    if epoch <= head_only_epochs:
        return {
            "features_early": 0.0,
            "features_late": 0.0,
            "head": 1.0,
        }
    if epoch <= late_unfreeze_epoch:
        return {
            "features_early": 0.0,
            "features_late": 1.0,
            "head": 1.0,
        }
    return {
        "features_early": 1.0,
        "features_late": 1.0,
        "head": 1.0,
    }


def _build_epoch_scale_config(
    epoch: int,
    num_epochs: int,
    schedule_name: str,
    head_only_epochs: int,
    late_unfreeze_epoch: int,
    early_feature_lr_scale: float,
    late_feature_lr_scale: float,
    head_lr_scale: float,
    dynamic_lr_min_scale: float,
    dynamic_lr_max_scale: float,
    final_lr_scale: float,
) -> dict[str, float]:
    base_scale = _base_lr_scale_for_epoch(
        epoch,
        num_epochs,
        schedule_name,
        dynamic_lr_min_scale,
        dynamic_lr_max_scale,
        final_lr_scale,
    )
    activation_scales = _group_activation_scales(
        epoch,
        head_only_epochs,
        late_unfreeze_epoch,
    )
    return {
        "features_early": base_scale
        * early_feature_lr_scale
        * activation_scales["features_early"],
        "features_late": base_scale
        * late_feature_lr_scale
        * activation_scales["features_late"],
        "head": base_scale * head_lr_scale * activation_scales["head"],
        "base_scale": base_scale,
    }


def _build_param_scale_tensors(
    params: list[ms.Parameter],
    group_scales: dict[str, float],
) -> tuple[Tensor, ...]:
    tensors: list[Tensor] = []
    for param in params:
        group_name = _parameter_group_name(param.name)
        scale = float(group_scales.get(group_name, group_scales["head"]))
        tensors.append(Tensor(scale, dtype=param.dtype))
    return tuple(tensors)


def _build_layerwise_lr_tensor(
    group_name: str,
    steps_per_epoch: int,
    num_epochs: int,
    learning_rate: float,
    schedule_name: str,
    head_only_epochs: int,
    late_unfreeze_epoch: int,
    early_feature_lr_scale: float,
    late_feature_lr_scale: float,
    head_lr_scale: float,
    dynamic_lr_min_scale: float,
    dynamic_lr_max_scale: float,
    final_lr_scale: float,
) -> Tensor:
    schedule: list[float] = []
    for epoch in range(1, num_epochs + 1):
        epoch_scale_config = _build_epoch_scale_config(
            epoch=epoch,
            num_epochs=num_epochs,
            schedule_name=schedule_name,
            head_only_epochs=head_only_epochs,
            late_unfreeze_epoch=late_unfreeze_epoch,
            early_feature_lr_scale=early_feature_lr_scale,
            late_feature_lr_scale=late_feature_lr_scale,
            head_lr_scale=head_lr_scale,
            dynamic_lr_min_scale=dynamic_lr_min_scale,
            dynamic_lr_max_scale=dynamic_lr_max_scale,
            final_lr_scale=final_lr_scale,
        )
        epoch_lr = learning_rate * float(epoch_scale_config[group_name])
        schedule.extend([epoch_lr] * steps_per_epoch)
    return Tensor(np.asarray(schedule, dtype=np.float32))


def _build_optimizer_group_params(
    model: nn.Cell,
    steps_per_epoch: int,
    num_epochs: int,
    learning_rate: float,
    weight_decay: float,
    schedule_name: str,
    head_only_epochs: int,
    late_unfreeze_epoch: int,
    early_feature_lr_scale: float,
    late_feature_lr_scale: float,
    head_lr_scale: float,
    dynamic_lr_min_scale: float,
    dynamic_lr_max_scale: float,
    final_lr_scale: float,
) -> list[dict[str, object]]:
    grouped_params: dict[str, list[ms.Parameter]] = {
        "features_early": [],
        "features_late": [],
        "head": [],
    }
    ordered_params = list(model.trainable_params())
    for param in ordered_params:
        grouped_params[_parameter_group_name(param.name)].append(param)

    group_params: list[dict[str, object]] = []
    for group_name in ("features_early", "features_late", "head"):
        params = grouped_params[group_name]
        if not params:
            continue
        group_params.append(
            {
                "params": params,
                "lr": _build_layerwise_lr_tensor(
                    group_name=group_name,
                    steps_per_epoch=steps_per_epoch,
                    num_epochs=num_epochs,
                    learning_rate=learning_rate,
                    schedule_name=schedule_name,
                    head_only_epochs=head_only_epochs,
                    late_unfreeze_epoch=late_unfreeze_epoch,
                    early_feature_lr_scale=early_feature_lr_scale,
                    late_feature_lr_scale=late_feature_lr_scale,
                    head_lr_scale=head_lr_scale,
                    dynamic_lr_min_scale=dynamic_lr_min_scale,
                    dynamic_lr_max_scale=dynamic_lr_max_scale,
                    final_lr_scale=final_lr_scale,
                ),
                "weight_decay": weight_decay,
            }
        )

    group_params.append({"order_params": ordered_params})
    return group_params


def _apply_gradient_controls(
    grads: tuple[Tensor, ...],
    param_scale_tensors: tuple[Tensor, ...],
    clip_norm: float,
) -> tuple[Tensor, ...]:
    scaled = tuple(
        ops.mul(grad, scale) for grad, scale in zip(grads, param_scale_tensors)
    )
    if clip_norm > 0:
        clipped = ops.clip_by_global_norm(scaled, clip_norm)
        return tuple(clipped)
    return scaled


def _item_epoch_value(item: dict[str, object]) -> int:
    value = item.get("epoch", 0)
    if isinstance(value, (int, float)):
        return int(value)
    return 0


def _item_rmse_value(item: dict[str, object]) -> float:
    value = item.get("rmse", 0.0)
    if isinstance(value, (int, float)):
        return float(value)
    return 0.0


def _build_dataset(
    source: CocoCountDataset,
    batch_size: int,
    num_workers: int,
    shuffle: bool,
) -> ds.Dataset:
    workers = max(1, min(16, num_workers))
    dataset = ds.GeneratorDataset(
        source=source,
        column_names=["image", "label"],
        shuffle=shuffle,
        num_parallel_workers=workers,
    )
    dataset = dataset.batch(batch_size=batch_size, drop_remainder=False)
    return dataset


def _evaluate(model: nn.Cell, dataset: ds.Dataset) -> tuple[float, float]:
    model.set_train(False)
    mae_sum = 0.0
    mse_sum = 0.0
    num_samples = 0

    for images, labels in dataset.create_tuple_iterator(num_epochs=1):
        preds = model(images)
        diff = preds - labels
        mae_sum += float(ops.abs(diff).sum().asnumpy())
        mse_sum += float(ops.square(diff).sum().asnumpy())
        num_samples += int(labels.shape[0])

    if num_samples == 0:
        return float("inf"), float("inf")

    mae = mae_sum / num_samples
    rmse = math.sqrt(mse_sum / num_samples)
    return mae, rmse


def _latest_checkpoint(ckpt_dir: Path) -> Optional[Path]:
    ckpts = sorted(
        ckpt_dir.glob("mindspore_colony_epoch*.ckpt"), key=_checkpoint_epoch_key
    )
    if not ckpts:
        return None
    return ckpts[-1]


def _pick_existing(paths: list[Path]) -> Optional[Path]:
    for path in paths:
        if path.exists() and path.is_file():
            return path
    return None


def _annotation_candidates(split_root: Path, split: str) -> list[Path]:
    split_name = split.lower().strip()
    return [
        split_root / "_annotations.coco.json",
        split_root / "annotations" / f"instances_{split_name}.json",
        split_root / "annotations" / f"instances_{split_name}2017.json",
    ]


def _image_root_candidates(split_root: Path) -> list[Path]:
    return [
        split_root,
        split_root / "images",
        split_root / "JPEGImages",
    ]


def _score_image_root(image_root: Path, ann_file: Path) -> int:
    try:
        with ann_file.open("r", encoding="utf-8") as fp:
            coco = json.load(fp)
    except Exception:
        return -1

    images = coco.get("images", [])
    if not isinstance(images, list) or not images:
        return 0

    score = 0
    limit = min(128, len(images))
    for item in images[:limit]:
        if not isinstance(item, dict):
            continue
        file_name = item.get("file_name")
        if not isinstance(file_name, str) or not file_name:
            continue
        if (image_root / file_name).exists():
            score += 1
    return score


def _resolve_split_layout(dataset_root: Path, split: str) -> tuple[Path, Path]:
    split_root = dataset_root / split
    ann_candidates = _annotation_candidates(split_root, split)
    ann_file = _pick_existing(ann_candidates)
    if ann_file is None:
        expected = "\n  ".join(str(p) for p in ann_candidates)
        raise FileNotFoundError(
            f"Missing COCO annotation for split '{split}'. Tried:\n  {expected}"
        )

    image_roots = [
        p for p in _image_root_candidates(split_root) if p.exists() and p.is_dir()
    ]
    if not image_roots:
        raise FileNotFoundError(
            f"No image root directory found under split: {split_root}"
        )

    best_root = image_roots[0]
    best_score = -1
    for candidate in image_roots:
        score = _score_image_root(candidate, ann_file)
        if score > best_score:
            best_score = score
            best_root = candidate

    return best_root, ann_file


def main() -> int:
    dataset_root = DEFAULT_DATASET_ROOT
    ckpt_dir = DEFAULT_CHECKPOINT_DIR
    ckpt_dir.mkdir(parents=True, exist_ok=True)

    preference = os.environ.get("COLONY_DEVICE", "npu")
    device_target = _resolve_device_target(preference)
    ms.set_context(mode=ms.PYNATIVE_MODE, device_target=device_target)

    image_size = _env_int("COLONY_IMAGE_SIZE", 384, min_value=128)
    num_epochs = _env_int("COLONY_NUM_EPOCHS", 40, min_value=1)
    batch_size = _env_int("COLONY_BATCH_SIZE", 8, min_value=1)
    num_workers = _env_int("COLONY_NUM_WORKERS", 4, min_value=1)
    valid_num_workers = _env_int("COLONY_VALID_NUM_WORKERS", 1, min_value=1)
    learning_rate = _env_float("COLONY_LR", 1e-3, min_value=1e-6)
    weight_decay = _env_float("COLONY_WEIGHT_DECAY", 1e-4, min_value=0.0)
    lr_schedule = _env_text("COLONY_LR_SCHEDULE", "constant").strip().lower()
    if lr_schedule not in {"constant", "staged_dynamic"}:
        lr_schedule = "constant"
    log_interval = _env_int("COLONY_LOG_INTERVAL_STEPS", 20, min_value=1)
    max_steps_per_epoch = _env_int("COLONY_MAX_STEPS_PER_EPOCH", 0, min_value=0)
    stop_after_first_epoch = _env_flag("COLONY_STOP_AFTER_FIRST_EPOCH", False)
    stall_timeout_seconds = _env_int("COLONY_STALL_TIMEOUT_SECONDS", 1800, min_value=0)
    preprocess_mode = _normalize_preprocess_mode(
        os.environ.get("COLONY_PREPROCESS_MODE", "center_crop_resize")
    )
    use_augment = _env_flag("COLONY_USE_AUGMENT", True)
    topk = _env_int("COLONY_TOPK", 3, min_value=1)
    export_topk_onnx = _env_flag("COLONY_EXPORT_TOPK_ONNX", True)
    model_variant = _env_text("COLONY_MODEL_VARIANT", "baseline").strip().lower()
    if model_variant not in {"baseline", "morph_v2"}:
        model_variant = "baseline"
    aux_prior_weight = _env_float("COLONY_AUX_PRIOR_WEIGHT", 0.15, min_value=0.0)
    early_feature_lr_scale = _env_float(
        "COLONY_EARLY_FEATURE_LR_SCALE", 0.10, min_value=0.0
    )
    late_feature_lr_scale = _env_float(
        "COLONY_LATE_FEATURE_LR_SCALE", 0.30, min_value=0.0
    )
    head_lr_scale = _env_float("COLONY_HEAD_LR_SCALE", 1.0, min_value=0.0)
    head_only_epochs = _env_int("COLONY_HEAD_ONLY_EPOCHS", 20, min_value=0)
    late_unfreeze_epoch = _env_int("COLONY_LATE_UNFREEZE_EPOCH", 120, min_value=0)
    if late_unfreeze_epoch < head_only_epochs:
        late_unfreeze_epoch = head_only_epochs
    dynamic_lr_min_scale = _env_float(
        "COLONY_DYNAMIC_LR_MIN_SCALE", 0.12, min_value=1e-6
    )
    dynamic_lr_max_scale = _env_float(
        "COLONY_DYNAMIC_LR_MAX_SCALE", 0.30, min_value=1e-6
    )
    if dynamic_lr_max_scale < dynamic_lr_min_scale:
        dynamic_lr_max_scale = dynamic_lr_min_scale
    final_lr_scale = _env_float("COLONY_FINAL_LR_SCALE", 0.02, min_value=1e-6)
    grad_clip_norm = _env_float("COLONY_GRAD_CLIP_NORM", 0.0, min_value=0.0)
    enable_loss_jitter_trigger = _env_flag("COLONY_ENABLE_LOSS_JITTER_TRIGGER", False)
    loss_jitter_window = _env_int("COLONY_LOSS_JITTER_WINDOW", 10, min_value=3)
    loss_jitter_threshold = _env_float(
        "COLONY_LOSS_JITTER_THRESHOLD", 0.15, min_value=0.0
    )
    loss_jitter_patience = _env_int("COLONY_LOSS_JITTER_PATIENCE", 3, min_value=1)
    loss_jitter_boost = _env_float("COLONY_LOSS_JITTER_BOOST", 1.20, min_value=1.0)
    loss_jitter_boost_steps = _env_int(
        "COLONY_LOSS_JITTER_BOOST_STEPS", 12, min_value=1
    )

    if device_target == "Ascend" and num_workers > 4:
        print(
            f"COLONY_NUM_WORKERS={num_workers} is too high for stable Ascend long runs; capping to 4."
        )
        num_workers = 4
    if device_target == "Ascend" and valid_num_workers > 2:
        print(
            f"COLONY_VALID_NUM_WORKERS={valid_num_workers} is too high for stable Ascend validation; capping to 2."
        )
        valid_num_workers = 2

    train_root, train_ann = _resolve_split_layout(dataset_root, "train")
    valid_root, valid_ann = _resolve_split_layout(dataset_root, "valid")

    print("MindSpore version:", ms.__version__)
    print("Device target:", device_target)
    print("COLONY_DATASET_ROOT=", str(dataset_root))
    print("COLONY_CHECKPOINT_DIR=", str(ckpt_dir))
    print(
        "Hparams: "
        f"epochs={num_epochs}, batch_size={batch_size}, image_size={image_size}, "
        f"lr={learning_rate}, weight_decay={weight_decay}, "
        f"lr_schedule={lr_schedule}, early_feature_lr_scale={early_feature_lr_scale}, "
        f"late_feature_lr_scale={late_feature_lr_scale}, head_lr_scale={head_lr_scale}, "
        f"head_only_epochs={head_only_epochs}, late_unfreeze_epoch={late_unfreeze_epoch}, "
        f"dynamic_lr_min_scale={dynamic_lr_min_scale}, dynamic_lr_max_scale={dynamic_lr_max_scale}, "
        f"final_lr_scale={final_lr_scale}, grad_clip_norm={grad_clip_norm}, "
        f"enable_loss_jitter_trigger={enable_loss_jitter_trigger}, "
        f"workers(train)={num_workers}, workers(valid)={valid_num_workers}, "
        f"stall_timeout_seconds={stall_timeout_seconds}, preprocess_mode={preprocess_mode}, "
        f"use_augment={use_augment}, topk={topk}, export_topk_onnx={export_topk_onnx}, "
        f"model_variant={model_variant}, aux_prior_weight={aux_prior_weight}"
    )

    print("Resolved train image root:", str(train_root))
    print("Resolved train annotation:", str(train_ann))
    print("Resolved valid image root:", str(valid_root))
    print("Resolved valid annotation:", str(valid_ann))

    train_source = CocoCountDataset(
        train_root,
        train_ann,
        image_size=image_size,
        preprocess_mode=preprocess_mode,
        augment=use_augment,
    )
    valid_source = CocoCountDataset(
        valid_root,
        valid_ann,
        image_size=image_size,
        preprocess_mode=preprocess_mode,
        augment=False,
    )

    train_ds = _build_dataset(train_source, batch_size, num_workers, shuffle=True)
    valid_ds = _build_dataset(
        valid_source, batch_size, valid_num_workers, shuffle=False
    )

    steps_per_epoch = train_ds.get_dataset_size()
    print("steps_per_epoch=", steps_per_epoch)

    if model_variant == "morph_v2":
        model = ColonyCountNetMorphV2()
    else:
        model = ColonyCountNet()
    latest = _latest_checkpoint(ckpt_dir)
    if latest is not None:
        print("Resuming from checkpoint:", str(latest))
        params = ms.load_checkpoint(str(latest))
        ms.load_param_into_net(model, params)

    loss_fn = nn.MSELoss()
    optimizer = nn.Adam(
        params=_build_optimizer_group_params(
            model=model,
            steps_per_epoch=steps_per_epoch,
            num_epochs=num_epochs,
            learning_rate=learning_rate,
            weight_decay=weight_decay,
            schedule_name=lr_schedule,
            head_only_epochs=head_only_epochs,
            late_unfreeze_epoch=late_unfreeze_epoch,
            early_feature_lr_scale=early_feature_lr_scale,
            late_feature_lr_scale=late_feature_lr_scale,
            head_lr_scale=head_lr_scale,
            dynamic_lr_min_scale=dynamic_lr_min_scale,
            dynamic_lr_max_scale=dynamic_lr_max_scale,
            final_lr_scale=final_lr_scale,
        ),
        learning_rate=learning_rate,
        weight_decay=weight_decay,
    )
    optimizer_params = list(optimizer.parameters)
    epoch_scale_config = _build_epoch_scale_config(
        epoch=1,
        num_epochs=num_epochs,
        schedule_name=lr_schedule,
        head_only_epochs=head_only_epochs,
        late_unfreeze_epoch=late_unfreeze_epoch,
        early_feature_lr_scale=early_feature_lr_scale,
        late_feature_lr_scale=late_feature_lr_scale,
        head_lr_scale=head_lr_scale,
        dynamic_lr_min_scale=dynamic_lr_min_scale,
        dynamic_lr_max_scale=dynamic_lr_max_scale,
        final_lr_scale=final_lr_scale,
    )
    neutral_scale_config = {
        "features_early": 1.0,
        "features_late": 1.0,
        "head": 1.0,
    }
    param_scale_tensors = _build_param_scale_tensors(
        optimizer_params, neutral_scale_config
    )
    loss_window: list[float] = []
    jitter_hits = 0
    jitter_boost_remaining = 0
    jitter_trigger_count = 0
    last_prior_loss = 0.0

    def forward_fn(images: Tensor, labels: Tensor):
        if model_variant == "morph_v2" and isinstance(model, ColonyCountNetMorphV2):
            preds, prior_logits = model.forward_with_aux(images)
            count_loss = loss_fn(preds, labels)
            prior_target = _build_input_morph_prior(images)
            prior_prob = ops.sigmoid(prior_logits)
            prior_loss = ops.mean(ops.square(prior_prob - prior_target))
            total_loss = count_loss + (aux_prior_weight * prior_loss)
            return total_loss, preds, count_loss, prior_loss

        preds = model(images)
        count_loss = loss_fn(preds, labels)
        zero_prior = Tensor(0.0, dtype=count_loss.dtype)
        return count_loss, preds, count_loss, zero_prior

    grad_fn = ms.value_and_grad(forward_fn, None, optimizer.parameters, has_aux=True)

    def train_step(
        images: Tensor, labels: Tensor
    ) -> tuple[Tensor, Tensor, Tensor, Tensor]:
        nonlocal param_scale_tensors
        (loss, preds, count_loss, prior_loss), grads = grad_fn(images, labels)
        grads = _apply_gradient_controls(grads, param_scale_tensors, grad_clip_norm)
        loss = ops.depend(loss, optimizer(grads))
        return loss, preds, count_loss, prior_loss

    best_rmse = float("inf")
    topk_items: list[dict[str, object]] = []
    train_start = time.time()
    progress: dict[str, object] = {"ts": time.time(), "stage": "startup"}
    watchdog_stop = threading.Event()
    _start_stall_watchdog(stall_timeout_seconds, progress, watchdog_stop, ckpt_dir)

    try:
        for epoch in range(1, num_epochs + 1):
            progress["ts"] = time.time()
            progress["stage"] = f"epoch_{epoch}_start"
            epoch_scale_config = _build_epoch_scale_config(
                epoch=epoch,
                num_epochs=num_epochs,
                schedule_name=lr_schedule,
                head_only_epochs=head_only_epochs,
                late_unfreeze_epoch=late_unfreeze_epoch,
                early_feature_lr_scale=early_feature_lr_scale,
                late_feature_lr_scale=late_feature_lr_scale,
                head_lr_scale=head_lr_scale,
                dynamic_lr_min_scale=dynamic_lr_min_scale,
                dynamic_lr_max_scale=dynamic_lr_max_scale,
                final_lr_scale=final_lr_scale,
            )
            print(
                "[schedule] "
                f"epoch={epoch}/{num_epochs} base_scale={epoch_scale_config['base_scale']:.6f} "
                f"features_early={epoch_scale_config['features_early']:.6f} "
                f"features_late={epoch_scale_config['features_late']:.6f} "
                f"head={epoch_scale_config['head']:.6f}"
            )

            model.set_train(True)
            epoch_loss_sum = 0.0
            epoch_count_loss_sum = 0.0
            epoch_prior_loss_sum = 0.0
            epoch_samples = 0
            iter_ms_sum = 0.0
            iter_count = 0
            epoch_start = time.time()

            iterator = train_ds.create_tuple_iterator(num_epochs=1)
            for step, (images, labels) in enumerate(iterator, start=1):
                progress["ts"] = time.time()
                progress["stage"] = f"epoch_{epoch}_train_step_{step}"

                t0 = time.perf_counter()
                loss, _, count_loss_tensor, prior_loss_tensor = train_step(
                    images, labels
                )
                iter_ms = (time.perf_counter() - t0) * 1000.0
                loss_value = float(loss.asnumpy())
                count_loss_value = float(count_loss_tensor.asnumpy())
                prior_loss_value = float(prior_loss_tensor.asnumpy())

                if enable_loss_jitter_trigger and epoch_scale_config["base_scale"] > 0:
                    if jitter_boost_remaining > 0:
                        jitter_boost_remaining -= 1
                    if len(loss_window) >= loss_jitter_window:
                        mean_loss = sum(loss_window[-loss_jitter_window:]) / float(
                            loss_jitter_window
                        )
                        deviation = abs(loss_value - mean_loss) / max(
                            1e-8, abs(mean_loss)
                        )
                        if deviation > loss_jitter_threshold:
                            jitter_hits += 1
                        else:
                            jitter_hits = 0
                        stage1, stage2, stage3, _ = _schedule_boundaries(num_epochs)
                        in_dynamic_stage = stage2 < epoch <= stage3
                        if (
                            in_dynamic_stage
                            and jitter_hits >= loss_jitter_patience
                            and jitter_boost_remaining <= 0
                        ):
                            jitter_boost_remaining = loss_jitter_boost_steps
                            jitter_trigger_count += 1
                            jitter_hits = 0
                            boosted_scale_config = dict(neutral_scale_config)
                            boosted_scale_config["head"] = loss_jitter_boost
                            param_scale_tensors = _build_param_scale_tensors(
                                optimizer_params, boosted_scale_config
                            )
                            print(
                                "[jitter] "
                                f"epoch={epoch} step={step} trigger_count={jitter_trigger_count} "
                                f"boost_steps={loss_jitter_boost_steps} head_scale={boosted_scale_config['head']:.6f}"
                            )
                        elif jitter_boost_remaining <= 0:
                            param_scale_tensors = _build_param_scale_tensors(
                                optimizer_params, neutral_scale_config
                            )
                    loss_window.append(loss_value)
                    if len(loss_window) > loss_jitter_window:
                        loss_window = loss_window[-loss_jitter_window:]

                batch_count = int(labels.shape[0])
                epoch_samples += batch_count
                epoch_loss_sum += loss_value * batch_count
                epoch_count_loss_sum += count_loss_value * batch_count
                epoch_prior_loss_sum += prior_loss_value * batch_count
                iter_ms_sum += iter_ms
                iter_count += 1

                if step % log_interval == 0:
                    avg_iter_ms = iter_ms_sum / max(1, iter_count)
                    samples_per_sec = (
                        (batch_size * 1000.0 / avg_iter_ms) if avg_iter_ms > 0 else 0.0
                    )
                    print(
                        "[train] "
                        f"epoch={epoch}/{num_epochs} step={step}/{steps_per_epoch} "
                        f"loss={loss_value:.6f} count_loss={count_loss_value:.6f} prior_loss={prior_loss_value:.6f} iter_ms={iter_ms:.2f} "
                        f"avg_iter_ms={avg_iter_ms:.2f} samples_per_sec={samples_per_sec:.2f}"
                    )

                if max_steps_per_epoch > 0 and step >= max_steps_per_epoch:
                    print(
                        f"Reached max_steps_per_epoch={max_steps_per_epoch}, "
                        "ending this epoch early."
                    )
                    break

            train_loss = epoch_loss_sum / max(1, epoch_samples)
            train_count_loss = epoch_count_loss_sum / max(1, epoch_samples)
            train_prior_loss = epoch_prior_loss_sum / max(1, epoch_samples)
            last_prior_loss = train_prior_loss
            progress["ts"] = time.time()
            progress["stage"] = f"epoch_{epoch}_evaluate"
            valid_mae, valid_rmse = _evaluate(model, valid_ds)
            epoch_seconds = time.time() - epoch_start
            elapsed_seconds = time.time() - train_start
            remaining_epochs = max(0, num_epochs - epoch)
            eta_seconds = epoch_seconds * remaining_epochs

            print(
                "[epoch] "
                f"{epoch}/{num_epochs} train_loss={train_loss:.6f} train_count_loss={train_count_loss:.6f} train_prior_loss={train_prior_loss:.6f} "
                f"valid_mae={valid_mae:.6f} valid_rmse={valid_rmse:.6f} "
                f"epoch_time={_format_seconds(epoch_seconds)} "
                f"elapsed={_format_seconds(elapsed_seconds)} "
                f"eta={_format_seconds(eta_seconds)}"
            )

            progress["ts"] = time.time()
            progress["stage"] = f"epoch_{epoch}_save_checkpoint"
            ckpt_path = ckpt_dir / f"mindspore_colony_epoch{epoch}.ckpt"
            ms.save_checkpoint(model, str(ckpt_path))
            print("Saved checkpoint:", str(ckpt_path))

            if valid_rmse < best_rmse:
                best_rmse = valid_rmse
                best_path = ckpt_dir / "mindspore_colony_best.ckpt"
                ms.save_checkpoint(model, str(best_path))
                print("Updated best checkpoint:", str(best_path))

            summary = {
                "epoch": epoch,
                "num_epochs": num_epochs,
                "train_loss": train_loss,
                "train_count_loss": train_count_loss,
                "train_prior_loss": train_prior_loss,
                "valid_mae": valid_mae,
                "valid_rmse": valid_rmse,
                "best_rmse": best_rmse,
                "device_target": device_target,
                "batch_size": batch_size,
                "learning_rate": learning_rate,
                "lr_schedule": lr_schedule,
                "early_feature_lr_scale": early_feature_lr_scale,
                "late_feature_lr_scale": late_feature_lr_scale,
                "head_lr_scale": head_lr_scale,
                "head_only_epochs": head_only_epochs,
                "late_unfreeze_epoch": late_unfreeze_epoch,
                "dynamic_lr_min_scale": dynamic_lr_min_scale,
                "dynamic_lr_max_scale": dynamic_lr_max_scale,
                "final_lr_scale": final_lr_scale,
                "grad_clip_norm": grad_clip_norm,
                "enable_loss_jitter_trigger": enable_loss_jitter_trigger,
                "loss_jitter_window": loss_jitter_window,
                "loss_jitter_threshold": loss_jitter_threshold,
                "loss_jitter_patience": loss_jitter_patience,
                "loss_jitter_boost": loss_jitter_boost,
                "loss_jitter_boost_steps": loss_jitter_boost_steps,
                "loss_jitter_trigger_count": jitter_trigger_count,
                "epoch_lr_scales": {
                    "base_scale": epoch_scale_config["base_scale"],
                    "features_early": epoch_scale_config["features_early"],
                    "features_late": epoch_scale_config["features_late"],
                    "head": epoch_scale_config["head"],
                },
                "image_size": image_size,
                "steps_per_epoch": steps_per_epoch,
                "workers_train": num_workers,
                "workers_valid": valid_num_workers,
                "stall_timeout_seconds": stall_timeout_seconds,
                "preprocess_mode": preprocess_mode,
                "use_augment": use_augment,
                "topk": topk,
                "export_topk_onnx": export_topk_onnx,
                "model_variant": model_variant,
                "aux_prior_weight": aux_prior_weight,
                "last_prior_loss": last_prior_loss,
            }
            (ckpt_dir / "mindspore_run_summary.json").write_text(
                json.dumps(summary, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

            topk_items.append(
                {
                    "epoch": int(epoch),
                    "rmse": float(valid_rmse),
                    "ckpt_path": str(ckpt_path),
                }
            )
            topk_items.sort(
                key=lambda item: (_item_rmse_value(item), _item_epoch_value(item))
            )
            topk_items = topk_items[:topk]

            for rank, item in enumerate(topk_items, start=1):
                src = Path(str(item["ckpt_path"]))
                if not src.exists():
                    continue
                alias = ckpt_dir / f"mindspore_top{rank}.ckpt"
                try:
                    shutil.copy2(src, alias)
                    item["alias_ckpt"] = str(alias)
                except Exception as exc:
                    print(f"[warn] Failed to refresh top{rank} alias: {exc}")

            topk_summary = {
                "status": "checkpointed",
                "topk": topk,
                "preprocess_mode": preprocess_mode,
                "use_augment": use_augment,
                "items": topk_items,
            }
            (ckpt_dir / "mindspore_topk_summary.json").write_text(
                json.dumps(topk_summary, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

            if stop_after_first_epoch:
                print("Benchmark mode enabled: stopping after first epoch.")
                break
    finally:
        watchdog_stop.set()

    if export_topk_onnx and topk_items:
        print("Exporting top-k checkpoints to ONNX...")
        dummy = Tensor(np.zeros((1, 3, image_size, image_size), dtype=np.float32))
        for rank, item in enumerate(topk_items, start=1):
            source_ckpt = Path(str(item.get("alias_ckpt") or item.get("ckpt_path", "")))
            if not source_ckpt.exists():
                print(f"[warn] top{rank} ckpt missing, skip ONNX export: {source_ckpt}")
                continue

            if model_variant == "morph_v2":
                net = ColonyCountNetMorphV2()
            else:
                net = ColonyCountNet()
            try:
                params = ms.load_checkpoint(str(source_ckpt))
                ms.load_param_into_net(net, params)
                net.set_train(False)
            except Exception as exc:
                print(
                    f"[warn] Failed loading top{rank} checkpoint for ONNX export: {exc}"
                )
                continue

            onnx_base = ckpt_dir / f"mindspore_top{rank}"
            try:
                ms.export(net, dummy, file_name=str(onnx_base), file_format="ONNX")
            except Exception as exc:
                print(f"[warn] Failed exporting top{rank} ONNX: {exc}")
                continue

            onnx_path = onnx_base.with_suffix(".onnx")
            if onnx_path.exists():
                item["onnx_path"] = str(onnx_path)
                try:
                    tagged_onnx = ckpt_dir / (
                        f"mindspore_top{rank}_epoch{_item_epoch_value(item)}_rmse{_item_rmse_value(item):.4f}.onnx"
                    )
                    shutil.copy2(onnx_path, tagged_onnx)
                    item["onnx_tagged_path"] = str(tagged_onnx)
                except Exception as exc:
                    print(f"[warn] Failed writing tagged ONNX for top{rank}: {exc}")

        topk_summary = {
            "status": "onnx_exported",
            "topk": topk,
            "preprocess_mode": preprocess_mode,
            "use_augment": use_augment,
            "items": topk_items,
        }
        (ckpt_dir / "mindspore_topk_summary.json").write_text(
            json.dumps(topk_summary, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    print("Training complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
