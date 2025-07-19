# Faster R-CNN ResNet101 菌落检测模型

## 概述

本项目实现了基于Faster R-CNN ResNet101架构的菌落检测模型，专门用于微生物菌落的自动识别和定位。

## 项目结构

```
faster_rcnn_resnet101/
├── configs/
│   └── faster_rcnn_resnet101_coco.py      # 模型配置文件
├── src/
│   ├── train.py                           # 训练脚本
│   ├── data/
│   │   └── dataset.py                     # 数据集处理
│   ├── models/
│   │   └── colony_detector.py             # 菌落检测器实现
│   └── utils/                             # 工具函数
├── checkpoints/                           # 模型检查点
├── model_output/                          # 模型输出
└── README.md                             # 项目说明
```

## 环境要求

### 基础依赖
- Python >= 3.7
- PyTorch >= 1.8.0
- torchvision >= 0.9.0
- mmcv-full >= 1.3.0
- mmdetection >= 2.20.0

### 安装命令
```bash
# 安装PyTorch
pip install torch torchvision

# 安装MMCV和MMDetection
pip install mmcv-full -f https://download.openmmlab.com/mmcv/dist/cu111/torch1.8.0/index.html
pip install mmdet

# 安装其他依赖
pip install opencv-python pillow scikit-learn matplotlib seaborn
```

## 数据准备

### 数据集结构
```
/merged_dataset/
├── train/
│   ├── image_001.jpg
│   ├── image_002.jpg
│   └── ...
├── val/
│   ├── image_001.jpg
│   ├── image_002.jpg
│   └── ...
├── test/
│   ├── image_001.jpg
│   ├── image_002.jpg
│   └── ...
└── annotations/
    ├── instances_train.json
    ├── instances_val.json
    └── instances_test.json
```

### 标注格式
使用COCO格式标注，每个标注文件包含：
- `images`: 图像信息
- `annotations`: 标注信息（边界框）
- `categories`: 类别信息（菌落）

## 训练模型

### 单GPU训练
```bash
cd faster_rcnn_resnet101
python src/train.py --config configs/faster_rcnn_resnet101_coco.py --work-dir ./checkpoints
```

### 多GPU训练
```bash
cd faster_rcnn_resnet101
python -m torch.distributed.launch --nproc_per_node=2 src/train.py --config configs/faster_rcnn_resnet101_coco.py --work-dir ./checkpoints
```

### 恢复训练
```bash
python src/train.py --config configs/faster_rcnn_resnet101_coco.py --work-dir ./checkpoints --resume-from ./checkpoints/latest.pth
```

## 模型评估

### 评估指标
- **mAP (mean Average Precision)**: 平均精度均值
- **AP50**: IoU阈值为0.5时的精度
- **AP75**: IoU阈值为0.75时的精度
- **AR (Average Recall)**: 平均召回率

### 评估命令
```bash
python -m mmdetection/tools/test.py configs/faster_rcnn_resnet101_coco.py ./checkpoints/latest.pth --eval bbox
```

## 模型推理

### 单张图像推理
```python
from src.models.colony_detector import ColonyDetector
import cv2

# 加载模型
detector = ColonyDetector(model_path='./checkpoints/latest.pth')

# 读取图像
image = cv2.imread('test_image.jpg')

# 检测菌落
results = detector.detect(image, confidence_threshold=0.5)

# 结果包含:
# - boxes: 边界框坐标
# - scores: 置信度分数
# - labels: 类别标签
# - num_detections: 检测到的菌落数量
```

### 批量推理
```python
# 批量检测
images = [cv2.imread(f'image_{i}.jpg') for i in range(10)]
results = detector.detect_batch(images)
```

## 性能基准

### 训练配置
- **输入尺寸**: 多尺度训练 [640, 2048]
- **优化器**: SGD with momentum
- **学习率**: 0.02 (初始)
- **训练周期**: 12 epochs
- **批量大小**: 2 (per GPU)

### 预期性能
- **训练时间**: ~2-3小时 (单GPU)
- **推理速度**: ~5 FPS (单张图像)
- **mAP**: 85-90% (取决于数据集质量)

## 模型优化

### 超参数调优
- 调整学习率和学习率调度策略
- 优化anchor尺寸和比例
- 调整NMS阈值和置信度阈值

### 数据增强
- 随机水平翻转
- 随机缩放和裁剪
- 颜色抖动
- 高斯模糊

## 故障排除

### 常见问题

1. **CUDA内存不足**
   - 减小批量大小
   - 减小输入图像尺寸
   - 使用梯度累积

2. **训练不收敛**
   - 检查学习率设置
   - 验证数据标注质量
   - 增加训练数据量

3. **检测精度低**
   - 检查anchor设置
   - 增加训练周期
   - 使用数据增强

### 调试工具
```python
# 启用详细日志
import logging
logging.basicConfig(level=logging.DEBUG)

# 可视化训练过程
from src.data.dataset import ColonyDataset
dataset = ColonyDataset('/merged_dataset', split='train')
dataset.visualize_sample(0, 'sample.jpg')
```

## 模型导出

### 导出为ONNX
```python
import torch.onnx

# 导出模型
torch.onnx.export(
    model,
    dummy_input,
    "faster_rcnn_resnet101.onnx",
    export_params=True,
    opset_version=11,
    do_constant_folding=True
)
```

### 导出为TorchScript
```python
# 导出为TorchScript
traced_model = torch.jit.trace(model, dummy_input)
traced_model.save("faster_rcnn_resnet101.pt")
```

## 贡献指南

1. Fork本项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建Pull Request

## 许可证

本项目采用MIT许可证 - 查看 [LICENSE](../LICENSE) 文件了解详情。

## 联系方式

- 项目维护者: [Your Name]
- 邮箱: [your.email@example.com]
- 项目地址: [GitHub Repository URL]

## 更新日志

### v1.0.0 (2024-01-01)
- 初始版本发布
- 支持Faster R-CNN ResNet101架构
- 完整的训练和评估流程
- 支持COCO格式数据集