# DetectoRS 菌落检测模型

基于DetectoRS的先进目标检测模型，专为菌落检测任务优化。

## 模型特点

- **递归特征金字塔(RFP)**：增强特征提取能力
- **可切换空洞卷积(SAC)**：自适应感受野调整
- **ResNet50骨干网络**：强大的特征表示
- **多尺度训练**：支持640-2048像素输入

## 目录结构

```
detectors/
├── configs/
│   └── detectors_coco.py             # 模型配置文件
├── src/
│   ├── train.py                      # 训练脚本
│   ├── data/
│   │   └── dataset.py               # 数据集处理
│   └── models/
│       └── colony_detector.py       # 模型定义
├── work_dirs/                       # 训练输出目录
├── checkpoints/                     # 预训练权重
└── README.md
```

## 快速开始

### 1. 环境准备

```bash
pip install mmdet mmcv-full
```

### 2. 数据准备

确保数据集结构如下：
```
/merged_dataset/
├── train/
├── val/
├── test/
└── annotations/
    ├── instances_train.json
    ├── instances_val.json
    └── instances_test.json
```

### 3. 开始训练

```bash
cd src
python train.py
```

### 4. 断点续训

```bash
python train.py --resume checkpoints/latest.pth
```

## 训练参数

- **输入尺寸**: [640, 2048] 多尺度
- **批次大小**: 2 images/GPU
- **学习率**: 0.02 (SGD)
- **训练周期**: 12 epochs
- **骨干网络**: ResNet50 + RFP + SAC

## 性能指标

| 指标 | 值 |
|------|-----|
| mAP@0.5 | 待训练 |
| mAP@0.5:0.95 | 待训练 |
| 推理速度 | 待测试 |

## 模型架构

```
输入图像
    ↓
ResNet50 + RFP (递归特征金字塔)
    ↓
SAC (可切换空洞卷积)
    ↓
FPN特征金字塔
    ↓
RPN区域建议网络
    ↓
Cascade R-CNN检测头
    ↓
最终检测结果
```

## 创新点

1. **RFP (Recursive Feature Pyramid)**: 通过递归结构增强特征表示
2. **SAC (Switchable Atrous Convolution)**: 动态调整感受野大小
3. **联合优化**: 检测和分割任务联合训练
4. **多任务学习**: 支持边界框和掩码预测

## 注意事项

1. 需要较大的GPU内存（建议8GB+）
2. 训练时间相对较长
3. 确保CUDA环境配置正确
4. 训练前检查数据集路径

## 相关链接

- [DetectoRS论文](https://arxiv.org/abs/2006.02334)
- [MMDetection文档](https://mmdetection.readthedocs.io/)