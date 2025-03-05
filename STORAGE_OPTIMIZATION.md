## Safe Cleanup Process

### 1. Repository Size Analysis
Use the repository analysis script:
```bash
# First analyze repository content
python scripts/analyze_repo.py .

# Check generated report
cat cleanup_report.txt

# Review cleanup script content
cat cleanup.sh
```

### 2. Safe Cleanup Steps
1. **Backup Important Data**
   ```bash
   # Create full backup
   tar -czf repo_backup.tar.gz .
   ```

2. **Execute Cleanup in Steps**
   - Review file list in analysis report
   - Confirm each file to be deleted
   - Execute move/delete operations one by one

3. **Verify Cleanup Results**
   ```bash
   # Re-analyze repository
   python scripts/analyze_repo.py .
   
   # Check git status
   git status
   ```

### 3. Important Notes
- Never delete source code files directly
- Keep necessary sample data
- Confirm backups before moving large files
- Maintain traceability of cleanup operations

### 4. Recovery Process
If files are deleted by mistake:
1. Restore from backup
2. Recover using git
   ```bash
   git checkout [file_path]
   ```
3. Re-download from external storage
