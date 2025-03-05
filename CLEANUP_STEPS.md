# 仓库清理步骤

## 1. 立即处理

### 1.1 备份重要数据
```bash
# 创建完整备份
cp -r .git .git.bak
git clone --mirror . repo.git.bak
```

### 1.2 配置.gitignore
```bash
# 添加以下内容到.gitignore
venv/
env/
__pycache__/
*.pyc
*.pyo
*.pyd
checkpoints/
*.weights
*.pth
*.h5
```

### 1.3 设置Git LFS
```bash
# 安装Git LFS
git lfs install

# 跟踪大文件
git lfs track "*.pth"
git lfs track "*.weights"
git lfs track "*.jpg"
git lfs track "*.png"
```

## 2. 清理步骤

### 2.1 删除venv目录
```bash
# 移除venv目录的跟踪
git rm -r --cached venv/
```

### 2.2 使用BFG清理历史
```bash
# 下载BFG
wget https://repo1.maven.org/maven2/com/madgag/bfg/1.14.0/bfg-1.14.0.jar -O bfg.jar

# 清理大文件
java -jar bfg.jar --strip-blobs-bigger-than 100M .

# 清理已配置的目录
java -jar bfg.jar --delete-folders venv .
```

### 2.3 压缩仓库
```bash
git reflog expire --expire=now --all
git gc --prune=now --aggressive
```

## 3. 文件迁移

### 3.1 模型文件
- 将checkpoint文件移动到Release
- 或上传到模型托管平台
- 提供下载脚本

### 3.2 数据集
- 将pic目录移动到外部存储
- 只保留少量示例图片
- 更新文档中的数据获取说明

### 3.3 开发依赖
- 使用requirements.txt管理依赖
- 提供环境配置脚本
- 移除所有编译后的文件

## 4. 提交更改

```bash
# 确认所有更改
git status

# 提交更改
git add .
git commit -m "Clean up repository and configure Git LFS"

# 强制推送（警告：这会重写历史！）
git push origin --force --all
git push origin --force --tags
```

## 5. 团队同步

1. 通知所有团队成员
2. 提供新的克隆说明：
   ```bash
   # 重新克隆仓库
   git clone https://github.com/username/repo.git
   
   # 设置环境
   python -m venv venv
   source venv/bin/activate  # 或 venv\Scripts\activate
   pip install -r requirements.txt
   
   # 下载模型文件
   python scripts/download_models.py
   ```

## 6. 预防措施

### 6.1 配置提交钩子
```bash
#!/bin/bash
# .git/hooks/pre-commit

# 检查大文件
maximum_size_kb=10240  # 10MB
while read -r file; do
    size=$(du -k "$file" | cut -f1)
    if [ "$size" -gt $maximum_size_kb ]; then
        echo "Error: $file is larger than ${maximum_size_kb}KB"
        exit 1
    fi
done < <(git diff --cached --name-only)
```

### 6.2 定期维护
- 每周运行仓库分析
- 及时处理大文件
- 更新.gitattributes配置

### 6.3 文档更新
- 更新贡献指南
- 添加文件大小限制说明
- 提供外部资源链接
