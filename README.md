# 菌落检测分析系统

![项目图标](docs/image/logo.png)

## 项目简介

开放源代码的菌落检测分析系统，基于深度学习技术实现高精度菌落计数和形态分析。

当前包含两个实现版本：
1. `apps/app/main.py` - 基于PyQt6的验证性实现，用于功能原型验证
2. `MICROAI-COLONY/` - 主要开发方向，基于Flask的现代化实现

## 快速开始

```bash
# 创建虚拟环境
python -m venv venv

# 激活环境
# Windows
venv\Scripts\activate
# Linux/macOS 
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 启动系统
python MICROAI-COLONY/app.py
```

## 文档目录

- [技术文档](docs/technical/)  
- [模型对比](docs/model_comparisons/)
- [性能报告](docs/performance_reports/)  
- [使用指南](docs/guides/)  
- [开发文档](docs/development/)  
- [模型分析](main_models_train/model_analysis.md)

## 核心功能

- 高精度菌落检测
- 多模型支持(Faster R-CNN, YOLO系列等)
- 批量处理能力
- 结果可视化
- 模型分析评估框架
  - 支持性能指标对比
  - 误差率统计分析
  - 场景适应性评估

## 联系我们

- 问题报告: GitHub Issues
- 讨论区: GitHub Discussions
- 邮件: colony@example.com

## 开源协议

[AGPL-3.0](LICENSE)
