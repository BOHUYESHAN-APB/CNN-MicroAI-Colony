# Complete Repository Maintenance Guide

## I. Repository Analysis

### 1.1 Analyze Current Working Directory
```bash
# Analyze large files in current directory
python scripts/analyze_repo.py .

# View analysis report
cat analysis_report.txt
```

### 1.2 Analyze Git History
```bash
# Analyze large files in Git history
python scripts/analyze_git_history.py

# Specify minimum file size (MB)
python scripts/analyze_git_history.py 50
```

### 1.3 Manual File Size Check
```bash
# List largest files and their history
git rev-list --objects --all | git cat-file --batch-check='%(objecttype) %(objectname) %(objectsize) %(rest)' | sed -n 's/^blob //p' | sort -rn -k2 | head -10

# Check current directory size
du -sh *
```

## II. Automatic Cleanup (Recommended)

### 2.1 Windows System
```batch
# Run cleanup script
scripts\cleanup_repo.bat

# To rollback if needed:
xcopy /E /I /H backup_[timestamp]\.git .git
```

### 2.2 Linux/macOS System
```bash
# Run cleanup script
python scripts/cleanup_repo.py

# To rollback if needed:
cp -r backup_[timestamp]/.git .
```

## III. Manual Cleanup Steps

### 3.1 Backup
```bash
# Create .git backup
cp -r .git .git.bak      # Linux/macOS
xcopy /E /I /H .git .git.bak   # Windows

# Create repository mirror
git clone --mirror . repo.git.bak
```

### 3.2 Clean Large Files

#### Using BFG (Recommended)
```bash
# 1. Download BFG
wget https://repo1.maven.org/maven2/com/madgag/bfg/1.14.0/bfg-1.14.0.jar -O bfg.jar
# Or download using browser

# 2. Remove large files (>100MB)
java -jar bfg.jar --strip-blobs-bigger-than 100M .

# 3. Remove specific directories
java -jar bfg.jar --delete-folders venv
```

#### Using git filter-repo
```bash
# Install git-filter-repo
pip install git-filter-repo

# Remove large files
git filter-repo --strip-blobs-bigger-than 100M

# Remove specific directories
git filter-repo --path venv --invert-paths
```

### 3.3 Maintenance and Optimization
```bash
# Clean and compress
git reflog expire --expire=now --all
git gc --prune=now --aggressive
```

## IV. Preventive Measures

### 4.1 Configure .gitignore
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

### 4.2 Configure Git LFS
```bash
# Install Git LFS
git lfs install

# Configure tracking rules
git lfs track "*.pth"
git lfs track "*.weights"
git lfs track "*.h5"
git lfs track "*.jpg"
git lfs track "*.png"
git lfs track "*.zip"

# Commit configuration
git add .gitattributes
git commit -m "Configure Git LFS"
```

### 4.3 Add Large File Check Hook
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

## V. Ongoing Maintenance

### 5.1 Regular Checks
```bash
# Analyze repository status
python scripts/analyze_repo.py .

# View LFS files
git lfs ls-files

# Check repository size
du -sh .git
```

### 5.2 Clean Temporary Files
```bash
# Clean Python cache
find . -type f -name "*.pyc" -delete
find . -type d -name "__pycache__" -exec rm -r {} +

# Clean logs
find . -type f -name "*.log" -delete
```

### 5.3 Commit Large Files
```bash
# Use Git LFS to add large files
git lfs track "path/to/large/file"
git add "path/to/large/file"
git commit -m "Add large file using Git LFS"
```

## VI. Recovery Operations

### 6.1 Restore from Backup
```bash
# Restore entire .git directory
rm -rf .git
cp -r backup_[timestamp]/.git .

# Or restore specific files
git checkout backup_[timestamp] -- path/to/file
```

### 6.2 Reset Changes
```bash
# Reset to specific commit
git reset --hard <commit-hash>

# Reset from remote
git fetch origin
git reset --hard origin/main
```

## VII. Important Notes

1. **Before Cleanup:**
   - Create complete backup
   - Notify team members
   - Record current state

2. **During Cleanup:**
   - Don't interrupt operations
   - Maintain network connection
   - Monitor error logs

3. **After Cleanup:**
   - Verify repository integrity
   - Test functionality
   - Update documentation

4. **Team Collaboration:**
   - Standardize Git LFS usage
   - Follow large file guidelines
   - Regular sync and cleanup
