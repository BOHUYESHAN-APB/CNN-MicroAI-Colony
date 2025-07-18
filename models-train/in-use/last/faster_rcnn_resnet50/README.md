# Faster R-CNN ResNet50 模型训练结构说明

## 分支说明
- `main`分支：当前标准训练流程
- `main_old`分支：旧版训练代码存档

## 目录结构
```
faster_rcnn_resnet50/
├── src/                  # 源代码目录
│   ├── train.py          # 主训练脚本
│   ├── data/            # 数据相关
│   │   └── dataset.py   # 数据加载和预处理
│   └── models/          # 模型定义
│       └── colony_detector.py  # 模型架构
├── checkpoints/         # 训练检查点
├── model_output/        # 最终模型输出
└── logs/                # 训练日志
```

## 训练说明
1. 准备数据：
   - 将训练图片放入 `data/images/`
   - 标注文件放入 `data/annotations/`

2. 开始训练：
```bash
python src/train.py
```

3. 输出文件：
   - 训练完成的模型保存在 `model_output/`
   - 训练日志在 `logs/training.log`

## 复现说明
- 如需验证旧版模型训练，请切换至`main_old`分支
- 本目录结构为标准模板，其他对比模型需保持相同结构