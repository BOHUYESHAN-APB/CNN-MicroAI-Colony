# 模型对比实验方案

## 模型分类与选型

### 1. 传统 & 多阶段检测器
| 模型 | 备注 | 是否纳入 |
|------|------|----------|
| Faster R-CNN + ResNet50 | 基线模型 | ✅ 必测 |
| Faster R-CNN + ResNet101/FPN | backbone深度/多尺度 | ✅ 建议 |
| Cascade R-CNN | 多阶段细化 | ✅ 建议 |
| Mask R-CNN | 形态学分割 | ✅ 建议 |
| HTC (Hybrid Task Cascade) | 检测+分割级联 | ✅ 建议 |
| DetectoRS | 递归特征+空洞卷积 | ✅ 可选 |

### 2. 单阶段 & 轻量检测器
| 模型 | 备注 | 是否纳入 |
|------|------|----------|
| YOLOv5-N/S | 超轻量，边缘快 | ✅ 可选 |
| YOLOv8-N/S/M | Anchor-Free 平衡 | ✅ 必测 |
| YOLOv11-N/S | Paddle官方移植 | ✅ 建议 |
| YOLOv12-S | FlashAttention | ✅ 建议 |
| YOLOv13-N/S | HyperACE SOTA | ✅ 必测 |

### 3. 菌落计数专用方法
| 模型 | 备注 | 是否纳入 |
|------|------|----------|
| U-Net + Counting | 分割后计数 | ✅ 建议 |
| CSRNet（密度图） | 密集场景回归 | ✅ 可选 |
| CNN-MicroAI-Colony | 本仓库专用 | ✅ 必测 |

### 4. 国产框架 & 算力适配
| 框架/模型 | 量化/加速 | 硬件 | 是否纳入 |
|-----------|----------|------|----------|
| PP-YOLO-E (PaddleDetection) | INT8/FP16 | GPU/昆仑/DCU | ✅ 必测 |
| YOLOv8-Ascend (MindSpore) | OM离线模型 | Ascend 910B | ✅ 必测 |
| TinyMS-YOLO | INT8 | Atlas 200 DK | ✅ 边缘场景 |
| PaddleSlim量化 | 蒸馏+稀疏 | 通用 | ✅ 量化对比 |

## 最小可行实验组合

| 对比组 | 目的 |
|--------|------|
| Faster R-CNN vs PP-YOLO-E vs YOLOv8-Ascend | 基线 vs 国产SOTA vs 国产加速 |
| YOLOv8-N vs YOLOv13-N | 轻量模型代际差异 |
| HTC vs Mask R-CNN vs U-Net | 形态学/分割能力 |
| PP-YOLO-E@GPU vs PP-YOLO-E@Ascend910B | 同模型跨国产芯片性能 |

## 实验准备清单

1. 统一测试集准备：
   - 包含重叠样本
   - 不同光照条件
   - 不同密度分布

2. 训练配置：
   - 使用PaddleDetection/MindSpore官方config
   - 一键训练脚本

3. 量化部署：
   - PaddleSlim工具链INT8量化
   - ATC工具链转换

4. 评估指标：
   - mAP@0.5
   - MAE (平均绝对误差)
   - RMSE (均方根误差) 
   - 单图推理延迟
   - FPS
   - 功耗(W)

## 目录结构规范

```
models-train/in-use/last/
├── faster_rcnn_resnet50/  # 标准结构
├── yolov8/               # YOLOv8结构
├── ppyolo/               # PP-YOLO结构
└── unet/                 # U-Net结构