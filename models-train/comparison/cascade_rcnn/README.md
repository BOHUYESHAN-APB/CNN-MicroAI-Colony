# Cascade R-CNN 菌落检测模型

基于MMDetection框架的Cascade R-CNN模型，专门用于菌落检测任务。

## 模型特点

- **级联结构**：3个级联检测头，逐步提升检测精度
- **ResNet50骨干网络**：强大的特征提取能力
- **FPN特征金字塔**：多尺度特征融合
- **多尺度训练**：支持640-2048像素输入

## 目录结构

```
cascade_rcnn/
├── README.md           # 模型说明文档
├── checkpoints/        # 训练检查点
├── configs/            # 配置文件
├── model_output/       # 最终模型输出
└── src/
    ├── data/           # 数据相关
    │   └── dataset.py  # 数据加载和预处理
    ├── models/         # 模型定义
    │   └── colony_detector.py  # Cascade R-CNN模型架构
    ├── train.py        # 主训练脚本
    └── utils/          # 工具函数
```

## 训练说明
- 配置文件位置: configs/cascade_rcnn_coco.py
- 训练命令: python src/train.py --config configs/cascade_rcnn_coco.py
- 数据集路径: /merged_dataset/

## 复现说明
- 如需验证旧版模型训练，请切换至`main_old`分支
- 本目录结构为标准模板，其他对比模型需保持相同结构
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
- **优化器**: SGD + momentum 0.9

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
ResNet50骨干网络
    ↓
FPN特征金字塔
    ↓
RPN区域建议网络
    ↓
级联ROI检测头 (3阶段)
    ↓
最终检测结果
```

## 注意事项

1. 确保CUDA环境配置正确
2. 训练前检查数据集路径
3. 建议使用GPU训练
4. 定期保存checkpoint

## 相关链接

- [MMDetection文档](https://mmdetection.readthedocs.io/)
- [Cascade R-CNN论文](https://arxiv.org/abs/1712.00726)