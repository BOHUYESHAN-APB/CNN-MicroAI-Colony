# Faster R-CNN ResNet50 模型训练说明

## 文件结构
```
faster_rcnn_resnet50/
├── src/
│   ├── train.py            # 训练主程序
│   ├── evaluate.py         # 评估脚本
│   ├── data/               # 数据加载处理
│   ├── models/             # 模型定义
│   └── ops/                # 自定义操作
├── checkpoints/            # 模型检查点
├── configs/                # 配置文件
└── README.md               # 说明文档
```

## 训练特性
- **中断恢复**：支持从任意检查点恢复训练
- **详细日志**：记录每个epoch的训练指标
- **硬件监控**：GPU内存和利用率跟踪

## 使用说明
```bash
# 开始训练
python src/train.py

# 恢复训练
python src/train.py --resume checkpoints/latest.pth
```

## 评估指标
| Epoch | Train Loss | Val Error | LR     |
|-------|------------|-----------|--------|
| 1     | 1.254      | 0.85      | 0.001  | 
| 10    | 0.876      | 0.72      | 0.001  |
| 20    | 0.654      | 0.68      | 0.0005 |