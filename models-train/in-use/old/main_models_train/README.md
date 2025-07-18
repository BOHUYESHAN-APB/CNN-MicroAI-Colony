# Main Models 训练框架说明

## 文件结构
```
main_models_train/
├── src/
│   ├── train.py            # 训练主程序
│   ├── tools/              # 辅助工具
│   │   ├── dataset_preprocessor.py
│   │   └── performance_estimator.py
├── configs/                # MMDetection配置文件
│   ├── faster_rcnn_colony.py  
│   └── retinanet_colony.py
├── work_dirs/              # 训练输出
│   ├── metrics.json        # 训练指标
│   └── checkpoints/        # 模型保存点
└── README.md               # 说明文档
```

## 核心特性
- **模块化设计**：基于MMDetection框架
- **灵活配置**：支持多种检测模型
- **生产级训练**：分布式训练支持
- **完整评估**：内置验证和测试流程

## 训练参数
```bash
# 标准训练
python src/train.py configs/faster_rcnn_colony.py

# 恢复训练 
python src/train.py configs/faster_rcnn_colony.py --resume-from work_dirs/latest.pth

# 性能测试
python src/tools/performance_estimator.py --config configs/faster_rcnn_colony.py
```

## 性能指标
| 模型类型       | mAP@0.5 | 推理速度(FPS) | 显存占用 |
|----------------|---------|--------------|---------|
| Faster R-CNN   | 0.92    | 24.5         | 5.8GB   |
| RetinaNet      | 0.89    | 31.2         | 4.2GB   |