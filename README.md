# 菌落检测分析系统

## 版本说明
目前项目包含三个版本：

### PyQt5版本 (app-pyqt/)
- 历史版本
- 仅用于研究和学习用途
- 基于PyQt5框架开发

### PySide6版本 (app_pyside6/)
- 当前过渡版本
- 迁移至PySide6框架
- 保持基础功能

### 新版本 (app/)
- 最新开发版本
- 基于PySide6和PyOneDark主题
- 现代化UI设计
- 优化的用户体验
- 更高的性能和稳定性

## 新版本特性
- 全新的深色主题界面
- 流畅的动画效果
- 更好的高DPI支持
- 优化的性能和内存使用
- 模块化的代码结构
- 完整的类型提示
- 全面的错误处理

## 目录结构
```
CNN-/
├── app/                # 新版本（开发中）
│   ├── config/        # 配置文件
│   ├── database/      # 数据库管理
│   ├── font/         # 字体资源
│   ├── gui/          # 图形界面
│   ├── models/       # 模型定义
│   ├── resources/    # 资源文件
│   │   ├── i18n/    # 国际化文件
│   │   └── themes/  # 主题文件
│   ├── templates/    # 报告模板
│   └── utils/       # 工具函数
├── app_pyside6/      # 过渡版本
├── app-pyqt/         # 旧版本
├── docs/            # 文档
└── src/            # 共享源码
```

## 技术栈
- **GUI框架**: PySide6 6.5+
- **主题**: PyOneDark风格
- **深度学习**: PyTorch 2.0+
- **图像处理**: OpenCV 4.8+
- **数据处理**: NumPy, Pandas
- **可视化**: Matplotlib
- **类型检查**: mypy
- **代码质量**: pylint, black
- **测试框架**: pytest

## 新版本安装
```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# 安装依赖
pip install -r requirements.txt

# 运行应用
python -m app.main
```

## 开发说明
- 使用Python 3.9+
- 遵循PEP 8编码规范
- 使用类型注解
- 编写单元测试
- 保持文档更新

## 许可说明
同上，保持双重许可模式：
- 非商业用途: AGPL v3
- 商业用途: 专有许可

## 贡献指南
1. 克隆仓库
2. 创建特性分支
3. 提交变更
4. 推送到分支
5. 创建Pull Request

## 联系方式
- 问题反馈：GitHub Issues
- 功能建议：Discussions
- 安全问题：直接联系维护者

## 更新日志
见 CHANGELOG.md