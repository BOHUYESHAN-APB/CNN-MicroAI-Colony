# PP-YOLO 菌落检测模型

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
使用COCO格式数据集，与YOLOv8保持一致：
1. 数据集路径：`/merged_dataset`
2. 多尺度训练：[640, 1280]范围
3. 相同数据增强策略

## 快速开始
```bash
python src/train.py --config configs/ppyolo_coco.yaml
```

## 模型特性
- 基于PaddleDetection PP-YOLO
- 多尺度训练支持
- 与YOLOv8相同的评估指标