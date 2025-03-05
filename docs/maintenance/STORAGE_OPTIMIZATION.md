# Storage Optimization Guide

## Repository Analysis and Cleanup

### 1. Size Analysis
```bash
# First analyze repository content
python scripts/analyze_repo.py .

# Check generated report
cat cleanup_report.txt

# Review cleanup script content
cat cleanup.sh
```

### 2. Data Classification
1. **Essential Files**
   - Source code
   - Configuration files
   - Documentation
   - Test cases
   - Build scripts

2. **Large Files**
   - Model checkpoints
   - Training datasets
   - Test images
   - Log files
   - Temporary files

3. **Unnecessary Files**
   - Cached data
   - Compiled binaries
   - Development artifacts
   - Backup files
   - Debug logs

## Cleanup Procedures

### 1. Preparation
1. **Backup Critical Data**
   ```bash
   # Create full backup
   tar -czf repo_backup.tar.gz .
   ```

2. **Document Current State**
   ```bash
   # Generate file list
   find . -type f > file_list.txt
   
   # Record git status
   git status > git_status.txt
   ```

3. **Check Dependencies**
   - Review import statements
   - Check configuration files
   - Verify resource references
   - Test data requirements

### 2. Safe Cleanup Steps
1. **Review and Plan**
   - Analyze cleanup report
   - Mark files for removal
   - Plan cleanup sequence
   - Document decisions

2. **Execute Cleanup**
   ```bash
   # Move large files to external storage
   python scripts/move_large_files.py
   
   # Remove temporary files
   python scripts/cleanup_temp.py
   
   # Clean git history
   python scripts/git_cleanup.py
   ```

3. **Verify Results**
   ```bash
   # Re-analyze repository
   python scripts/analyze_repo.py .
   
   # Check git status
   git status
   
   # Run tests
   python -m pytest tests/
   ```

## Storage Management

### 1. Git LFS Setup
```bash
# Initialize Git LFS
git lfs install

# Track large file types
git lfs track "*.pth"
git lfs track "*.h5"
git lfs track "*.onnx"
git lfs track "*.jpg"
```

### 2. Automatic Cleanup
1. **Pre-commit Hooks**
   ```bash
   # Install pre-commit
   pip install pre-commit
   
   # Configure hooks
   cp scripts/pre-commit .git/hooks/
   chmod +x .git/hooks/pre-commit
   ```

2. **Scheduled Tasks**
   ```bash
   # Add to crontab
   0 0 * * 1 python scripts/weekly_cleanup.py
   ```

### 3. Storage Monitoring
1. **Size Tracking**
   ```bash
   # Monitor repository size
   du -sh .
   
   # Track large files
   find . -type f -size +100M
   ```

2. **Usage Alerts**
   - Size threshold warnings
   - Space usage notifications
   - Cleanup reminders

## Recovery Procedures

### 1. Immediate Recovery
```bash
# Restore from backup
tar -xzf repo_backup.tar.gz

# Git checkout
git checkout [file_path]

# LFS pull
git lfs pull
```

### 2. External Storage
1. **Cloud Storage**
   - AWS S3 backup
   - Google Cloud Storage
   - Azure Blob Storage

2. **Local Backup**
   - External hard drives
   - Network storage
   - Tape backup

### 3. Version Control
```bash
# Review history
git log --all --full-history -- [file_path]

# Restore specific version
git checkout [commit] -- [file_path]
```

## Best Practices

### 1. Prevention
- Use .gitignore properly
- Implement size checks
- Regular maintenance
- Document procedures

### 2. Documentation
- Update cleanup logs
- Record decisions
- Maintain procedures
- Track changes

### 3. Training
- Team guidelines
- Storage policies
- Cleanup procedures
- Recovery processes

## Important Notes

### 1. Safety Measures
- Never delete source code directly
- Keep necessary sample data
- Confirm backups before cleanup
- Maintain traceability

### 2. Communication
- Notify team before cleanup
- Document removed files
- Share cleanup results
- Update access methods

### 3. Monitoring
- Track storage usage
- Monitor cleanup impact
- Verify system integrity
- Update documentation
