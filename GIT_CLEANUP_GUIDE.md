# Git仓库瘦身指南

## 问题说明
即使清理了当前工作目录的大文件，仓库大小仍然很大，这是因为：
1. Git保留了所有文件的历史版本
2. 删除的大文件仍然存在于历史提交中
3. .git目录会持续增长

## 解决方案

### 1. 分析Git历史
```bash
# 查看最大的文件及其历史
git rev-list --objects --all | git cat-file --batch-check='%(objecttype) %(objectname) %(objectsize) %(rest)' | sed -n 's/^blob //p' | sort -rn -k2 | head -10

# 或使用git-filter-repo查看统计
git filter-repo --analyze
```

### 2. 清理Git历史

#### 2.1 使用BFG Repo Cleaner（推荐）
```bash
# 1. 下载BFG
wget https://repo1.maven.org/maven2/com/madgag/bfg/1.14.0/bfg-1.14.0.jar -O bfg.jar

# 2. 创建仓库镜像
git clone --mirror your-repo.git
cd your-repo.git

# 3. 运行BFG删除大文件
java -jar bfg.jar --strip-blobs-bigger-than 100M .

# 4. 清理和更新
git reflog expire --expire=now --all
git gc --prune=now --aggressive
```

#### 2.2 使用git filter-repo
```bash
# 安装git-filter-repo
pip install git-filter-repo

# 删除大于100MB的文件
git filter-repo --strip-blobs-bigger-than 100M

# 或删除特定文件
git filter-repo --path-glob '*.zip' --invert-paths
```

### 3. 提交更改

```bash
# 强制推送更改（警告：这将重写历史！）
git push origin --force --all

# 如果有标签也需要更新
git push origin --force --tags
```

## 预防措施

### 1. 配置Git LFS
```bash
# 安装Git LFS
git lfs install

# 跟踪大文件
git lfs track "*.psd"
git lfs track "*.zip"
git add .gitattributes

# 提交使用LFS
git add file.psd
git commit -m "Add design file"
```

### 2. 设置Git属性
创建.gitattributes文件：
```
*.psd filter=lfs diff=lfs merge=lfs -text
*.zip filter=lfs diff=lfs merge=lfs -text
*.pdf filter=lfs diff=lfs merge=lfs -text
*.bin filter=lfs diff=lfs merge=lfs -text
```

### 3. 使用预提交钩子
创建.git/hooks/pre-commit：
```bash
#!/bin/bash

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

## 注意事项

1. **备份重要数据**
   - 在执行历史清理前备份整个仓库
   - 保存重要的大文件到外部存储

2. **团队协作**
   - 通知所有团队成员
   - 协调时间执行历史清理
   - 提供新克隆指南

3. **后续维护**
   - 定期检查仓库大小
   - 及时处理大文件
   - 使用Git LFS管理二进制文件

## 恢复方案

如果清理出现问题：

```bash
# 1. 从备份恢复
cp -r backup/.git/* .git/

# 2. 或重置到特定提交
git reset --hard <commit-hash>

# 3. 如果有备份的远程仓库
git remote add backup <backup-url>
git fetch backup
git reset --hard backup/main
