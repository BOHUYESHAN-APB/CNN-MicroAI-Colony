# 存储优化指南

## 仓库分析与清理

### 1. 规模分析
```bash
# 首先分析仓库内容
python scripts/analyze_repo.py .

# 检查生成的报告
cat cleanup_report.txt

# 审查清理脚本内容
cat cleanup.sh
```

### 2. 数据分类
1. **必要文件**
   - 源代码
   - 配置文件
   - 文档
   - 测试用例
   - 构建脚本

2. **大型文件**
   - 模型检查点
   - 训练数据集
   - 测试图像
   - 日志文件
   - 临时文件

3. **不必要文件**
   - 缓存数据
   - 编译二进制文件
   - 开发产物
   - 备份文件
   - 调试日志

## 清理程序

### 1. 准备工作
1. **备份关键数据**
   ```bash
   # 创建完整备份
   tar -czf repo_backup.tar.gz .
   ```

2. **记录当前状态**
   ```bash
   # 生成文件列表
   find . -type f > file_list.txt
   
   # 记录git状态
   git status > git_status.txt
   ```

3. **检查依赖关系**
   - 审查导入语句
   - 检查配置文件
   - 验证资源引用
   - 测试数据要求

### 2. 安全清理步骤
1. **审查与计划**
   - 分析清理报告
   - 标记待删除文件
   - 规划清理顺序
   - 记录决策

2. **执行清理**
   ```bash
   # 将大文件移至外部存储
   python scripts/move_large_files.py
   
   # 删除临时文件
   python scripts/cleanup_temp.py
   
   # 清理git历史
   python scripts/git_cleanup.py
   ```

3. **验证结果**
   ```bash
   # 重新分析仓库
   python scripts/analyze_repo.py .
   
   # 检查git状态
   git status
   
   # 运行测试
   python -m pytest tests/
   ```

## 存储管理

### 1. Git LFS设置
```bash
# 初始化Git LFS
git lfs install

# 跟踪大型文件类型
git lfs track "*.pth"
git lfs track "*.h5"
git lfs track "*.onnx"
git lfs track "*.jpg"
```

### 2. 自动清理
1. **预提交钩子**
   ```bash
   # 安装pre-commit
   pip install pre-commit
   
   # 配置钩子
   cp scripts/pre-commit .git/hooks/
   chmod +x .git/hooks/pre-commit
   ```

2. **定时任务**
   ```bash
   # 添加到crontab
   0 0 * * 1 python scripts/weekly_cleanup.py
   ```

### 3. 存储监控
1. **规模跟踪**
   ```bash
   # 监控仓库大小
   du -sh .
   
   # 跟踪大文件
   find . -type f -size +100M
   ```

2. **使用警报**
   - 大小阈值警告
   - 空间使用通知
   - 清理提醒

## 恢复程序

### 1. 即时恢复
```bash
# 从备份恢复
tar -xzf repo_backup.tar.gz

# Git检出
git checkout [file_path]

# LFS拉取
git lfs pull
```

### 2. 外部存储
1. **云存储**
   - AWS S3备份
   - Google Cloud Storage
   - Azure Blob Storage

2. **本地备份**
   - 外部硬盘
   - 网络存储
   - 磁带备份

### 3. 版本控制
```bash
# 查看历史
git log --all --full-history -- [file_path]

# 恢复特定版本
git checkout [commit] -- [file_path]
```

## 最佳实践

### 1. 预防措施
- 正确使用.gitignore
- 实施大小检查
- 定期维护
- 文档程序

### 2. 文档
- 更新清理日志
- 记录决策
- 维护程序
- 跟踪变更

### 3. 培训
- 团队指南
- 存储策略
- 清理程序
- 恢复流程

## 重要注意事项

### 1. 安全措施
- 禁止直接删除源代码
- 保留必要的样本数据
- 清理前确认备份
- 维持可追溯性

### 2. 沟通
- 清理前通知团队
- 记录已删除文件
- 分享清理结果
- 更新访问方法

### 3. 监控
- 跟踪存储使用情况
- 监控清理影响
- 验证系统完整性
- 更新文档
