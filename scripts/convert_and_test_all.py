import os
import sys
import torch
import cv2
import numpy as np
from pathlib import Path

# Prepare paths
repo_root = Path(__file__).resolve().parents[1]
onnx_dir = repo_root / 'onnx model'
onnx_dir.mkdir(parents=True, exist_ok=True)

test_pic_dir = repo_root / 'test-pic'
if not test_pic_dir.exists():
    print('test-pic directory not found:', test_pic_dir)
    sys.exit(1)

out_base = test_pic_dir

# 1) Export torchvision-based ColonyDetector (checkpoint_epoch_31.pth)
def export_colony_detector():
    # import local module
    model_pkg_root = repo_root / 'models-train' / 'in-use' / 'old' / 'faster_rcnn_resnet50'
    sys.path.insert(0, str(model_pkg_root))
    from src.models.colony_detector import ColonyDetector

    ckpt = Path(r'd:\train\checkpoint_epoch_31.pth')
    if not ckpt.exists():
        print('Checkpoint missing:', ckpt)
        return None
    data = torch.load(str(ckpt), map_location='cpu')
    if isinstance(data, dict) and 'model_state_dict' in data:
        sd = data['model_state_dict']
    elif isinstance(data, dict) and 'state_dict' in data:
        sd = data['state_dict']
    else:
        sd = data

    model = ColonyDetector(pretrained=False)
    model.load_state_dict(sd, strict=False)
    model.eval()

    out_path = onnx_dir / 'checkpoint_epoch_31.onnx'
    # wrapper similar to previous script
    class Wrapper(torch.nn.Module):
        def __init__(self, net, max_det=200):
            super().__init__()
            self.net = net
            self.max_det = max_det
        def forward(self, images):
            imgs = [images[i] for i in range(images.shape[0])]
            outputs = self.net(imgs)
            boxes, labels, scores, nums = [], [], [], []
            for out in outputs:
                b = out['boxes']
                l = out['labels']
                s = out['scores']
                n = b.shape[0]
                nums.append(torch.tensor([n], dtype=torch.int64))
                if n < self.max_det:
                    pad = self.max_det - n
                    b = torch.cat([b, torch.zeros((pad,4), device=b.device, dtype=b.dtype)], dim=0)
                    l = torch.cat([l, torch.zeros((pad,), device=l.device, dtype=l.dtype)], dim=0)
                    s = torch.cat([s, torch.zeros((pad,), device=s.device, dtype=s.dtype)], dim=0)
                else:
                    b = b[:self.max_det]; l = l[:self.max_det]; s = s[:self.max_det]
                boxes.append(b.unsqueeze(0)); labels.append(l.unsqueeze(0)); scores.append(s.unsqueeze(0))
            boxes = torch.cat(boxes, dim=0); labels = torch.cat(labels, dim=0); scores = torch.cat(scores, dim=0); nums = torch.cat(nums, dim=0)
            return boxes, labels, scores, nums

    wrapper = Wrapper(model)
    wrapper.eval()
    dummy = torch.randn(1,3,800,800)
    torch.onnx.export(wrapper, dummy, str(out_path), opset_version=12,
                      input_names=['images'], output_names=['boxes','labels','scores','num_detections'],
                      dynamic_axes={'images':{0:'batch',2:'height',3:'width'}, 'boxes':{0:'batch',1:'num_detections'}})
    print('Exported torchvision model to', out_path)
    return model


# 2) Try to convert MMDetection checkpoint heuristically by mapping keys
def export_mmdet_ckpt():
    ckpt = Path(r'd:\train\faster_rcnn_colony_epoch12.pth')
    if not ckpt.exists():
        print('MMDetection checkpoint missing:', ckpt)
        return None
    data = torch.load(str(ckpt), map_location='cpu')
    if isinstance(data, dict):
        if 'model_state_dict' in data:
            sd = data['model_state_dict']
        elif 'state_dict' in data:
            sd = data['state_dict']
        else:
            # maybe state_dict directly
            sd = data
    else:
        sd = data

    # Build a torchvision FasterRCNN with ResNet50 FPN, try infer num_classes
    num_classes = 2
    # try to detect classifier weight shape in sd
    cls_weights = [v for k,v in sd.items() if 'cls_score' in k or 'fc_cls.weight' in k or 'box_predictor.cls_score.weight' in k]
    if cls_weights:
        # infer classes from weight shape
        w = cls_weights[0]
        try:
            out_dim = w.shape[0]
            num_classes = out_dim
            print('Inferred num_classes from checkpoint:', num_classes)
        except Exception:
            pass

    # create model
    import torchvision
    model = torchvision.models.detection.fasterrcnn_resnet50_fpn(weights=None, num_classes=num_classes)
    tv_sd = model.state_dict()

    # heuristic mapping: for each tv key, try to find ckpt key with same suffix
    new_sd = {}
    ck_keys = list(sd.keys())
    for tvk in tv_sd.keys():
        found = None
        tv_tokens = tvk.split('.')
        for k in ck_keys:
            k_tokens = k.split('.')
            # match by suffix tokens
            for n in range(1, min(len(tv_tokens), len(k_tokens))+1):
                if tv_tokens[-n:] == k_tokens[-n:]:
                    if sd[k].shape == tv_sd[tvk].shape:
                        found = k
                        break
        if found:
            new_sd[tvk] = sd[found]
    # load into model
    tv_sd.update(new_sd)
    model.load_state_dict(tv_sd, strict=False)
    model.eval()
    out_path = onnx_dir / 'faster_rcnn_colony_epoch12.onnx'
    class Wrapper2(torch.nn.Module):
        def __init__(self, net, max_det=200):
            super().__init__(); self.net=net; self.max_det=max_det
        def forward(self, images):
            imgs = [images[i] for i in range(images.shape[0])]
            outputs = self.net(imgs)
            boxes, labels, scores, nums = [], [], [], []
            for out in outputs:
                b = out['boxes']; l = out['labels']; s = out['scores']; n=b.shape[0]
                nums.append(torch.tensor([n], dtype=torch.int64))
                if n < self.max_det:
                    pad = self.max_det - n
                    b = torch.cat([b, torch.zeros((pad,4), device=b.device, dtype=b.dtype)], dim=0)
                    l = torch.cat([l, torch.zeros((pad,), device=l.device, dtype=l.dtype)], dim=0)
                    s = torch.cat([s, torch.zeros((pad,), device=s.device, dtype=s.dtype)], dim=0)
                else:
                    b=b[:self.max_det]; l=l[:self.max_det]; s=s[:self.max_det]
                boxes.append(b.unsqueeze(0)); labels.append(l.unsqueeze(0)); scores.append(s.unsqueeze(0))
            boxes = torch.cat(boxes, dim=0); labels=torch.cat(labels,dim=0); scores=torch.cat(scores,dim=0); nums=torch.cat(nums,dim=0)
            return boxes, labels, scores, nums

    wrapper = Wrapper2(model)
    dummy = torch.randn(1,3,800,800)
    torch.onnx.export(wrapper, dummy, str(out_path), opset_version=12,
                      input_names=['images'], output_names=['boxes','labels','scores','num_detections'],
                      dynamic_axes={'images':{0:'batch',2:'height',3:'width'}, 'boxes':{0:'batch',1:'num_detections'}})
    print('Attempted export of MMDetection checkpoint to', out_path)
    return model


def run_inference_and_save(model, out_folder_name):
    out_dir = out_base / out_folder_name
    out_dir.mkdir(parents=True, exist_ok=True)
    # device cpu
    device = torch.device('cpu')
    model.to(device)
    model.eval()
    for img_path in sorted(test_pic_dir.glob('*.jpg')):
        img = cv2.imread(str(img_path))
        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        h,w = rgb.shape[:2]
        # preprocess: resize/normalize similar to training: here use simple resize to 800
        inp = cv2.resize(rgb, (800,800))
        inp = inp.astype('float32')/255.0
        mean = np.array([0.485,0.456,0.406]); std=np.array([0.229,0.224,0.225])
        inp = (inp - mean) / std
        inp = np.transpose(inp, (2,0,1))
        tensor = torch.from_numpy(inp).unsqueeze(0).to(device)
        with torch.no_grad():
            boxes, labels, scores, nums = model([tensor.squeeze(0)]) if hasattr(model,'predict')==False else model.predict([tensor.squeeze(0)])
        # If model returned dicts (like torchvision), handle earlier; our wrapper returns tensors
        if isinstance(boxes, torch.Tensor):
            boxes = boxes.cpu().numpy()[0]
            scores = scores.cpu().numpy()[0]
        else:
            # fallback
            boxes = []
            scores = []

        # draw boxes on original image (scale boxes back from 800x800 to original size)
        scale_x = w/800.0; scale_y = h/800.0
        vis = img.copy()
        for i,box in enumerate(boxes):
            x1,y1,x2,y2 = box
            x1 = int(x1*scale_x); x2=int(x2*scale_x); y1=int(y1*scale_y); y2=int(y2*scale_y)
            score = float(scores[i]) if i < len(scores) else 0.0
            if score < 0.05: continue
            cv2.rectangle(vis, (x1,y1),(x2,y2),(0,255,0),2)
            cv2.putText(vis, f'{score:.2f}', (x1, max(y1-6,0)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,0),1)
        out_path = out_dir / img_path.name
        cv2.imwrite(str(out_path), vis)


if __name__ == '__main__':
    print('Exporting and testing models...')
    model_tv = export_colony_detector()
    model_mmdet = export_mmdet_ckpt()
    if model_tv:
        run_inference_and_save(model_tv, 'annotated_checkpoint_epoch_31')
    if model_mmdet:
        run_inference_and_save(model_mmdet, 'annotated_faster_rcnn_colony_epoch12')
    print('Done')
