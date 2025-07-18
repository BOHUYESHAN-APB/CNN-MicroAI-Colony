# YOLOv13 菌落检测模型

## 目录结构说明
- `src/`: 训练和评估源代码
  - `train.py`: 主训练脚本（支持断点恢复）
  - `eval.py`: 评估脚本
  - `data/`: 数据加载和处理
  - `models/`: 模型定义
- `configs/`: 训练配置文件
- `checkpoints/`: 模型权重保存
- `model_output/`: 训练输出和可视化结果

## 数据集配置
使用COCO格式数据集，与所有模型保持一致：
1. 数据集路径：`/merged_dataset`
2. 多尺度训练：[640, 2048]范围
3. 支持断点恢复训练

## 快速开始
```bash
python src/train.py --config configs/yolov13_coco.yaml
```

## 模型特性
- 基于Ultralytics YOLOv13
- HyperACE架构优化
- 支持中断/恢复训练
- 可视化训练进度
- CUDA加速