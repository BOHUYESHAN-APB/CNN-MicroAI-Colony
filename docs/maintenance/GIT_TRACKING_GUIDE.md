# Git文件追踪说明

## 一、基本规则

### 1.1 Git默认追踪
- 所有文件和目录都会被追踪，除非：
  1. 被`.gitignore`排除
  2. 已经在Git中但被标记为不追踪(`git rm --cached`)
  3. 目录为空（Git不追踪空目录）

### 1.2 常见会被追踪的文件
```plaintext
# 源代码
*.py
*.cpp
*.h
*.java
*.js
*.css
*.html

# 配置文件
*.json
*.yaml
*.yml
*.xml
*.ini

# 文档
*.md
*.txt
LICENSE
README.*

# 其他项目文件
.gitignore
.gitattributes
requirements.txt
setup.py
```

### 1.3 通常不需要追踪的文件
```plaintext
# 编译生成的文件
*.pyc
*.pyo
*.pyd
__pycache__/
*.so
*.dll
*.dylib

# 环境相关
venv/
env/
.env
.venv/

# IDE配置
.vscode/
.idea/
*.sublime-*

# 临时文件
*.log
*.tmp
*.temp
*.swp

# 大文件
*.zip
*.tar.gz
*.rar
*.pth
*.weights
*.model
```

## 二、控制追踪

### 2.1 配置.gitignore
```bash
# 创建或编辑.gitignore
cat > .gitignore << EOL
# Python
__pycache__/
*.py[cod]
*$py.class
*.so

# 虚拟环境
venv/
ENV/

# IDE
.idea/
.vscode/
*.swp

# 大文件
*.zip
*.rar
*.pth
*.weights

# 日志和临时文件
*.log
*.tmp
EOL
```

### 2.2 停止追踪文件
```bash
# 从Git中移除但保留文件
git rm --cached file.txt

# 从Git中移除目录
git rm -r --cached directory/

# 添加到.gitignore后应用更改
git add .gitignore
git commit -m "Update .gitignore"
```

### 2.3 强制追踪文件
```bash
# 即使在.gitignore中也要追踪
git add -f file.txt

# 或在.gitignore中使用!
!important.txt
```

## 三、Git LFS文件

### 3.1 LFS追踪的文件
```plaintext
# 常见LFS文件类型
*.psd       # Photoshop文件
*.ai        # Illustrator文件
*.mp4       # 视频文件
*.zip       # 压缩包
*.pth       # PyTorch模型
*.h5        # HDF5文件
*.weights   # 深度学习权重
```

### 3.2 配置LFS
```bash
# 初始化LFS
git lfs install

# 配置追踪
git lfs track "*.psd"
git lfs track "*.zip"
git lfs track "*.pth"

# 确认追踪
git lfs ls-files
```

## 四、检查追踪状态

### 4.1 查看状态
```bash
# 查看所有更改
git status

# 查看未追踪的文件
git status -u

# 查看忽略的文件
git status --ignored
```

### 4.2 查看详细信息
```bash
# 查看已追踪文件
git ls-files

# 查看忽略规则
git check-ignore -v file.txt

# 查看LFS文件
git lfs ls-files
```

## 五、最佳实践

1. **提交前检查**
   ```bash
   # 检查将要提交的文件
   git status
   
   # 检查具体更改
   git diff --cached
   ```

2. **定期更新.gitignore**
   ```bash
   # 检查是否有新的应该忽略的文件
   git status -u
   
   # 更新.gitignore
   vim .gitignore
   ```

3. **使用通配符**
   ```plaintext
   # 在.gitignore中使用
   *.log       # 所有日志文件
   logs/       # logs目录
   **/temp/    # 任何位置的temp目录
   ```

4. **目录结构维护**
   ```bash
   # 保留空目录
   touch directory/.gitkeep
   
   # 记录目录结构
   tree > structure.txt
