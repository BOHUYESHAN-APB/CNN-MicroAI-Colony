# 使用指南 / Usage Guide

[中文](#使用说明) | [English](#usage-instructions)

## 使用说明

### 1. 存储空间检查和优化

#### 1.1 运行分析脚本
```shell
# Windows系统:
python scripts\analyze_repo.py .

# Linux/macOS系统:
python scripts/analyze_repo.py .
```

分析脚本会生成以下内容：
- analysis_report.txt - 分析报告
- cleanup_script.{bat|sh} - 清理脚本
- backup/ - 备份目录

#### 1.2 检查分析报告
```shell
# Windows系统:
type analysis_report.txt

# Linux/macOS系统:
cat analysis_report.txt
```

报告包含：
- 文件大小统计
- 文件分类信息
- 清理建议

#### 1.3 执行安全清理
Windows系统:
```batch
:: 1. 创建备份
mkdir backup
robocopy . backup /MIR /XD backup

:: 2. 检查清理脚本内容
type cleanup_script.bat

:: 3. 执行清理
:: 在CMD中运行:
cleanup_script.bat

:: 或在PowerShell中运行:
.\cleanup_script.bat
```

Linux/macOS系统:
```bash
# 1. 创建备份
mkdir -p backup
rsync -av --exclude 'backup' . backup/

# 2. 检查清理脚本内容
cat cleanup_script.sh

# 3. 执行清理
bash cleanup_script.sh
```

### 2. 开发环境设置

#### 2.1 环境准备
Windows系统:
```batch
:: 创建虚拟环境
python -m venv venv

:: 激活环境
# CMD中运行:
venv\Scripts\activate.bat

# PowerShell中运行:
.\venv\Scripts\Activate.ps1

:: 安装依赖
pip install -r requirements.txt
```

Linux/macOS系统:
```bash
# 创建虚拟环境
python -m venv venv

# 激活环境
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

#### 2.2 开发工具配置
- 安装VSCode扩展
  - Python
  - Pylint
  - autopep8
- 配置git
  - 设置.gitignore
  - 配置git lfs（大文件存储）

### 3. 常见问题处理

#### 3.1 文件恢复
```shell
# 从Git恢复
git checkout [file_path]

# 从备份恢复
# Windows CMD:
robocopy backup [file_path] [destination]

# Windows PowerShell:
Copy-Item backup\[file_path] [destination]

# Linux/macOS:
rsync -av backup/[file_path] [destination]
```

#### 3.2 清理后环境修复
1. 重新安装依赖：
```shell
pip install -r requirements.txt
```

2. 下载模型文件：
```shell
python scripts/download_models.py
```

### 4. 其他资源

#### 4.1 有用的脚本
- `scripts/analyze_repo.py` - 仓库分析工具
- `scripts/download_models.py` - 模型下载工具
- `scripts/cleanup.py` - 其他清理工具

#### 4.2 文档
- `docs/` 中的技术规格
- `api_docs/` 中的API文档
- `CONTRIBUTING.md` 中的贡献指南

#### 4.3 支持
如有问题或疑问：
- 在GitHub上创建issue
- 查看现有文档
- 联系维护者

---

## Usage Instructions

### 1. Storage Space Check and Optimization

#### 1.1 Run Analysis Script
```shell
# On Windows:
python scripts\analyze_repo.py .

# On Linux/macOS:
python scripts/analyze_repo.py .
```

The analysis script generates:
- analysis_report.txt - Analysis report
- cleanup_script.{bat|sh} - Cleanup script
- backup/ - Backup directory

#### 1.2 Check Analysis Report
```shell
# On Windows:
type analysis_report.txt

# On Linux/macOS:
cat analysis_report.txt
```

Report includes:
- File size statistics
- File categorization
- Cleanup recommendations

#### 1.3 Execute Safe Cleanup
Windows:
```batch
:: 1. Create backup
mkdir backup
robocopy . backup /MIR /XD backup

:: 2. Check cleanup script content
type cleanup_script.bat

:: 3. Execute cleanup
:: In CMD:
cleanup_script.bat

:: Or in PowerShell:
.\cleanup_script.bat
```

Linux/macOS:
```bash
# 1. Create backup
mkdir -p backup
rsync -av --exclude 'backup' . backup/

# 2. Check cleanup script content
cat cleanup_script.sh

# 3. Execute cleanup
bash cleanup_script.sh
```

### 2. Development Environment Setup

#### 2.1 Environment Preparation
Windows:
```batch
:: Create virtual environment
python -m venv venv

:: Activate environment
# In CMD:
venv\Scripts\activate.bat

# In PowerShell:
.\venv\Scripts\Activate.ps1

:: Install dependencies
pip install -r requirements.txt
```

Linux/macOS:
```bash
# Create virtual environment
python -m venv venv

# Activate environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

#### 2.2 Development Tools Configuration
- Install VSCode extensions
  - Python
  - Pylint
  - autopep8
- Configure git
  - Set up .gitignore
  - Configure git lfs (Large File Storage)

### 3. Common Issues Resolution

#### 3.1 File Recovery
```shell
# Recover from Git
git checkout [file_path]

# Recover from backup
# Windows CMD:
robocopy backup [file_path] [destination]

# Windows PowerShell:
Copy-Item backup\[file_path] [destination]

# Linux/macOS:
rsync -av backup/[file_path] [destination]
```

#### 3.2 Post-cleanup Environment Recovery
1. Reinstall dependencies:
```shell
pip install -r requirements.txt
```

2. Download model files:
```shell
python scripts/download_models.py
```

### 4. Additional Resources

#### 4.1 Useful Scripts
- `scripts/analyze_repo.py` - Repository analysis tool
- `scripts/download_models.py` - Model download utility
- `scripts/cleanup.py` - Additional cleanup utilities

#### 4.2 Documentation
- Technical specifications in `docs/`
- API documentation in `api_docs/`
- Contribution guidelines in `CONTRIBUTING.md`

#### 4.3 Support
For issues and questions:
- Create an issue on GitHub
- Check existing documentation
- Contact maintainers
