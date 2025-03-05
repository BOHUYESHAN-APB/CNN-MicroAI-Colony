# Git Repository Size Reduction Guide

## Problem Description
Even after cleaning up large files in the working directory, the repository size remains large because:
1. Git keeps all historical versions of files
2. Deleted large files still exist in commit history
3. The .git directory continues to grow

## Solutions

### 1. Analyze Git History
```bash
# View the largest files and their history
git rev-list --objects --all | git cat-file --batch-check='%(objecttype) %(objectname) %(objectsize) %(rest)' | sed -n 's/^blob //p' | sort -rn -k2 | head -10

# Or use git-filter-repo for analysis
git filter-repo --analyze

# Using our custom script
python scripts/analyze_git_history.py
```

### 2. Clean Git History

#### 2.1 Using BFG Repo Cleaner (Recommended)
```bash
# 1. Download BFG
wget https://repo1.maven.org/maven2/com/madgag/bfg/1.14.0/bfg-1.14.0.jar -O bfg.jar

# 2. Create repository mirror
git clone --mirror your-repo.git
cd your-repo.git

# 3. Run BFG to remove large files
java -jar bfg.jar --strip-blobs-bigger-than 100M .

# 4. Clean and update
git reflog expire --expire=now --all
git gc --prune=now --aggressive
```

#### 2.2 Using git filter-repo
```bash
# Install git-filter-repo
pip install git-filter-repo

# Remove files larger than 100MB
git filter-repo --strip-blobs-bigger-than 100M

# Or remove specific files
git filter-repo --path-glob '*.zip' --invert-paths
```

### 3. Push Changes

```bash
# Force push changes (Warning: This rewrites history!)
git push origin --force --all

# If you have tags that need updating
git push origin --force --tags
```

## Preventive Measures

### 1. Configure Git LFS
```bash
# Install Git LFS
git lfs install

# Track large files
git lfs track "*.psd"
git lfs track "*.zip"
git add .gitattributes

# Commit using LFS
git add file.psd
git commit -m "Add design file"
```

### 2. Set Git Attributes
Create .gitattributes file:
```
*.psd filter=lfs diff=lfs merge=lfs -text
*.zip filter=lfs diff=lfs merge=lfs -text
*.pdf filter=lfs diff=lfs merge=lfs -text
*.bin filter=lfs diff=lfs merge=lfs -text
```

### 3. Use Pre-commit Hook
Create .git/hooks/pre-commit:
```bash
#!/bin/bash

# Check for large files
maximum_size_kb=10240  # 10MB
while read -r file; do
    size=$(du -k "$file" | cut -f1)
    if [ "$size" -gt $maximum_size_kb ]; then
        echo "Error: $file is larger than ${maximum_size_kb}KB"
        exit 1
    fi
done < <(git diff --cached --name-only)
```

## Important Notes

1. **Backup Important Data**
   - Back up the entire repository before cleaning history
   - Save important large files to external storage

2. **Team Collaboration**
   - Notify all team members
   - Coordinate timing for history cleanup
   - Provide new clone instructions

3. **Ongoing Maintenance**
   - Regular repository size checks
   - Prompt handling of large files
   - Use Git LFS for binary files

## Recovery Options

If cleanup goes wrong:

```bash
# 1. Restore from backup
cp -r backup/.git/* .git/

# 2. Or reset to specific commit
git reset --hard <commit-hash>

# 3. If you have a backup remote repository
git remote add backup <backup-url>
git fetch backup
git reset --hard backup/main
```

## Additional Tools

### 1. Custom Git History Analysis Script
```bash
# Analyze Git history for large files
python scripts/analyze_git_history.py

# Specify minimum file size (in MB)
python scripts/analyze_git_history.py 10
```

### 2. Repository Maintenance
```bash
# Regular maintenance commands
git gc
git prune
git repack -ad
```

### 3. Git LFS Management
```bash
# View tracked patterns
git lfs track

# List tracked files
git lfs ls-files

# Pull all LFS objects
git lfs pull
