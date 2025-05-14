# 智能菌落分析系统 V2 (Colony Analysis System)

![项目图标](docs/image/logo.png)

> 注意：这是新版本的开发分支。如需查看原有版本，请参考 [README_OLD.md](README_OLD.md)。

## 项目简介

新一代智能菌落分析系统，基于深度学习技术实现高精度菌落计数和形态分析，支持多平台部署。相比原有版本，新版本采用了更现代化的技术栈，提供了更好的跨平台支持和用户体验。

## 功能特点

- 多平台支持
  - 移动端：Android/iOS应用
  - 桌面端：Windows/macOS/Linux
  - Web端：支持现代浏览器访问
- 增强的检测功能
  - 高精度菌落检测和计数
  - 实时相机预览
  - 水平仪功能（倾斜度检测）
  - 5度以内绿色边框提示
- AI增强分析
  - 兼容OpenAI API格式
  - 支持本地AI模型(Ollama/LM Studio)
  - AI辅助报告生成
- 数据管理
  - 自定义历史记录存储
  - 工程文件管理系统
  - 多格式导出(JSON/CSV/Excel/PDF/Markdown)
- 界面优化
  - iOS风格简洁设计
  - 自适应布局
  - 暗黑模式支持
  - 手势操作支持

## 新版目录结构

```
colony-next/
├── frontend/                 # Tauri + React前端
│   ├── src/
│   │   ├── components/      # UI组件
│   │   ├── layouts/         # 布局组件
│   │   └── pages/          # 页面
├── backend/                 # Python FastAPI后端
│   ├── core/               # 核心功能
│   ├── api/                # API接口
│   └── services/           # 业务服务
└── docs/                   # 项目文档
```

## 环境配置

```bash
# 1. 克隆仓库
git clone https://github.com/yourusername/colony-analysis-system.git
cd colony-analysis-system

# 2. 后端配置
cd backend
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/macOS 
source venv/bin/activate
pip install -r requirements.txt

# 3. 前端配置
cd ../frontend
npm install

# 4. 启动开发服务
# 终端1: 后端服务
cd backend
python main.py

# 终端2: 前端开发服务
cd frontend
npm run tauri dev
```

## 技术栈

- 前端：
  - Tauri (跨平台应用框架)
  - React (UI框架)
  - TypeScript (类型安全)
- 后端：
  - Python FastAPI (API服务)
  - PyTorch (AI模型)
  - SQLite (数据存储)
- AI集成：
  - OpenAI API 兼容接口
  - Ollama 本地模型支持
  - LM Studio 本地模型支持

## 文档

- [部署指南](docs/deployment/)
- [开发文档](docs/development/)
- [API参考](docs/api/)
- [用户指南](docs/guides/)
- [历史版本](README_OLD.md)

## 开源协议

[MIT License](LICENSE)

## 联系我们

- 问题报告: GitHub Issues
- 邮件: project@example.com
