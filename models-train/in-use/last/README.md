# 模型训练说明

## 训练文件说明
`combined_model_train.py` 是结合了 Faster R-CNN 和 MMDetection 优点的训练脚本，具有以下特点：

- **中断/恢复训练**：支持从检查点恢复训练
- **详细日志记录**：记录每个epoch的训练指标
- **灵活配置**：通过命令行参数控制训练过程

## 训练参数说明

| 参数 | 默认值 | 说明 |
|------|--------|------|
| config | 无 | 训练配置文件路径 |
| work-dir | 自动生成 | 工作目录 |
| resume-from | 无 | 恢复训练的检查点路径 |
| epochs | 50 | 训练总轮数 |
| save-interval | 1 | 每隔多少轮保存一次检查点 |
| seed | None | 随机种子 |
| gpu-ids | None | 使用的GPU ID |

## 训练指标记录
训练过程中会生成以下文件：
- `metrics_history.json`：记录每个epoch的训练指标
- `training.log`：详细训练日志
- `checkpoint_epoch_{N}.pth`：模型检查点

## 目录结构
```
models-train/in-use/last/
├── combined_model_train.py  # 训练脚本
├── README.md               # 说明文件
├── configs/                # 配置文件目录
└── work_dirs/              # 训练输出目录
    ├── metrics_history.json
    ├── training.log
    └── checkpoint_*.pth
```

## 使用示例
```bash
# 开始新训练
python combined_model_train.py configs/faster_rcnn.py --work-dir work_dirs/exp1

# 恢复训练
python combined_model_train.py configs/faster_rcnn.py --resume-from work_dirs/exp1/checkpoint_epoch_10.pth