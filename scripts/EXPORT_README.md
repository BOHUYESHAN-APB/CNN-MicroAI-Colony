导出 Faster R-CNN 检查点为 ONNX

使用本目录下的 `export_fasterrcnn_to_onnx.py` 脚本可以把 PyTorch 的 Faster R-CNN checkpoint (.pth) 导出为 ONNX 模型，方便在安卓/其他平台中使用（配合 ONNX Runtime、OpenVINO 或转换成 TensorFlow Lite 等）。

示例（Windows PowerShell）：

```powershell
# 导出第一个模型
python .\scripts\export_fasterrcnn_to_onnx.py \
  --checkpoint d:\train\faster_rcnn_colony_epoch12.pth \
  --output .\models-train\in-use\old\main_models_train\faster_rcnn_colony_epoch12.onnx \
  --device cpu --opset 12 --max-detections 200 --num-classes 2

# 导出第二个模型
python .\scripts\export_fasterrcnn_to_onnx.py \
  --checkpoint d:\train\checkpoint_epoch_31.pth \
  --output .\models-train\in-use\old\faster_rcnn_resnet50\checkpoint_epoch_31.onnx \
  --device cpu --opset 12 --max-detections 200 --num-classes 91
```

说明：
- `--num-classes` 请根据训练时的类别数量设置（包含背景类）。
- `--max-detections` 表示导出时对每帧结果的最大检测数，过小可能截断结果，过大会增大模型输出尺寸。安卓端可按需设置更小的值以优化性能。
- 如果 checkpoint 使用 GPU 保存（包含 CUDA 张量），脚本会用 `map_location` 在 CPU 上加载（除非你指定 `--device cuda` 并在有 GPU 的环境下运行）。
