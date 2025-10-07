import sys
from pathlib import Path
import torch
import numpy as np
import cv2

repo_root = Path(__file__).resolve().parents[1]
test_pic_dir = repo_root / 'test-pic'
if not test_pic_dir.exists():
    print('test-pic not found', test_pic_dir); sys.exit(1)

def preprocess(rgb_img, size=800):
    h,w = rgb_img.shape[:2]
    img = cv2.resize(rgb_img, (size, size)).astype('float32')/255.0
    mean = np.array([0.485,0.456,0.406]); std=np.array([0.229,0.224,0.225])
    img = (img - mean) / std
    img = np.transpose(img, (2,0,1))
    return torch.from_numpy(img).unsqueeze(0)

def draw_boxes_and_save(orig_bgr, boxes, scores, out_path, score_thr=0.3):
    vis = orig_bgr.copy()
    h,w = orig_bgr.shape[:2]
    for i,(b,s) in enumerate(zip(boxes, scores)):
        if s < score_thr: continue
        x1,y1,x2,y2 = b
        # boxes are in resized 800x800 coordinates; scale back
        x1 = int(x1 * (w/800.0)); x2 = int(x2 * (w/800.0))
        y1 = int(y1 * (h/800.0)); y2 = int(y2 * (h/800.0))
        cv2.rectangle(vis, (x1,y1),(x2,y2),(0,0,255),2)
        cv2.putText(vis, f'{s:.2f}', (x1, max(y1-6,0)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,255),1)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out_path), vis)

#### PyTorch torchvision model inference
tv_ckpt = Path(r'd:\train\checkpoint_epoch_31.pth')
if tv_ckpt.exists():
    print('Loading torchvision checkpoint:', tv_ckpt)
    data = torch.load(str(tv_ckpt), map_location='cpu')
    if isinstance(data, dict) and 'model_state_dict' in data:
        sd = data['model_state_dict']
    elif isinstance(data, dict) and 'state_dict' in data:
        sd = data['state_dict']
    else:
        sd = data
    import torchvision
    num_classes = 2
    for k,v in sd.items():
        if 'cls_score' in k and hasattr(v,'shape'):
            num_classes = v.shape[0]; break
    model = torchvision.models.detection.fasterrcnn_resnet50_fpn(weights=None, num_classes=num_classes)
    model.load_state_dict(sd, strict=False)
    # ensure model params and buffers are float32 and on CPU
    device = torch.device('cpu')
    model = model.to(device=device)
    for p in model.parameters():
        if p.dtype != torch.float32:
            p.data = p.data.float()
    for b in model.buffers():
        if b.dtype != torch.float32:
            b.data = b.data.float()
    model = model.eval().float()
    out_dir = test_pic_dir / 'visualized_pytorch'
    for p in sorted(test_pic_dir.glob('*.jpg')):
        img = cv2.imread(str(p))
        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        tensor = preprocess(rgb)
        tensor = tensor.to(dtype=torch.float32, device=device)
        with torch.no_grad():
            try:
                preds = model([tensor.squeeze(0)])
                if isinstance(preds, list) and len(preds)>0:
                    out = preds[0]
                    boxes = out.get('boxes', torch.zeros((0,4))).cpu().numpy()
                    scores = out.get('scores', torch.zeros((0,))).cpu().numpy()
                else:
                    boxes = np.zeros((0,4)); scores = np.array([])
            except Exception as e:
                print('PyTorch inference error on', p, e)
                boxes = np.zeros((0,4)); scores = np.array([])
        draw_boxes_and_save(img, boxes, scores, out_dir / p.name)
    print('PyTorch visualizations saved to', out_dir)
else:
    print('torchvision checkpoint not found:', tv_ckpt)

#### ONNX Runtime visualization for exported ONNXs
try:
    import onnxruntime as ort
    onnx_dir = repo_root / 'onnx model'
    onnx_files = [onnx_dir / 'faster_rcnn_colony_epoch12.onnx', repo_root / 'models-train' / 'in-use' / 'old' / 'faster_rcnn_resnet50' / 'checkpoint_epoch_31.onnx']
    for onnxp in onnx_files:
        if not onnxp.exists():
            print('ONNX not found, skip:', onnxp); continue
        print('Running ONNX Runtime for', onnxp)
        sess = ort.InferenceSession(str(onnxp))
        inp_name = sess.get_inputs()[0].name
        out_dir = test_pic_dir / f'visualized_onnx_{onnxp.stem}'
        for p in sorted(test_pic_dir.glob('*.jpg')):
            img = cv2.imread(str(p))
            rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            tensor = preprocess(rgb).numpy()
            try:
                outs = sess.run(None, {inp_name: tensor.astype('float32')})
                # outs: boxes, labels, scores, num_detections
                boxes = outs[0][0]
                scores = outs[2][0]
            except Exception as e:
                print('ONNX inference error on', p, e)
                boxes = np.zeros((0,4)); scores = np.array([])
            draw_boxes_and_save(img, boxes, scores, out_dir / p.name)
        print('ONNX visualizations saved to', out_dir)
except Exception as e:
    print('ONNX Runtime not available or failed:', e)

print('Visualization complete')
