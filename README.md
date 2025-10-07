# 智能菌落分析和抑菌圈检测系统

![项目图标](docs/image/logo.png)

> 注意：这是新版本的开发分支。如需查看原有版本，请参考 [README_OLD.md](README_OLD.md)。

## 项目简介

新一代智能菌落分析和抑菌圈检测系统，基于百度PP-YOLO深度学习框架进行优化，实现高精度菌落计数、抑菌圈测量和形态分析。系统专注于PP-YOLO算法的改进和应用，提供现代化的用户界面和丰富的分析功能。

**重要说明**：本项目已停止多模型性能比较工作，专注于百度PP-YOLO框架的优化和应用。

## 功能特点

### 菌落分析
- 高精度菌落检测和计数
- 实时相机预览和图像采集
- 基于PP-YOLO的优化检测算法
- 批量处理功能

### 抑菌圈检测
- 培养皿自动识别
- 主次抑菌圈测量
- 重叠区域分析
- 标准测量和校准
- 手动标注功能

### 数据分析
- 自动生成分析报告
- 多种数据可视化方式
- 测量数据导出
- 历史记录管理

### 界面特性
- 现代化三栏式布局
- 图像预览和缩放
- 实时测量反馈
- 中英文界面切换
- 文件管理系统

## 项目结构

```
colony-analysis/
├── opencv-circle-detection/     # 抑菌圈检测模块
│   ├── core/                   # 核心功能模块
│   │   ├── detector.py        # 检测算法实现
│   │   ├── models.py          # 数据模型定义
│   │   └── processor.py       # 图像处理功能
│   ├── gui/                    # 图形界面模块
│   │   ├── main_window.py     # 主窗口实现
│   │   ├── image_view.py      # 图像查看器
│   │   └── report_view.py     # 报告显示模块
│   └── utils/                  # 工具类模块
├── models-colony-counting/     # 菌落计数模块
└── docs/                      # 项目文档
    ├── guides/                # 用户指南
    ├── development/          # 开发文档
    └── technical/            # 技术规格
```

## 环境配置

### 系统要求
- Python 3.9 或更高版本
- OpenCV 4.5.0 或更高版本
- PySide6 6.0.0 或更高版本

### 安装步骤
```bash
# 1. 克隆仓库
git clone https://github.com/yourusername/colony-analysis-system.git
cd colony-analysis-system

# 2. 创建虚拟环境
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/macOS 
source venv/bin/activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 运行程序
python main.py
```

## 使用说明

1. 打开图像：
   - 点击"打开图像"按钮
   - 通过左侧资源管理器选择
   - 支持拖拽导入

2. 检测功能：
   - 自动检测培养皿
   - 识别主次抑菌圈
   - 分析重叠区域
   - 添加标注信息

3. 结果查看：
   - 可视化显示结果
   - 测量数据统计
   - 生成分析报告

4. 数据导出：
   - 保存分析图像
   - 导出测量数据
   - 生成PDF报告

## 文档

- [用户指南](docs/guides/USER_GUIDE.md)
- [开发文档](docs/development/DEVELOPMENT_GUIDE.md)
- [技术规格](docs/technical/TECHNICAL_SPECS.md)
- [PP-YOLO优化文档](docs/technical/PPYOLO_OPTIMIZATION.md)
- [历史版本](README_OLD.md)

## 许可证

[Apache-2.0 license](LICENSE)

## 贡献指南

我们欢迎任何形式的贡献，包括但不限于：
- 代码改进
- 文档完善
- 问题报告
- 功能建议

请通过以下方式参与项目：
1. Fork 本仓库
2. 创建您的特性分支
3. 提交您的改动
4. 推送到您的分支
5. 创建Pull Request

## 联系方式

- 问题反馈：GitHub Issues
- 技术支持：project@example.com
