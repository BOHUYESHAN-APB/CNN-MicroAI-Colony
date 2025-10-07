import os
import sys
from pathlib import Path
import torch
import traceback

repo_root = Path(__file__).resolve().parents[1]
onnx_dir = repo_root / 'onnx model'
onnx_dir.mkdir(parents=True, exist_ok=True)
test_pic_dir = repo_root / 'test-pic'
if not test_pic_dir.exists():
    print('test-pic not found:', test_pic_dir)
    sys.exit(1)

ckpt_path = Path(r'd:\train\faster_rcnn_colony_epoch12.pth')
if not ckpt_path.exists():
    print('Checkpoint not found:', ckpt_path)
    sys.exit(1)

def safe_load(path):
    try:
        # prefer explicit weights_only=False to fully load
        return torch.load(str(path), map_location='cpu', weights_only=False)
    except TypeError:
        # older torch may not support weights_only argument
        pass
    except Exception as e:
        print('load with weights_only=False failed:', e)
    try:
        # try using safe globals to allow getattr if needed
        from torch.serialization import add_safe_globals
        with add_safe_globals([getattr]):
            return torch.load(str(path), map_location='cpu')
    except Exception as e:
        print('safe globals load failed:', e)
    # last resort: plain load (may raise)
    try:
        return torch.load(str(path), map_location='cpu')
    except Exception as e:
        print('final load failed.')
        traceback.print_exc()
        return None

print('Loading checkpoint (this may print warnings)...')
data = safe_load(ckpt_path)
if data is None:
    print('Failed to load checkpoint. Aborting.')
    sys.exit(1)

print('Checkpoint loaded, type:', type(data))
if isinstance(data, dict):
    # find state dict
    if 'model_state_dict' in data:
        sd = data['model_state_dict']
    elif 'state_dict' in data:
        sd = data['state_dict']
    elif 'model' in data and isinstance(data['model'], dict):
        sd = data['model']
    else:
        # maybe entire dict is state_dict
        sd = data
else:
    sd = data

print('state_dict type:', type(sd), 'num keys:', len(sd) if hasattr(sd,'__len__') else 'N/A')

# Try to infer num_classes from any classifier weight
num_classes = None
for k,v in sd.items():
    if any(x in k for x in ['cls_score', 'fc_cls.weight', 'box_predictor.cls_score.weight', 'roi_heads.box_predictor.cls_score.weight']):
        try:
            num_classes = v.shape[0]
            print('Inferred num_classes from', k, '=', num_classes)
            break
        except Exception:
            continue
if num_classes is None:
    num_classes = 2
    print('Defaulting num_classes to', num_classes)

print('Building torchvision Faster R-CNN (ResNet50-FPN) with num_classes=', num_classes)
import torchvision
model = torchvision.models.detection.fasterrcnn_resnet50_fpn(weights=None, num_classes=num_classes)
tv_sd = model.state_dict()

print('Attempting heuristic state-dict mapping...')
ck_keys = list(sd.keys())
new_sd = {}
for tvk in tv_sd.keys():
    found = None
    tv_tokens = tvk.split('.')
    # search for key with matching suffix and same shape
    for k in ck_keys:
        k_tokens = k.split('.')
        # match by increasing suffix length
        for n in range(1, min(len(tv_tokens), len(k_tokens))+1):
            if tv_tokens[-n:] == k_tokens[-n:]:
                try:
                    if hasattr(sd[k], 'shape') and hasattr(tv_sd[tvk], 'shape') and sd[k].shape == tv_sd[tvk].shape:
                        found = k
                        break
                except Exception:
                    pass
        if found:
            break
    if found:
        new_sd[tvk] = sd[found]

matched = len(new_sd)
print(f'Matched {matched} / {len(tv_sd)} parameters by heuristic')
tv_sd.update(new_sd)
model.load_state_dict(tv_sd, strict=False)
# Ensure model parameters are float32 to avoid dtype mismatches
model = model.float()
model.eval()

onnx_out = onnx_dir / 'faster_rcnn_colony_epoch12.onnx'
print('Exporting to ONNX:', onnx_out)
try:
    class Wrapper(torch.nn.Module):
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

    wrapper = Wrapper(model)
    # ensure dummy is float32
    dummy = torch.randn(1,3,800,800).to(dtype=torch.float32)
    torch.onnx.export(wrapper, dummy, str(onnx_out), opset_version=12,
                      input_names=['images'], output_names=['boxes','labels','scores','num_detections'],
                      dynamic_axes={'images':{0:'batch',2:'height',3:'width'}, 'boxes':{0:'batch',1:'num_detections'}})
    print('ONNX export completed:', onnx_out)
except Exception as e:
    print('Export failed:', e)
    traceback.print_exc()

print('Running inference on test-pic and saving annotated images...')
import cv2, numpy as np
out_dir = test_pic_dir / 'annotated_faster_rcnn_colony_epoch12'
out_dir.mkdir(parents=True, exist_ok=True)
device = torch.device('cpu')
# Ensure model is on the desired device and in float32 to avoid dtype mismatches
model = model.to(device=device, dtype=torch.float32)
model.eval()
for img_path in sorted(test_pic_dir.glob('*.jpg')):
    img = cv2.imread(str(img_path))
    if img is None:
        continue
    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    h,w = rgb.shape[:2]
    inp = cv2.resize(rgb, (800,800)).astype('float32')/255.0
    mean = np.array([0.485,0.456,0.406]); std=np.array([0.229,0.224,0.225])
    inp = (inp - mean) / std
    inp = np.transpose(inp,(2,0,1))
    tensor = torch.from_numpy(inp).unsqueeze(0)
    # make sure input tensor is float32 and on the same device as the model
    tensor = tensor.to(dtype=torch.float32, device=device)
    with torch.no_grad():
        preds = model([tensor.squeeze(0)])
    if isinstance(preds, list) and len(preds)>0:
        out = preds[0]
        boxes = out['boxes'].cpu().numpy()
        scores = out['scores'].cpu().numpy()
    else:
        boxes = np.zeros((0,4)); scores = np.array([])
    vis = img.copy()
    scale_x = w/800.0; scale_y = h/800.0
    for i,box in enumerate(boxes):
        score = float(scores[i]) if i < len(scores) else 0.0
        if score < 0.05: continue
        x1,y1,x2,y2 = box
        x1 = int(x1*scale_x); x2=int(x2*scale_x); y1=int(y1*scale_y); y2=int(y2*scale_y)
        cv2.rectangle(vis, (x1,y1),(x2,y2),(0,0,255),2)
        cv2.putText(vis, f'{score:.2f}', (x1, max(y1-6,0)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,255),1)
    cv2.imwrite(str(out_dir / img_path.name), vis)

print('Annotated images saved to', out_dir)
