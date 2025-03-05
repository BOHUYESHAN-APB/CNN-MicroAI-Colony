# Git追踪状态总结

## 一、已追踪的文件类型

### 1. 文档文件
- Markdown文档 (*.md)
- 文本文件 (*.txt)
- 许可证文件 (LICENSE*)
- HTML模板文件 (app/templates/*.html)

### 2. 源代码
- Python源文件 (*.py)
- 配置文件 (*.yaml, *.json)
- 初始化文件 (__init__.py)

### 3. 数据和结果
- CSV数据文件 (app/results/*.csv)
- JSON结果文件 (app/results/*.json)
- Excel文件 (app/results/*.xlsx)

### 4. 资源文件
- 国际化资源 (app/resources/i18n/*.json)
- 字体文件 (app/font/MiSans VF.ttf)

### 5. 脚本和工具
- 构建脚本 (build.py)
- 清理脚本 (cleanup.bat, cleanup.sh)
- 分析脚本 (scripts/*)

## 二、被忽略的文件类型（.gitignore）

### 1. 临时文件
- Python缓存 (__pycache__/, *.pyc, *.pyo)
- 编译文件 (*.so, *.dll)
- 日志文件 (*.log)

### 2. 环境相关
- 虚拟环境 (venv/, env/)
- IDE配置 (.vscode/, .idea/)

### 3. 大文件
- 模型文件 (*.pth, *.pt, *.weights)
- 图片文件 (*.jpg, *.png, *.jpeg)
- 视频文件 (*.mp4)

### 4. 数据目录
- 高分辨率图片 (pic/higher-resolution/)
- 低分辨率图片 (pic/lower-resolution/)
- 结果目录 (results/predictions/, results/visualizations/)

## 三、需要注意的问题

1. **结果文件**
   - app/results/目录下的文件被追踪
   - 考虑是否应该移动到外部存储

2. **模型文件**
   - 建议使用Git LFS管理字体文件
   - 检查是否有大型二进制文件未被忽略

3. **日志和缓存**
   - 确保所有日志目录被正确忽略
   - 检查是否有临时文件被意外追踪

## 四、建议操作

1. **配置Git LFS**
```bash
git lfs track "*.ttf"   # 字体文件
git lfs track "app/results/**/*.xlsx"  # Excel结果文件
```

2. **更新.gitignore**
```bash
# 添加以下规则
app/results/**/*.xlsx
app/results/**/*.csv
app/results/**/*.json
```

3. **清理已追踪的大文件**
```bash
# 停止追踪结果文件
git rm --cached app/results/**/*.xlsx
git rm --cached app/results/**/*.csv
git rm --cached app/results/**/*.json
```

4. **调整文件存储**
- 将results目录移到外部存储
- 创建数据下载脚本
- 更新文档说明数据获取方式
