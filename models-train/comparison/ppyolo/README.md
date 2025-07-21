# PP-YOLO 菌落检测模型

## 目录结构
```
ppyolo/
├── README.md           # 模型说明文档
├── checkpoints/        # 训练检查点
├── configs/            # 配置文件
├── model_output/       # 最终模型输出
└── src/
    ├── data/           # 数据相关
    │   └── dataset.py  # 数据加载和预处理
    ├── models/         # 模型定义
    │   └── ppyolo.py   # PP-YOLO模型架构
    ├── train.py        # 主训练脚本
    └── utils/          # 工具函数
```

## 训练说明
- 配置文件位置: configs/ppyolo_coco.yaml
- 训练命令: python src/train.py --config configs/ppyolo_coco.yaml
- 数据集路径: /merged_dataset/

## 复现说明
- 如需验证旧版模型训练，请切换至`main_old`分支
- 本目录结构为标准模板，其他对比模型需保持相同结构

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