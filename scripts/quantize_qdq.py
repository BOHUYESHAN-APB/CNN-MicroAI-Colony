from pathlib import Path
from onnxruntime.quantization import quantize_dynamic, QuantType, QuantFormat

repo_root = Path(__file__).resolve().parents[1]
src = repo_root / 'models-train' / 'in-use' / 'old' / 'faster_rcnn_resnet50' / 'checkpoint_epoch_31.onnx'
dst = repo_root / 'onnx model' / 'checkpoint_epoch_31.qdq.onnx'
dst.parent.mkdir(parents=True, exist_ok=True)
if not src.exists():
    print('Source ONNX not found:', src); raise SystemExit(1)
print('Quantizing to QDQ format', src, '->', dst)
quantize_dynamic(str(src), str(dst), weight_type=QuantType.QInt8, quant_format=QuantFormat.QDQ)
print('QDQ quantized model saved to', dst)
