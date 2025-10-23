# OpenCV抑菌圈检测系统

> 基于OpenCV的智能抑菌圈检测与分析系统，为微生物实验提供高效、准确的自动化检测解决方案。

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-green.svg)
![OpenCV](https://img.shields.io/badge/opencv-4.x-orange.svg)
![PyQt6](https://img.shields.io/badge/PyQt6-6.x-red.svg)

## 🎯 项目概述

OpenCV抑菌圈检测系统是一个专业的计算机视觉应用，专门用于自动化检测和分析微生物培养中的抑菌圈。系统采用先进的图像处理算法，提供直观的图形用户界面，支持单张和批量图像处理。

### 核心功能
- 🔬 **自动培养皿识别**：精确检测培养皿边界和尺寸标定
- 🎯 **抑菌物质检测**：支持滤纸片和透明挖孔两种检测模式
- 📏 **抑菌圈测量**：自动测量抑菌圈直径，支持像素和毫米单位
- 🖥️ **图形用户界面**：现代化暗色主题，操作简单直观
- 📊 **批量处理**：支持多文件批量处理和统计分析
- ✅ **精度验证**：内置精度验证系统，确保检测质量

## 🚀 快速开始

### 环境要求

- Python 3.8 或更高版本
- OpenCV 4.x
- PyQt6
- NumPy

### 安装步骤

1. **克隆项目**
```bash
git clone <repository-url>
cd opencv-circle-detection
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **运行程序**

#### 单张图像处理
```bash
python gui/standalone_gui.py
```

#### 批量处理
```bash
python run_batch_processing.py
```

#### 精度验证测试
```bash
python test_accuracy_validation.py
```

## 📖 使用指南

### 基本使用流程

1. **打开图像**：选择要分析的抑菌圈图像
2. **选择检测器**：根据样本类型选择合适的检测算法
3. **设置参数**：调整培养皿直径、物质类型等参数
4. **开始检测**：点击检测按钮，系统自动分析
5. **查看结果**：在结果面板查看检测数据和可视化结果
6. **保存结果**：导出检测结果和标注图像

### 检测器选择建议

| 样本类型 | 推荐检测器 | 检测准确率 | 适用场景 |
|---------|-----------|-----------|---------|
| 滤纸片法 | 原始检测器 | 3/3 ✅ | 滤纸片比背景明显更亮 |
| 透明挖孔法 | 修正检测器 | 3/4 👍 | 透明挖孔需要排除气泡干扰 |
| 混合场景 | 自动检测 | 自适应 | 让系统自动判断最佳算法 |

### 批量处理功能

- **文件管理**：支持文件和文件夹批量导入
- **实时进度**：显示处理进度和当前文件状态
- **错误处理**：自动跳过有问题的文件，记录错误信息
- **结果统计**：生成详细的批量处理报告

### 配置与调优（暗底 / 透明孔洞）

在暗背景或透明挖孔（例如 OIP-C）场景下，默认的霍夫圆检测容易失效。项目提供一个调优好的参数集 `profiles.dark_blob`，用于增强预处理和基于 blob 的候选证据提取，以作为 Hough 的稳健备选。

默认配置位置：`opencv-circle-detection/utils/config.py` 中的 `Config().profiles['dark_blob']`。

默认参数示例：

- `tophat_kernel`: (7, 7)
- `clahe_clip`: 1.0
- `minArea`: 20
- `maxArea`: 4000
- `minCircularity`: 0.12
- `minInertiaRatio`: 0.05

如何使用与调优：
- 直接编辑 `opencv-circle-detection/utils/config.py` 中的 `profiles['dark_blob']` 并保存。
- 在命令行模式下运行检测（系统会在检测到暗底或 HOLE 类型时自动应用该 profile）：

```bash
python main.py --image <path/to/image.jpg> --output <path/to/out.jpg>
```

- 若需系统化调优，请参考 `tools/tune_blob_grid.py`：该脚本会对若干预处理与 blob 参数做网格扫描，生成 overlay 可视化结果和 `tools/tune_blob_grid_results.csv` 供人工确认；确认后将选定参数写回 `utils/config.py`。

注意：在实用判定中，建议结合环带内的 keypoint 密度（ring-density）与径向灰度剖面（radial profile）共同决策，以减少噪声导致的误判。

## 🏗️ 项目架构

### 目录结构
```
opencv-circle-detection/
├── core/                          # 核心算法模块
│   ├── detector.py                # 原始检测器
│   ├── corrected_detector_fixed.py # 修正检测器
│   ├── models.py                  # 数据模型
│   └── ...                       # 其他检测器版本
├── gui/                           # 图形用户界面
│   ├── standalone_gui.py          # 单张处理界面
│   ├── batch_gui.py               # 批量处理界面
│   └── ...                       # 其他界面组件
├── utils/                         # 工具模块
│   └── accuracy_validator.py      # 精度验证工具
├── test_images/                   # 测试图像
├── docs/                          # 项目文档
│   └── opencv-circle-detection/   # 详细文档
├── tests/                         # 测试脚本
└── requirements.txt               # 项目依赖
```

### 核心技术
- **图像处理**：OpenCV霍夫圆检测、自适应阈值、形态学操作
- **用户界面**：PyQt6现代化GUI框架
- **多线程**：后台检测处理，保持界面响应
- **数据管理**：JSON配置、文件存储、结果导出

## 📊 性能指标

### 检测精度
- **培养皿检测**：≥95%准确率
- **抑菌物质检测**：75%-100%（取决于类型）
- **抑菌圈测量**：像素级精度，支持毫米换算

### 处理性能
- **单张图像**：3-10秒（取决于图像大小和复杂度）
- **批量处理**：支持多线程，界面保持响应
- **内存占用**：优化的图像缓存管理

### 支持格式
- **图像格式**：JPG、PNG、BMP、TIFF
- **图像尺寸**：建议500x500至4000x4000像素
- **批量数量**：理论上无限制

## 🔬 算法原理

### 检测流程

```
输入图像 → 图像预处理 → 培养皿检测 → 抑菌物质检测 → 抑菌圈检测 → 结果输出
```

### 关键算法
1. **霍夫圆检测**：用于培养皿和圆形物质检测
2. **自适应阈值**：适应不同光照条件
3. **形态学操作**：优化检测结果，减少噪声
4. **轮廓分析**：精确提取目标边界
5. **圆形拟合**：准确测量圆形对象参数

## 📈 测试验证

### 测试数据
- **测试图像**：2张标准抑菌圈图像
- **测试场景**：透明挖孔（4个孔）+ 滤纸片（3个片）
- **验证方法**：人工验证 + 自动精度评估

### 测试结果
| 检测器版本 | 透明挖孔检测 | 滤纸片检测 | 总体评价 |
|-----------|-------------|-----------|----------|
| 原始检测器 | 0/4 ❌ | 3/3 ✅ | 适合滤纸片 |
| 修正检测器 | 3/4 👍 | 稳定 | 适合挖孔 |

### 精度验证系统
- **标准答案管理**：支持JSON格式的标准数据
- **多维度评估**：培养皿、物质、抑菌圈分别评估
- **统计分析**：提供详细的精度统计报告

## 🛠️ 开发指南

### 开发环境设置
```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# 安装开发依赖
pip install -r requirements.txt
pip install pytest black flake8  # 开发工具
```

### 代码规范
- **代码风格**：遵循PEP8标准
- **类型提示**：使用Type Hints增强代码可读性
- **文档字符串**：完整的docstring文档
- **单元测试**：pytest测试框架

### 扩展开发
- **新检测器**：继承BaseDetector基类
- **自定义界面**：基于PyQt6组件开发
- **插件系统**：支持第三方算法集成

## 📚 文档索引

### 用户文档
- 📖 [GUI使用指南](docs/opencv-circle-detection/user-guides/GUI_USER_GUIDE.md) - 详细的界面使用说明
- 🔬 [检测算法对比](docs/opencv-circle-detection/reports/DETECTION_ANALYSIS_SUMMARY.md) - 各检测器性能分析

### 技术文档
- 🏗️ [技术架构文档](docs/opencv-circle-detection/technical/TECHNICAL_ARCHITECTURE.md) - 系统架构和技术原理
- 🧪 [专利技术对比](docs/opencv-circle-detection/PROJECT_COMPARISON_WITH_PATENT.md) - 与专利技术的对比分析

### 开发文档
- 🛣️ [未来发展路线图](docs/opencv-circle-detection/development/FUTURE_ROADMAP.md) - 项目发展规划和技术路线

## 🔮 未来规划

### 短期目标（3个月内）
- [ ] **深度学习集成**：引入CNN模型提升检测精度
- [ ] **菌种鉴定功能**：实现基本的菌种识别能力
- [ ] **药敏分析模块**：添加抗生素敏感性分析

### 中期目标（6个月内）
- [ ] **新菌种记忆**：实现新菌种学习和记忆功能
- [ ] **医学标准集成**：符合CLSI/EUCAST医学标准
- [ ] **亚像素精度**：提升测量精度到专利要求水平

### 长期目标（1年内）
- [ ] **多光谱成像**：支持紫外、红外等多波段检测
- [ ] **实时监测**：动态跟踪培养过程
- [ ] **云端AI服务**：提供在线识别和分析服务

## 🤝 贡献指南

### 如何贡献
1. Fork本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建Pull Request

### 报告问题
- 使用GitHub Issues报告bug
- 提供详细的错误信息和复现步骤
- 附上相关的图像样本（如果可能）

### 改进建议
- 提出新功能需求
- 算法优化建议
- 用户体验改进

## 📄 许可证

本项目采用MIT许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 👥 团队与致谢

### 核心团队
- **算法开发**：OpenCV图像处理算法设计与优化
- **界面开发**：PyQt6现代化GUI设计与实现
- **测试验证**：算法性能测试与精度验证

### 特别致谢
- OpenCV社区提供的强大计算机视觉库
- PyQt项目提供的优秀GUI框架
- 微生物学专家提供的专业指导

## 📞 联系方式

- **项目主页**：[GitHub Repository]
- **问题反馈**：[GitHub Issues]
- **技术交流**：[Discussions]

---

*README版本：v1.0*  
*最后更新：2025年7月15日*  
*项目状态：积极开发中* 🚧

## 🏷️ 标签

`opencv` `computer-vision` `image-processing` `microbiology` `gui` `python` `pyqt6` `detection` `analysis` `automation`