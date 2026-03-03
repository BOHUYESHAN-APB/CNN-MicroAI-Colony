"""Export Faster R-CNN PyTorch checkpoints to ONNX.

This script loads a checkpoint (state_dict or model checkpoint) for a torchvision
`fasterrcnn_resnet50_fpn` style model and exports a single-file ONNX model.

Outputs (dynamic axes enabled):
- boxes: [batch, num_detections, 4]
- labels: [batch, num_detections]
- scores: [batch, num_detections]
- num_detections: [batch]

Usage examples:
  python scripts/export_fasterrcnn_to_onnx.py \
    --checkpoint d:\train\faster_rcnn_colony_epoch12.pth \
    --output models-train\in-use\old\main_models_train\faster_rcnn_colony_epoch12.onnx \
    --device cpu

  python scripts/export_fasterrcnn_to_onnx.py \
    --checkpoint d:\train\checkpoint_epoch_31.pth \
    --output models-train\in-use\old\faster_rcnn_resnet50\checkpoint_epoch_31.onnx \
    --device cpu

"""

import argparse
import torch
import torchvision
import os


def build_model(num_classes=2):
    # Build a fresh model with the right number of classes (including background)
    model = torchvision.models.detection.fasterrcnn_resnet50_fpn(
        weights=None, weights_backbone=None, num_classes=num_classes
    )
    model.eval()
    return model


def load_checkpoint_into_model(model, ckpt_path, map_location="cpu"):
    data = torch.load(ckpt_path, map_location=map_location, weights_only=False)
    # checkpoint might be a state_dict or a dict with wrapped state dict
    if isinstance(data, dict):
        if "model_state_dict" in data:
            state = data["model_state_dict"]
        elif "model" in data:
            state = data["model"]
        elif "state_dict" in data:
            state = data["state_dict"]
        else:
            # assume it's the state_dict directly
            state = data
    else:
        state = data

    # remove common distributed-training prefixes
    cleaned_state = {}
    for k, v in state.items():
        nk = k
        if nk.startswith("module."):
            nk = nk[len("module.") :]
        if nk.startswith("model."):
            nk = nk[len("model.") :]
        cleaned_state[nk] = v

    # try to load state dict leniently and print diagnostics
    missing, unexpected = model.load_state_dict(cleaned_state, strict=False)
    print(
        f"Loaded checkpoint with missing={len(missing)}, unexpected={len(unexpected)}"
    )
    if missing:
        print("Missing keys sample:", missing[:10])
    if unexpected:
        print("Unexpected keys sample:", unexpected[:10])
    return model


def export_onnx(model, output_path, device="cpu", opset=12, max_detections=100):
    model.to(device)

    # Create a dummy input: list[Tensor] for torchvision detection models
    dummy_img = torch.randn(3, 800, 800, device=device)
    # detection models expect list of tensors
    example_inputs = [dummy_img]

    # Forward once to ensure model is ready
    with torch.no_grad():
        _ = model(example_inputs)

    # We will export a wrapper that takes a single tensor (batch of images)
    # and returns padded outputs with dynamic axes.

    class Wrapper(torch.nn.Module):
        def __init__(self, net, max_det):
            super().__init__()
            self.net = net
            self.max_det = max_det

        def forward(self, images):
            # images: [batch, 3, H, W]
            imgs = [images[i] for i in range(images.shape[0])]
            outputs = self.net(imgs)
            # outputs is list of dicts with keys boxes, labels, scores
            batch = len(outputs)
            boxes = []
            labels = []
            scores = []
            num = []
            for out in outputs:
                b = out["boxes"]
                l = out["labels"]
                s = out["scores"]
                n = b.shape[0]
                num.append(torch.tensor([n], dtype=torch.int64))
                # pad to max_det
                if n < self.max_det:
                    pad = self.max_det - n
                    b = torch.cat(
                        [b, torch.zeros((pad, 4), device=b.device, dtype=b.dtype)],
                        dim=0,
                    )
                    l = torch.cat(
                        [l, torch.zeros((pad,), device=l.device, dtype=l.dtype)], dim=0
                    )
                    s = torch.cat(
                        [s, torch.zeros((pad,), device=s.device, dtype=s.dtype)], dim=0
                    )
                else:
                    b = b[: self.max_det]
                    l = l[: self.max_det]
                    s = s[: self.max_det]
                boxes.append(b.unsqueeze(0))
                labels.append(l.unsqueeze(0))
                scores.append(s.unsqueeze(0))

            boxes = torch.cat(boxes, dim=0)
            labels = torch.cat(labels, dim=0)
            scores = torch.cat(scores, dim=0)
            num = torch.cat(num, dim=0)
            return boxes, labels, scores, num

    wrapper = Wrapper(model, max_detections)
    wrapper.eval()

    # example batch size 1
    batch_example = torch.randn(1, 3, 800, 800, device=device)

    input_names = ["images"]
    output_names = ["boxes", "labels", "scores", "num_detections"]
    dynamic_axes = {
        "images": {0: "batch", 2: "height", 3: "width"},
        "boxes": {0: "batch", 1: "num_detections"},
        "labels": {0: "batch", 1: "num_detections"},
        "scores": {0: "batch", 1: "num_detections"},
        "num_detections": {0: "batch"},
    }

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    torch.onnx.export(
        wrapper,
        (batch_example,),
        output_path,
        verbose=False,
        opset_version=opset,
        input_names=input_names,
        output_names=output_names,
        dynamic_axes=dynamic_axes,
        do_constant_folding=True,
    )

    print(f"Exported ONNX to: {output_path}")


def parse_args():
    p = argparse.ArgumentParser(description="Export Faster R-CNN checkpoint to ONNX")
    p.add_argument("--checkpoint", required=True, help="Path to .pth checkpoint")
    p.add_argument("--output", required=True, help="Output .onnx path")
    p.add_argument("--device", default="cpu", choices=["cpu", "cuda"], help="Device")
    p.add_argument("--opset", type=int, default=12, help="ONNX opset version")
    p.add_argument(
        "--max-detections",
        type=int,
        default=100,
        help="Max detections to pad/truncate to",
    )
    p.add_argument(
        "--num-classes",
        type=int,
        default=2,
        help="Number of classes (including background)",
    )
    return p.parse_args()


def main():
    args = parse_args()
    device = args.device
    print(f"Loading model, num_classes={args.num_classes}")
    model = build_model(num_classes=args.num_classes)
    print(f"Loading checkpoint: {args.checkpoint}")
    model = load_checkpoint_into_model(model, args.checkpoint, map_location=device)
    export_onnx(
        model,
        args.output,
        device=device,
        opset=args.opset,
        max_detections=args.max_detections,
    )


if __name__ == "__main__":
    main()
