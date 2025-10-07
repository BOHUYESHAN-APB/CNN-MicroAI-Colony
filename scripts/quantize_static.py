from pathlib import Path
import numpy as np
import cv2
from onnxruntime.quantization import CalibrationDataReader, quantize_static, QuantFormat, QuantType

repo_root = Path(__file__).resolve().parents[1]
src = repo_root / 'models-train' / 'in-use' / 'old' / 'faster_rcnn_resnet50' / 'checkpoint_epoch_31.onnx'
dst = repo_root / 'onnx model' / 'checkpoint_epoch_31.static_qdq.onnx'
test_dir = repo_root / 'test-pic'

def preprocess_image(path, size=800):
    img = cv2.imread(str(path))
    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = cv2.resize(rgb, (size,size)).astype('float32')/255.0
    mean = np.array([0.485,0.456,0.406]); std=np.array([0.229,0.224,0.225])
    img = (img - mean)/std
    img = np.transpose(img, (2,0,1))
    return img[np.newaxis, ...].astype('float32')

class SimpleDataReader(CalibrationDataReader):
    def __init__(self, input_name, image_paths):
        self.input_name = input_name
        self.image_paths = image_paths
        self.data_iter = iter(self.image_paths)

    def get_next(self):
        try:
            p = next(self.data_iter)
        except StopIteration:
            return None
        arr = preprocess_image(p)
        return {self.input_name: arr}

if not src.exists():
    print('Source ONNX not found:', src); raise SystemExit(1)
if not test_dir.exists():
    print('Test images not found', test_dir); raise SystemExit(1)

from onnxruntime import InferenceSession
sess = InferenceSession(str(src))
input_name = sess.get_inputs()[0].name
image_paths = list(test_dir.glob('*.jpg'))[:20]
reader = SimpleDataReader(input_name, image_paths)
print('Running static quantization with', len(image_paths), 'calibration images...')
quantize_static(str(src), str(dst), reader, quant_format=QuantFormat.QDQ, per_channel=False, activation_type=QuantType.QUInt8, weight_type=QuantType.QInt8)
print('Static QDQ quantized model saved to', dst)
