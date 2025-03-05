#!/usr/bin/env python3
"""
仓库清理自动化脚本
执行清理前会自动创建备份
"""

import os
import sys
import shutil
import subprocess
import platform
from datetime import datetime
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('cleanup.log'),
        logging.StreamHandler()
    ]
)

def run_command(command, check=True):
    """执行命令并记录日志"""
    try:
        logging.info(f"执行命令: {command}")
        result = subprocess.run(
            command,
            shell=True,
            check=check,
            capture_output=True,
            text=True
        )
        if result.stdout:
            logging.info(result.stdout)
        if result.stderr:
            logging.warning(result.stderr)
        return result
    except subprocess.CalledProcessError as e:
        logging.error(f"命令执行失败: {e}")
        raise

def create_backup():
    """创建仓库备份"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = f"backup_{timestamp}"
    
    logging.info(f"创建备份目录: {backup_dir}")
    os.makedirs(backup_dir, exist_ok=True)
    
    # 备份.git目录
    logging.info("备份.git目录")
    shutil.copytree(".git", os.path.join(backup_dir, ".git"))
    
    # 创建镜像克隆
    logging.info("创建仓库镜像")
    run_command(f"git clone --mirror . {backup_dir}/repo.git")
    
    return backup_dir

def setup_gitignore():
    """配置.gitignore"""
    gitignore_content = """
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
"""
    
    logging.info("更新.gitignore")
    with open(".gitignore", "w") as f:
        f.write(gitignore_content.strip())

def setup_git_lfs():
    """配置Git LFS"""
    try:
        run_command("git lfs install")
        
        # 配置要跟踪的文件类型
        lfs_tracks = [
            "*.pth", "*.weights", "*.h5", "*.onnx",
            "*.jpg", "*.png", "*.jpeg", "*.gif",
            "*.zip", "*.tar.gz", "*.rar"
        ]
        
        for pattern in lfs_tracks:
            run_command(f"git lfs track {pattern}")
        
        # 提交.gitattributes
        run_command("git add .gitattributes")
        run_command('git commit -m "Configure Git LFS tracking"')
        
    except subprocess.CalledProcessError as e:
        logging.error("Git LFS配置失败")
        raise

def clean_history():
    """清理Git历史"""
    # 下载BFG
    if not os.path.exists("bfg.jar"):
        logging.info("下载BFG工具")
        url = "https://repo1.maven.org/maven2/com/madgag/bfg/1.14.0/bfg-1.14.0.jar"
        run_command(f"curl -L {url} -o bfg.jar")
    
    # 使用BFG清理大文件
    logging.info("清理大文件")
    run_command("java -jar bfg.jar --strip-blobs-bigger-than 100M .")
    
    # 清理和压缩
    logging.info("压缩仓库")
    run_command("git reflog expire --expire=now --all")
    run_command("git gc --prune=now --aggressive")

def main():
    """主函数"""
    if not os.path.isdir(".git"):
        logging.error("当前目录不是Git仓库")
        sys.exit(1)
    
    try:
        # 1. 创建备份
        backup_dir = create_backup()
        logging.info(f"备份已创建在: {backup_dir}")
        
        # 2. 配置.gitignore
        setup_gitignore()
        
        # 3. 设置Git LFS
        setup_git_lfs()
        
        # 4. 清理历史
        clean_history()
        
        logging.info("""
清理完成！接下来的步骤：

1. 检查清理结果
   git status
   git lfs ls-files

2. 如果确认无误，强制推送更改
   git push origin --force --all
   git push origin --force --tags

3. 如果需要回滚，使用备份恢复
   cp -r {backup_dir}/.git .

更多详细说明请查看：CLEANUP_STEPS.md
""")
        
    except Exception as e:
        logging.error(f"清理过程中出错: {e}")
        logging.info(f"可以使用备份恢复: {backup_dir}")
        sys.exit(1)

if __name__ == "__main__":
    main()
