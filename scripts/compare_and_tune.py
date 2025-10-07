import sys
from pathlib import Path
import numpy as np
import cv2
import torch
import torchvision
from torchvision.ops import nms

repo_root = Path(__file__).resolve().parents[1]
test_pic_dir = repo_root / 'test-pic'
if not test_pic_dir.exists():
    print('test-pic not found', test_pic_dir); sys.exit(1)

py_ckpt = Path(r'd:\train\checkpoint_epoch_31.pth')
onnx_a = repo_root / 'onnx model' / 'faster_rcnn_colony_epoch12.onnx'
onnx_b = repo_root / 'models-train' / 'in-use' / 'old' / 'faster_rcnn_resnet50' / 'checkpoint_epoch_31.onnx'

def preprocess_rgb(rgb, size=800):
    img = cv2.resize(rgb, (size, size)).astype('float32') / 255.0
    mean = np.array([0.485,0.456,0.406]); std=np.array([0.229,0.224,0.225])
    img = (img - mean) / std
    img = np.transpose(img, (2,0,1))
    return torch.from_numpy(img).unsqueeze(0)

def nms_numpy(boxes, scores, iou_thr=0.5):
    # boxes: (N,4) [x1,y1,x2,y2]
    if boxes.shape[0] == 0:
        return np.array([], dtype=np.int64)
    x1 = boxes[:,0]; y1 = boxes[:,1]; x2 = boxes[:,2]; y2 = boxes[:,3]
    areas = (x2 - x1 + 1) * (y2 - y1 + 1)
    order = scores.argsort()[::-1]
    keep = []
    while order.size > 0:
        i = order[0]
        keep.append(i)
        xx1 = np.maximum(x1[i], x1[order[1:]])
        yy1 = np.maximum(y1[i], y1[order[1:]])
        xx2 = np.minimum(x2[i], x2[order[1:]])
        yy2 = np.minimum(y2[i], y2[order[1:]])
        w = np.maximum(0.0, xx2 - xx1 + 1)
        h = np.maximum(0.0, yy2 - yy1 + 1)
        inter = w * h
        ovr = inter / (areas[i] + areas[order[1:]] - inter)
        inds = np.where(ovr <= iou_thr)[0]
        order = order[inds + 1]
    return np.array(keep, dtype=np.int64)

def draw_and_save(orig_bgr, boxes, scores, outp, score_thr=0.4):
    vis = orig_bgr.copy()
    h,w = orig_bgr.shape[:2]
    for i,(b,s) in enumerate(zip(boxes, scores)):
        if s < score_thr: continue
        x1,y1,x2,y2 = b
        x1 = int(x1 * (w/800.0)); x2 = int(x2 * (w/800.0))
        y1 = int(y1 * (h/800.0)); y2 = int(y2 * (h/800.0))
        cv2.rectangle(vis, (x1,y1),(x2,y2),(0,0,255),2)
        cv2.putText(vis, f'{s:.2f}', (x1, max(y1-6,0)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,255),1)
    outp.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(outp), vis)

### Load PyTorch model
py_model = None
if py_ckpt.exists():
    print('Loading PyTorch checkpoint', py_ckpt)
    data = torch.load(str(py_ckpt), map_location='cpu')
    if isinstance(data, dict) and 'model_state_dict' in data:
        sd = data['model_state_dict']
    elif isinstance(data, dict) and 'state_dict' in data:
        sd = data['state_dict']
    else:
        sd = data
    num_classes = 2
    for k,v in sd.items():
        if 'cls_score' in k and hasattr(v,'shape'):
            num_classes = v.shape[0]; break
    py_model = torchvision.models.detection.fasterrcnn_resnet50_fpn(weights=None, num_classes=num_classes)
    py_sd = py_model.state_dict()
    # try load many keys
    matched = 0
    for k in py_sd.keys():
        if k in sd and hasattr(sd[k],'shape') and hasattr(py_sd[k],'shape') and sd[k].shape == py_sd[k].shape:
            py_sd[k] = sd[k]; matched += 1
    py_model.load_state_dict(py_sd, strict=False)
    # ensure model params and buffers are float32 and on CPU to avoid dtype mismatch
    device = torch.device('cpu')
    py_model = py_model.to(device=device)
    for p in py_model.parameters():
        if p.dtype != torch.float32:
            p.data = p.data.float()
    for b in py_model.buffers():
        if b.dtype != torch.float32:
            b.data = b.data.float()
    py_model = py_model.eval().float()
    print('PyTorch model loaded, matched params:', matched, '/', len(py_sd))
else:
    print('PyTorch checkpoint not found:', py_ckpt)

### Prepare ONNX runtime sessions
ort_sessions = {}
try:
    import onnxruntime as ort
    for name,p in [('onnx_a', onnx_a), ('onnx_b', onnx_b)]:
        if p.exists():
            try:
                sess = ort.InferenceSession(str(p))
                ort_sessions[name] = sess
                print('Loaded ONNX session', name)
            except Exception as e:
                print('Failed to load ONNX', p, e)
        else:
            print('ONNX file missing', p)
except Exception as e:
    print('onnxruntime not available:', e)

thresholds = [0.3, 0.35, 0.4, 0.45, 0.5]
iou_thr = 0.3
report_lines = []

for img_p in sorted(test_pic_dir.glob('*.jpg')):
    print('\nImage:', img_p.name)
    img_bgr = cv2.imread(str(img_p))
    rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    # PyTorch
    if py_model is not None:
        t = preprocess_rgb(rgb)
        t = t.to(dtype=torch.float32, device='cpu')
        with torch.no_grad():
            try:
                preds = py_model([t.squeeze(0)])
            except Exception as e:
                print('PyTorch model inference error:', e)
                preds = []
        if isinstance(preds, list) and len(preds)>0:
            out = preds[0]
            boxes = out.get('boxes', torch.zeros((0,4))).cpu().numpy()
            scores = out.get('scores', torch.zeros((0,))).cpu().numpy()
        else:
            boxes = np.zeros((0,4)); scores = np.array([])
        for thr in thresholds:
            keep = nms_numpy(boxes, scores, iou_thr=iou_thr)
            cnt = np.sum(scores[keep] >= thr) if keep.size>0 else 0
            report_lines.append(f'{img_p.name},pytorch,thr={thr},count={cnt},top_score={scores.max() if scores.size>0 else 0:.3f}')
        # save tuned visualization at default thr=0.45
        keep = nms_numpy(boxes, scores, iou_thr=iou_thr)
        if keep.size>0:
            sel = keep[np.argsort(-scores[keep])]
            draw_and_save(img_bgr, boxes[sel], scores[sel], repo_root / 'test-pic' / 'tuned_pytorch' / img_p.name, score_thr=0.45)
        else:
            draw_and_save(img_bgr, boxes, scores, repo_root / 'test-pic' / 'tuned_pytorch' / img_p.name, score_thr=0.45)

    # ONNX sessions
    for name,sess in ort_sessions.items():
        inp_name = sess.get_inputs()[0].name
        t_np = preprocess_rgb(rgb).numpy().astype('float32')
        try:
            outs = sess.run(None, {inp_name: t_np})
            # outs: boxes, labels, scores, num_detections
            boxes_ = outs[0][0]
            scores_ = outs[2][0]
        except Exception as e:
            print('ONNX inference error for', name, e)
            boxes_ = np.zeros((0,4)); scores_ = np.array([])
        for thr in thresholds:
            keep = nms_numpy(boxes_, scores_, iou_thr=iou_thr)
            cnt = np.sum(scores_[keep] >= thr) if keep.size>0 else 0
            report_lines.append(f'{img_p.name},{name},thr={thr},count={cnt},top_score={scores_.max() if scores_.size>0 else 0:.3f}')
        # save tuned visualization
        keep = nms_numpy(boxes_, scores_, iou_thr=iou_thr)
        if keep.size>0:
            sel = keep[np.argsort(-scores_[keep])]
            draw_and_save(img_bgr, boxes_[sel], scores_[sel], repo_root / 'test-pic' / f'tuned_{name}' / img_p.name, score_thr=0.45)
        else:
            draw_and_save(img_bgr, boxes_, scores_, repo_root / 'test-pic' / f'tuned_{name}' / img_p.name, score_thr=0.45)


# write report
out_report = repo_root / 'scripts' / 'compare_report.csv'
with open(out_report, 'w', encoding='utf-8') as f:
    f.write('image,model,thr,count,top_score\n')
    f.write('\n'.join(report_lines))

print('\nComparison complete. Report saved to', out_report)
