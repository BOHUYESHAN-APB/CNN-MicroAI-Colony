## 安全清理流程

### 1. 分析仓库大小
使用仓库分析脚本：
```bash
# 先分析仓库内容
python scripts/analyze_repo.py .

# 检查生成的报告
cat cleanup_report.txt

# 查看清理脚本内容
cat cleanup.sh
```

### 2. 安全清理步骤
1. **备份重要数据**
   ```bash
   # 创建完整备份
   tar -czf repo_backup.tar.gz .
   ```

2. **分步执行清理**
   - 检查分析报告中的文件列表
   - 确认每个要删除的文件
   - 逐个执行移动/删除操作

3. **验证清理结果**
   ```bash
   # 重新分析仓库
   python scripts/analyze_repo.py .
   
   # 检查git状态
   git status
   ```

### 3. 注意事项
- 不要直接删除源代码文件
- 保留必要的示例数据
- 大文件移动前先确认备份
- 保持清理操作可追溯

### 4. 恢复流程
如果误删文件，可以：
1. 从备份中恢复
2. 使用git恢复
   ```bash
   git checkout [file_path]
   ```
3. 从外部存储重新下载
