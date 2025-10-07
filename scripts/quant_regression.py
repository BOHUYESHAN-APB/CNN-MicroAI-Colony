from pathlib import Path
import numpy as np
import cv2
import onnxruntime as ort

repo_root = Path(__file__).resolve().parents[1]
orig_onnx = repo_root / 'models-train' / 'in-use' / 'old' / 'faster_rcnn_resnet50' / 'checkpoint_epoch_31.onnx'
quant_onnx = repo_root / 'onnx model' / 'checkpoint_epoch_31.static_qdq.onnx'
test_dir = repo_root / 'test-pic'
out_csv = repo_root / 'scripts' / 'quant_regression_report.csv'

def preprocess(rgb, size=800):
    img = cv2.resize(rgb, (size, size)).astype('float32')/255.0
    mean = np.array([0.485,0.456,0.406]); std=np.array([0.229,0.224,0.225])
    img = (img - mean)/std
    img = np.transpose(img, (2,0,1))
    return img[np.newaxis, ...].astype('float32')

def iou(boxA, boxB):
    xA = max(boxA[0], boxB[0]); yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2]); yB = min(boxA[3], boxB[3])
    interW = max(0, xB - xA); interH = max(0, yB - yA)
    inter = interW * interH
    boxAArea = max(0,(boxA[2]-boxA[0])) * max(0,(boxA[3]-boxA[1]))
    boxBArea = max(0,(boxB[2]-boxB[0])) * max(0,(boxB[3]-boxB[1]))
    denom = boxAArea + boxBArea - inter
    return inter/denom if denom>0 else 0.0

def postprocess_onnx_outputs(outs):
    # outs: boxes (1,N,4), labels (1,N), scores (1,N), num_detections (1,)
    boxes = outs[0][0]
    scores = outs[2][0]
    return boxes, scores

sess_orig = ort.InferenceSession(str(orig_onnx))
sess_quant = ort.InferenceSession(str(quant_onnx))
inp_name = sess_orig.get_inputs()[0].name

threshold = 0.45
iou_match_thr = 0.5
rows = []

for p in sorted(test_dir.glob('*.jpg')):
    img = cv2.imread(str(p))
    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    inp = preprocess(rgb)
    try:
        o1 = sess_orig.run(None, {inp_name: inp})
        o2 = sess_quant.run(None, {inp_name: inp})
    except Exception as e:
        print('ONNX runtime error for', p.name, e)
        continue
    boxes1, scores1 = postprocess_onnx_outputs(o1)
    boxes2, scores2 = postprocess_onnx_outputs(o2)
    # filter by score
    idx1 = np.where(scores1 >= threshold)[0]
    idx2 = np.where(scores2 >= threshold)[0]
    sel1 = boxes1[idx1] if idx1.size>0 else np.zeros((0,4))
    sel2 = boxes2[idx2] if idx2.size>0 else np.zeros((0,4))
    # compute match counts
    matched = 0
    for b in sel1:
        for b2 in sel2:
            if iou(b, b2) >= iou_match_thr:
                matched += 1
                break
    rows.append((p.name, len(sel1), len(sel2), matched, float(scores1.max() if scores1.size>0 else 0.0), float(scores2.max() if scores2.size>0 else 0.0)))

with open(out_csv, 'w', encoding='utf-8') as f:
    f.write('image,orig_count,quant_count,matched,orig_top,quant_top\n')
    for r in rows:
        f.write(','.join(map(str,r)) + '\n')

print('Quant regression complete. Report:', out_csv)
