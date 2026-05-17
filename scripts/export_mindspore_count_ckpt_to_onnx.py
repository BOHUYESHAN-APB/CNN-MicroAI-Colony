from __future__ import annotations

import argparse
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export MindSpore colony count-regression ckpt to ONNX"
    )
    parser.add_argument("--ckpt", required=True, help="MindSpore checkpoint path")
    parser.add_argument("--output", required=True, help="Output ONNX path")
    parser.add_argument(
        "--input-size",
        type=int,
        default=384,
        help="Square input size used by model preprocessing",
    )
    parser.add_argument(
        "--model-variant",
        choices=["baseline", "morph_v2"],
        default="baseline",
        help="Model architecture variant used when training checkpoint",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    ckpt_path = Path(args.ckpt)
    output_path = Path(args.output)

    if not ckpt_path.exists():
        raise FileNotFoundError(f"Checkpoint not found: {ckpt_path}")
    if args.input_size < 128:
        raise ValueError("--input-size must be >= 128")

    try:
        import mindspore as ms
        from mindspore import Tensor, nn, ops
    except Exception as exc:
        raise RuntimeError(
            "MindSpore is required for export. Run in MindSpore environment."
        ) from exc

    class ColonyCountNet(nn.Cell):
        def __init__(self) -> None:
            super().__init__()
            self.features = nn.SequentialCell(
                [
                    nn.Conv2d(
                        3, 32, kernel_size=3, stride=1, pad_mode="pad", padding=1
                    ),
                    nn.ReLU(),
                    nn.MaxPool2d(kernel_size=2, stride=2),
                    nn.Conv2d(
                        32, 64, kernel_size=3, stride=1, pad_mode="pad", padding=1
                    ),
                    nn.ReLU(),
                    nn.MaxPool2d(kernel_size=2, stride=2),
                    nn.Conv2d(
                        64, 128, kernel_size=3, stride=1, pad_mode="pad", padding=1
                    ),
                    nn.ReLU(),
                    nn.MaxPool2d(kernel_size=2, stride=2),
                    nn.Conv2d(
                        128, 256, kernel_size=3, stride=1, pad_mode="pad", padding=1
                    ),
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
                    nn.Conv2d(
                        3, 32, kernel_size=3, stride=1, pad_mode="pad", padding=1
                    ),
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
                    nn.Conv2d(
                        3, 16, kernel_size=3, stride=1, pad_mode="pad", padding=1
                    ),
                    nn.ReLU(),
                    nn.Conv2d(
                        16, 16, kernel_size=3, stride=1, pad_mode="pad", padding=1
                    ),
                    nn.ReLU(),
                    nn.Conv2d(16, 1, kernel_size=1, stride=1, pad_mode="valid"),
                ]
            )
            self.prior_pool = nn.AvgPool2d(kernel_size=8, stride=8)

        def construct(self, x: Tensor) -> Tensor:
            prior_logits = self.prior_head(x)
            gate = ops.sigmoid(self.prior_pool(prior_logits))
            features = self.features(x)
            features = features * (1.0 + gate * self.fusion_alpha)
            pooled = ops.mean(features, axis=(2, 3))
            return self.head(pooled)

    if args.model_variant == "morph_v2":
        net = ColonyCountNetMorphV2()
    else:
        net = ColonyCountNet()
    params = ms.load_checkpoint(str(ckpt_path))
    ms.load_param_into_net(net, params)
    net.set_train(False)

    dummy = Tensor(
        ms.numpy.zeros(
            (1, 3, int(args.input_size), int(args.input_size)), dtype=ms.float32
        )
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    base = output_path.with_suffix("")
    ms.export(net, dummy, file_name=str(base), file_format="ONNX")

    generated = base.with_suffix(".onnx")
    if not generated.exists():
        raise RuntimeError(f"Export finished but ONNX file not found: {generated}")

    if generated.resolve() != output_path.resolve():
        generated.replace(output_path)

    print(f"Exported ONNX: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
