import os
import sys
import torch
import importlib

# Path to the faster_rcnn_resnet50 src
local_root = os.path.abspath(r"models-train\in-use\old\faster_rcnn_resnet50")
src_parent = os.path.join(local_root, 'src')
if src_parent not in sys.path:
    sys.path.insert(0, os.path.abspath(local_root))

from src.models.colony_detector import ColonyDetector

def load_checkpoint_model(ckpt_path, device='cpu'):
    data = torch.load(ckpt_path, map_location=device)
    if isinstance(data, dict) and 'model_state_dict' in data:
        state = data['model_state_dict']
    elif isinstance(data, dict) and 'state_dict' in data:
        state = data['state_dict']
    else:
        state = data

    model = ColonyDetector(pretrained=False)
    model.load_state_dict(state, strict=False)
    model.eval()
    return model

def export(model, output_path, device='cpu', opset=12, max_detections=200):
    model.to(device)

    class Wrapper(torch.nn.Module):
        def __init__(self, net, max_det):
            super().__init__()
            self.net = net
            self.max_det = max_det

        def forward(self, images):
            imgs = [images[i] for i in range(images.shape[0])]
            outputs = self.net(imgs)
            batch = len(outputs)
            boxes = []
            labels = []
            scores = []
            num = []
            for out in outputs:
                b = out['boxes']
                l = out['labels']
                s = out['scores']
                n = b.shape[0]
                num.append(torch.tensor([n], dtype=torch.int64))
                if n < self.max_det:
                    pad = self.max_det - n
                    b = torch.cat([b, torch.zeros((pad, 4), device=b.device, dtype=b.dtype)], dim=0)
                    l = torch.cat([l, torch.zeros((pad,), device=l.device, dtype=l.dtype)], dim=0)
                    s = torch.cat([s, torch.zeros((pad,), device=s.device, dtype=s.dtype)], dim=0)
                else:
                    b = b[:self.max_det]
                    l = l[:self.max_det]
                    s = s[:self.max_det]
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

    batch_example = torch.randn(1,3,800,800, device=device)

    input_names = ['images']
    output_names = ['boxes','labels','scores','num_detections']
    dynamic_axes = {
        'images': {0: 'batch', 2: 'height', 3: 'width'},
        'boxes': {0: 'batch', 1: 'num_detections'},
        'labels': {0: 'batch', 1: 'num_detections'},
        'scores': {0: 'batch', 1: 'num_detections'},
        'num_detections': {0: 'batch'}
    }

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    torch.onnx.export(wrapper, batch_example, output_path, opset_version=opset,
                      input_names=input_names, output_names=output_names,
                      dynamic_axes=dynamic_axes, do_constant_folding=True)
    print('Exported to', output_path)


if __name__ == '__main__':
    ckpt = r'd:\train\checkpoint_epoch_31.pth'
    out = r'.\models-train\in-use\old\faster_rcnn_resnet50\checkpoint_epoch_31.onnx'
    device = 'cpu'
    print('Loading checkpoint', ckpt)
    model = load_checkpoint_model(ckpt, device=device)
    print('Exporting...')
    export(model, out, device=device, opset=12, max_detections=200)
