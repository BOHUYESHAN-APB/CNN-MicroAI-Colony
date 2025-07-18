# YOLOv8 菌落检测模型

## 目录结构说明
- `src/`: 训练和评估源代码
  - `train.py`: 主训练脚本
  - `eval.py`: 评估脚本
  - `data/`: 数据加载和处理
  - `models/`: 模型定义
- `configs/`: 训练配置文件
- `checkpoints/`: 模型权重保存
- `model_output/`: 训练输出和可视化结果

## 数据集配置
使用COCO格式数据集，需配置：
1. 数据集路径：`/merged_dataset`
2. 类别映射：85个菌落类别
3. 图像尺寸：支持640x640到2048x2048

## 快速开始
```bash
python src/train.py --config configs/yolov8_coco.yaml
```

## 模型特性
- 基于Ultralytics YOLOv8
- 支持多尺度训练
- COCO评估指标