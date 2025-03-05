# 仓库维护完整指南

## 一、仓库分析

### 1.1 分析当前工作目录
```bash
# 分析当前目录大文件
python scripts/analyze_repo.py .

# 查看分析报告
cat analysis_report.txt
```

### 1.2 分析Git历史
```bash
# 分析Git历史中的大文件
python scripts/analyze_git_history.py

# 指定最小文件大小（MB）
python scripts/analyze_git_history.py 50
```

### 1.3 手动查看大文件
```bash
# 列出最大的文件及其历史
git rev-list --objects --all | git cat-file --batch-check='%(objecttype) %(objectname) %(objectsize) %(rest)' | sed -n 's/^blob //p' | sort -rn -k2 | head -10

# 查看当前目录大小
du -sh *
```

## 二、自动清理（推荐）

### 2.1 Windows系统
```batch
# 执行清理脚本
scripts\cleanup_repo.bat

# 如果需要回滚：
xcopy /E /I /H backup_[timestamp]\.git .git
```

### 2.2 Linux/macOS系统
```bash
# 执行清理脚本
python scripts/cleanup_repo.py

# 如果需要回滚：
cp -r backup_[timestamp]/.git .
```

## 三、手动清理步骤

### 3.1 备份
```bash
# 创建.git备份
cp -r .git .git.bak      # Linux/macOS
xcopy /E /I /H .git .git.bak   # Windows

# 创建仓库镜像
git clone --mirror . repo.git.bak
```

### 3.2 清理大文件

#### 使用BFG（推荐）
```bash
# 1. 下载BFG
wget https://repo1.maven.org/maven2/com/madgag/bfg/1.14.0/bfg-1.14.0.jar -O bfg.jar
# 或使用浏览器下载

# 2. 删除大文件（>100MB）
java -jar bfg.jar --strip-blobs-bigger-than 100M .

# 3. 删除特定目录
java -jar bfg.jar --delete-folders venv
```

#### 使用git filter-repo
```bash
# 安装git-filter-repo
pip install git-filter-repo

# 删除大文件
git filter-repo --strip-blobs-bigger-than 100M

# 删除特定目录
git filter-repo --path venv --invert-paths
```

### 3.3 维护和优化
```bash
# 清理和压缩
git reflog expire --expire=now --all
git gc --prune=now --aggressive
```

## 四、预防措施配置

### 4.1 配置.gitignore
```bash
cat >> .gitignore << EOL
# Python
venv/
env/
__pycache__/
*.pyc
*.pyo
*.pyd

# Model files
checkpoints/
*.weights
*.pth
*.h5
*.onnx

# Large files
*.zip
*.tar.gz
*.rar

# Development
.vscode/
.idea/
*.log

# Data
data/raw/
pic/higher-resolution/
pic/lower-resolution/
EOL
```

### 4.2 配置Git LFS
```bash
# 安装Git LFS
git lfs install

# 配置跟踪规则
git lfs track "*.pth"
git lfs track "*.weights"
git lfs track "*.h5"
git lfs track "*.jpg"
git lfs track "*.png"
git lfs track "*.zip"

# 提交配置
git add .gitattributes
git commit -m "Configure Git LFS"
```

### 4.3 添加大文件检查钩子
```bash
cat > .git/hooks/pre-commit << 'EOL'
#!/bin/bash

maximum_size_kb=10240  # 10MB
while read -r file; do
    size=$(du -k "$file" | cut -f1)
    if [ "$size" -gt $maximum_size_kb ]; then
        echo "Error: $file is larger than ${maximum_size_kb}KB"
        exit 1
    fi
done < <(git diff --cached --name-only)
EOL

chmod +x .git/hooks/pre-commit
```

## 五、后续维护

### 5.1 定期检查
```bash
# 分析仓库状态
python scripts/analyze_repo.py .

# 查看LFS文件
git lfs ls-files

# 检查仓库大小
du -sh .git
```

### 5.2 清理临时文件
```bash
# 清理Python缓存
find . -type f -name "*.pyc" -delete
find . -type d -name "__pycache__" -exec rm -r {} +

# 清理日志
find . -type f -name "*.log" -delete
```

### 5.3 提交大文件
```bash
# 使用Git LFS添加大文件
git lfs track "path/to/large/file"
git add "path/to/large/file"
git commit -m "Add large file using Git LFS"
```

## 六、恢复操作

### 6.1 从备份恢复
```bash
# 恢复整个.git目录
rm -rf .git
cp -r backup_[timestamp]/.git .

# 或恢复特定文件
git checkout backup_[timestamp] -- path/to/file
```

### 6.2 重置更改
```bash
# 重置到特定提交
git reset --hard <commit-hash>

# 从远程重置
git fetch origin
git reset --hard origin/main
```

## 七、注意事项

1. **执行清理前：**
   - 创建完整备份
   - 通知团队成员
   - 记录当前状态

2. **清理过程中：**
   - 不要中断操作
   - 保持网络连接
   - 监控错误日志

3. **清理后：**
   - 验证仓库完整性
   - 测试功能正常
   - 更新文档

4. **团队协作：**
   - 统一使用Git LFS
   - 遵循大文件规范
   - 定期同步和清理
