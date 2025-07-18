# 菌落检测模型选择指南

## 📋 模型分类与选择策略

### 1. 传统 & 多阶段检测器

| 模型 | 备注 | 是否纳入 | 状态 |
|------|------|----------|------|
| **Faster R-CNN + ResNet50** | 你的基线 | ✅ 必测 | ✅ 已完成 |
| **Faster R-CNN + ResNet101/FPN** | backbone 深度/多尺度 | ✅ 建议 | ✅ 已完成 |
| **Cascade R-CNN** | 多阶段细化 | ✅ 建议 | ✅ 已完成 |
| **Mask R-CNN** | 形态学分割 | ✅ 建议 | ✅ 已完成 |
| **HTC (Hybrid Task Cascade)** | 检测+分割级联 | ✅ 建议 | ✅ 已完成 |
| **DetectoRS** | 递归特征+空洞卷积 | ✅ 可选 | ✅ 已完成 |

### 2. 单阶段 & 轻量检测器

| 模型 | 备注 | 是否纳入 | 状态 |
|------|------|----------|------|
| **YOLOv5-N/S** | 超轻量，边缘快 | ✅ 可选 | ✅ 已完成 |
| **YOLOv8-N/S/M** | Anchor-Free 平衡 | ✅ 必测 | ✅ 已完成 |
| **YOLOv11-N/S** | Paddle 官方移植 | ✅ 建议 | ✅ 已完成 |
| **YOLOv12-S** | FlashAttention | ✅ 建议 | ✅ 已完成 |
| **YOLOv13-N/S** | HyperACE SOTA | ✅ 必测 | ✅ 已完成 |

### 3. 菌落计数专用 / 其它方法

| 模型 | 备注 | 是否纳入 | 状态 |
|------|------|----------|------|
| **U-Net + Counting** | 分割后计数 | ✅ 建议 | ✅ 已完成 |
| **CSRNet（密度图）** | 密集场景回归 | ✅ 可选 | ❌ 待添加 |
| **CNN-MicroAI-Colony** | 本仓库专用 | ✅ 必测 | ✅ 已完成 |

### 4. 国产框架 & 算力适配

| 框架/模型 | 量化/加速 | 硬件 | 是否纳入 | 状态 |
|-----------|-----------|------|----------|------|
| **PP-YOLO-E (PaddleDetection)** | INT8/FP16 | GPU / 昆仑 / DCU | ✅ 必测 | ✅ 已完成 |
| **YOLOv8-Ascend (MindSpore)** | OM 离线模型 | Ascend 910B | ✅ 必测 | ❌ 待适配 |
| **TinyMS-YOLO** | INT8 | Atlas 200 DK | ✅ 边缘场景 | ❌ 待添加 |
| **PaddleSlim 量化** | 蒸馏+稀疏 | 通用 | ✅ 量化对比 | ❌ 待添加 |

## 🎯 最小可行实验组合（推荐直接开跑）

| 对比组 | 目的 | 状态 |
|--------|------|------|
| **Faster R-CNN vs PP-YOLO-E vs YOLOv8** | 基线 vs 国产 SOTA vs 主流 | ✅ 就绪 |
| **YOLOv8-N vs YOLOv13-N** | 轻量模型代际差异 | ✅ 就绪 |
| **HTC vs Mask R-CNN vs U-Net** | 形态学/分割能力 | ✅ 就绪 |
| **PP-YOLO-E@GPU vs PP-YOLO-E@Ascend910B** | 同模型跨国产芯片性能 | ❌ 待硬件 |

## 📊 模型性能预期对比

### 精度预期（mAP@0.5）
- **传统检测器**: 85-92%
- **单阶段检测器**: 82-90%
- **分割模型**: 88-94%
- **轻量模型**: 75-85%

### 速度预期（FPS @ 640×640）
- **传统检测器**: 5-15 FPS
- **单阶段检测器**: 20-60 FPS
- **轻量模型**: 50-200 FPS
- **分割模型**: 3-10 FPS

### 内存占用（训练时）
- **ResNet50系列**: 4-8GB
- **ResNet101系列**: 6-12GB
- **轻量YOLO**: 2-4GB
- **DetectoRS**: 8-16GB

## 🚀 快速开始实验

### 实验1：基线对比
```bash
# 传统检测器
cd models-train/comparison/faster_rcnn_resnet50 && python src/train.py

# 单阶段检测器
cd models-train/comparison/yolov8 && python src/train.py

# 国产框架
cd models-train/comparison/ppyolo && python src/train.py
```

### 实验2：精度对比
```bash
# 多阶段细化
cd models-train/comparison/cascade_rcnn && python src/train.py

# 分割能力
cd models-train/comparison/mask_rcnn && python src/train.py
cd models-train/comparison/unet && python src/train.py
```

### 实验3：轻量模型
```bash
# 轻量YOLO对比
cd models-train/comparison/yolov5 && python src/train.py
cd models-train/comparison/yolov13 && python src/train.py
```

## 📈 实验结果记录模板

| 模型 | mAP@0.5 | mAP@0.5:0.95 | FPS | 参数量 | 训练时间 | 备注 |
|------|---------|--------------|-----|---------|----------|------|
| Faster R-CNN-R50 | - | - | - | - | - | 基线 |
| YOLOv8-S | - | - | - | - | - | 平衡 |
| PP-YOLO-E | - | - | - | - | - | 国产 |
| ... | ... | ... | ... | ... | ... | ... |

## 🔧 下一步扩展计划

1. **CSRNet密度图模型** - 添加密集计数能力
2. **国产芯片适配** - Ascend 910B/MindSpore版本
3. **量化对比实验** - INT8/FP16性能测试
4. **边缘设备部署** - Atlas 200 DK优化版本

## ✅ 当前完成状态

- **已完成**: 12个核心模型架构
- **已就绪**: 传统检测器、YOLO系列、分割模型
- **待添加**: CSRNet、国产芯片适配、量化版本
- **立即可用**: 基线对比实验组合