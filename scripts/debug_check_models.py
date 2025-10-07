import sys
from pathlib import Path
import torch
import numpy as np
import cv2

repo_root = Path(__file__).resolve().parents[1]
test_pic_dir = repo_root / 'test-pic'
if not test_pic_dir.exists():
    print('test-pic not found', test_pic_dir)
    sys.exit(1)

img_files = sorted(test_pic_dir.glob('*.jpg'))
if len(img_files) == 0:
    print('no jpg images in test-pic')
    sys.exit(1)

img_path = img_files[0]
print('Using image:', img_path)
img = cv2.imread(str(img_path))
rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

def preprocess_for_torchvision(rgb_img, short_side=800):
    h,w = rgb_img.shape[:2]
    inp = cv2.resize(rgb_img, (short_side, short_side)).astype('float32')/255.0
    mean = np.array([0.485,0.456,0.406]); std = np.array([0.229,0.224,0.225])
    inp = (inp - mean) / std
    inp = np.transpose(inp, (2,0,1))
    tensor = torch.from_numpy(inp).unsqueeze(0)
    return tensor

def print_preds_info(preds, topk=10):
    if isinstance(preds, list):
        preds = preds[0]
    if not preds:
        print('empty preds')
        return
    boxes = preds.get('boxes')
    scores = preds.get('scores')
    labels = preds.get('labels')
    if boxes is None or scores is None:
        print('no boxes/scores in preds')
        return
    print('boxes shape:', boxes.shape)
    print('scores: min', float(scores.min()), 'max', float(scores.max()))
    svals = scores.detach().cpu().numpy()
    top_idx = np.argsort(-svals)[:topk]
    print('top scores:', svals[top_idx])
    if labels is not None:
        print('labels unique:', torch.unique(labels).cpu().numpy())


#### Test torchvision-based checkpoint
tv_ckpt = Path(r'd:\train\checkpoint_epoch_31.pth')
if tv_ckpt.exists():
    print('\nTesting torchvision checkpoint:', tv_ckpt)
    data = torch.load(str(tv_ckpt), map_location='cpu')
    if isinstance(data, dict) and 'model_state_dict' in data:
        sd = data['model_state_dict']
    elif isinstance(data, dict) and 'state_dict' in data:
        sd = data['state_dict']
    else:
        sd = data
    import torchvision
    # try infer num_classes
    num_classes = None
    for k,v in sd.items():
        if 'cls_score' in k and hasattr(v,'shape'):
            num_classes = v.shape[0]
            break
    if num_classes is None:
        num_classes = 2
    print('Constructing torchvision model with num_classes=', num_classes)
    model = torchvision.models.detection.fasterrcnn_resnet50_fpn(weights=None, num_classes=num_classes)
    try:
        model.load_state_dict(sd, strict=False)
        print('state_dict loaded (torchvision)')
    except Exception as e:
        print('load_state_dict error:', e)
    model = model.eval().float()
    tensor = preprocess_for_torchvision(rgb)
    tensor = tensor.to(dtype=torch.float32)
    with torch.no_grad():
        try:
            preds = model([tensor.squeeze(0)])
            print_preds_info(preds)
        except Exception as e:
            print('Error running torchvision model:', e)
else:
    print('torchvision checkpoint not found:', tv_ckpt)


#### Test MMDetection-style checkpoint via heuristic mapping (reuse mapping logic)
mm_ckpt = Path(r'd:\train\faster_rcnn_colony_epoch12.pth')
if mm_ckpt.exists():
    print('\nTesting MMDetection-style checkpoint (heuristic mapping):', mm_ckpt)
    from torch.serialization import add_safe_globals
    try:
        data = torch.load(str(mm_ckpt), map_location='cpu')
    except Exception:
        try:
            with add_safe_globals([getattr]):
                data = torch.load(str(mm_ckpt), map_location='cpu')
        except Exception as e:
            print('failed to load mm checkpoint:', e)
            data = None
    if data is None:
        print('skip mmtest')
    else:
        sd = None
        if isinstance(data, dict):
            if 'model_state_dict' in data:
                sd = data['model_state_dict']
            elif 'state_dict' in data:
                sd = data['state_dict']
            else:
                sd = data
        else:
            sd = data
        import torchvision
        model = torchvision.models.detection.fasterrcnn_resnet50_fpn(weights=None, num_classes=2)
        tv_sd = model.state_dict()
        # heuristic mapping by suffix+shape
        new_sd = {}
        ck_keys = list(sd.keys())
        for tvk in tv_sd.keys():
            found = None
            tv_tokens = tvk.split('.')
            for k in ck_keys:
                k_tokens = k.split('.')
                for n in range(1, min(len(tv_tokens), len(k_tokens))+1):
                    if tv_tokens[-n:] == k_tokens[-n:]:
                        try:
                            if hasattr(sd[k],'shape') and hasattr(tv_sd[tvk],'shape') and sd[k].shape == tv_sd[tvk].shape:
                                found = k; break
                        except Exception:
                            pass
                if found: break
            if found:
                new_sd[tvk] = sd[found]
        print('heuristic matched', len(new_sd), '/', len(tv_sd))
        tv_sd.update(new_sd)
        model.load_state_dict(tv_sd, strict=False)
        model = model.eval().float()
        tensor = preprocess_for_torchvision(rgb)
        tensor = tensor.to(dtype=torch.float32)
        with torch.no_grad():
            try:
                preds = model([tensor.squeeze(0)])
                print_preds_info(preds)
            except Exception as e:
                print('Error running mapped mm model:', e)
else:
    print('mm checkpoint not found:', mm_ckpt)


#### Try ONNX Runtime if available to run the exported ONNXs
try:
    import onnxruntime as ort
    print('\nONNX Runtime available. Testing exported ONNX models...')
    onnx_list = [repo_root / 'onnx model' / 'faster_rcnn_colony_epoch12.onnx', repo_root / 'models-train' / 'in-use' / 'old' / 'faster_rcnn_resnet50' / 'checkpoint_epoch_31.onnx']
    for onnxp in onnx_list:
        if onnxp.exists():
            print('Testing ONNX:', onnxp)
            sess = ort.InferenceSession(str(onnxp))
            inp_name = sess.get_inputs()[0].name
            img_tensor = preprocess_for_torchvision(rgb).numpy()
            # ONNX export used batch size 1 and images shape (1,3,H,W)
            try:
                out = sess.run(None, {inp_name: img_tensor.astype('float32')})
                print('ONNX outputs count:', len(out))
                for i,o in enumerate(out):
                    print(f' out[{i}] shape:', getattr(o,'shape', None))
            except Exception as e:
                print('ONNX inference error:', e)
        else:
            print('ONNX not found:', onnxp)
except Exception as e:
    print('\nONNX Runtime not installed or failed to import:', e)

print('\nDebug checks complete')
