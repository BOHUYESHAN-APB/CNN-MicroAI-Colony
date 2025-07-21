# YOLOv5 模型训练结构说明

## 目录结构
```
yolov5/
├── README.md           # 模型说明文档
├── checkpoints/        # 训练检查点
├── configs/            # 配置文件
├── model_output/       # 最终模型输出
└── src/
    ├── data/           # 数据相关
    │   └── dataset.py  # 数据加载和预处理
    ├── models/         # 模型定义
    │   └── yolov5.py   # YOLOv5模型架构
    ├── train.py        # 主训练脚本
    └── utils/          # 工具函数
```

## 训练说明
- 配置文件位置: configs/yolov5_coco.yaml
- 训练命令: python src/train.py --config configs/yolov5_coco.yaml
- 数据集路径: /merged_dataset/

## 复现说明
- 如需验证旧版模型训练，请切换至`main_old`分支
- 本目录结构为标准模板，其他对比模型需保持相同结构