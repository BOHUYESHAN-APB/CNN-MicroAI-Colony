#!/usr/bin/env python3
"""
仓库分析和清理脚本
用于分析仓库中的大文件并生成清理建议
"""

import os
import sys
from pathlib import Path
import json
from collections import defaultdict
import platform
import locale

# 设置默认编码
if platform.system() == 'Windows':
    # 使用UTF-8编码
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# 文件大小阈值（MB）
SIZE_THRESHOLDS = {
    "large": 100,    # GitHub单文件限制
    "medium": 50,    # 需要注意的文件
    "small": 10      # 可以保留的文件
}

# 排除的目录
EXCLUDED_DIRS = {
    '.git',          # Git目录
    'venv',          # 虚拟环境
    'env',           # 虚拟环境
    'backup',        # 备份目录
    '__pycache__',   # Python缓存
    'node_modules'   # Node.js模块
}

# 不应删除的重要文件扩展名
ESSENTIAL_EXTENSIONS = {
    '.py',    # Python源代码
    '.md',    # 文档
    '.txt',   # 文本文件
    '.yml',   # 配置文件
    '.yaml',  # 配置文件
    '.json',  # 配置文件
    '.sh',    # 脚本
    '.bat'    # Windows脚本
}

# 可以清理的临时文件扩展名
TEMP_EXTENSIONS = {
    '.pyc',   # Python编译文件
    '.pyo',   # Python优化文件
    '.pyd',   # Python动态链接库
    '.log',   # 日志文件
    '.tmp',   # 临时文件
    '.temp',  # 临时文件
    '.bak'    # 备份文件
}

def should_exclude_dir(path):
    """检查是否应该排除该目录"""
    return any(excluded in path for excluded in EXCLUDED_DIRS)

def get_file_size(file_path):
    """获取文件大小（MB）"""
    return os.path.getsize(file_path) / (1024 * 1024)

def analyze_directory(directory):
    """分析目录中的文件"""
    file_sizes = defaultdict(list)
    
    for root, dirs, files in os.walk(directory):
        # 排除特定目录
        if should_exclude_dir(root):
            continue
        
        for file in files:
            file_path = os.path.join(root, file)
            try:
                file_size = get_file_size(file_path)
                
                # 根据大小分类
                if file_size >= SIZE_THRESHOLDS["large"]:
                    file_sizes["large"].append((file_path, file_size))
                elif file_size >= SIZE_THRESHOLDS["medium"]:
                    file_sizes["medium"].append((file_path, file_size))
                elif file_size >= SIZE_THRESHOLDS["small"]:
                    file_sizes["small"].append((file_path, file_size))
            except (OSError, IOError) as e:
                print(f"警告: 无法读取文件 {file_path}: {e}")
    
    return file_sizes

def generate_cleanup_suggestions(file_sizes):
    """生成清理建议"""
    suggestions = {
        "must_move": [],     # 必须移动到外部存储的文件
        "consider_move": [], # 考虑移动的文件
        "can_delete": [],    # 可以删除的临时文件
        "review": []         # 需要人工审查的文件
    }
    
    for size_cat in ["large", "medium", "small"]:
        for file_path, size in file_sizes[size_cat]:
            ext = os.path.splitext(file_path)[1].lower()
            
            if ext in TEMP_EXTENSIONS:
                suggestions["can_delete"].append((file_path, size))
            elif ext in ESSENTIAL_EXTENSIONS:
                if size >= SIZE_THRESHOLDS["large"]:
                    suggestions["review"].append((file_path, size))
            elif size >= SIZE_THRESHOLDS["large"]:
                suggestions["must_move"].append((file_path, size))
            elif size >= SIZE_THRESHOLDS["medium"]:
                suggestions["consider_move"].append((file_path, size))
    
    return suggestions

def format_size(size_mb):
    """格式化文件大小显示"""
    if size_mb >= 1024:
        return f"{size_mb/1024:.2f} GB"
    return f"{size_mb:.2f} MB"

def generate_report(suggestions):
    """生成分析报告"""
    report = ["=== 仓库大文件分析报告 ===\n"]
    
    total_size = 0
    
    report.append("必须移动到外部存储的文件:")
    for file_path, size in suggestions["must_move"]:
        report.append(f"- {file_path} ({format_size(size)})")
        total_size += size
    
    report.append("\n建议考虑移动的文件:")
    for file_path, size in suggestions["consider_move"]:
        report.append(f"- {file_path} ({format_size(size)})")
        total_size += size
    
    report.append("\n可以删除的临时文件:")
    for file_path, size in suggestions["can_delete"]:
        report.append(f"- {file_path} ({format_size(size)})")
        total_size += size
    
    report.append("\n需要人工审查的大文件:")
    for file_path, size in suggestions["review"]:
        report.append(f"- {file_path} ({format_size(size)})")
        total_size += size
    
    report.append(f"\n总计大文件大小: {format_size(total_size)}")
    
    return "\n".join(report)

def generate_cleanup_script(suggestions, is_windows=False):
    """生成清理脚本"""
    script_lines = []
    
    if is_windows:
        script_lines.extend([
            '@echo off',
            'chcp 65001 >nul',  # 设置UTF-8编码
            ':: 自动生成的清理脚本 - 使用前请仔细审查！',
            'mkdir backup 2>nul',
            '',
            ':: 检查目录是否存在',
            'if not exist backup\\ (',
            '    echo 错误：无法创建备份目录',
            '    exit /b 1',
            ')',
            ''
        ])
        # 移动大文件
        script_lines.append(':: 移动大文件到备份目录')
        for file_path, _ in suggestions["must_move"]:
            backup_path = os.path.join("backup", os.path.basename(file_path))
            script_lines.extend([
                f'if exist "{file_path}" (',
                f'    echo 移动文件：{file_path}',
                f'    move "{file_path}" "{backup_path}"',
                ') else (',
                f'    echo 警告：文件不存在 - {file_path}',
                ')'
            ])
        
        # 删除临时文件
        script_lines.append('\n:: 删除临时文件')
        for file_path, _ in suggestions["can_delete"]:
            script_lines.extend([
                f'if exist "{file_path}" (',
                f'    echo 删除文件：{file_path}',
                f'    del /f "{file_path}"',
                ') else (',
                f'    echo 警告：文件不存在 - {file_path}',
                ')'
            ])
    else:
        script_lines.extend([
            '#!/bin/bash',
            '# 自动生成的清理脚本 - 使用前请仔细审查！',
            'mkdir -p ./backup',
            '',
            '# 检查目录是否存在',
            'if [ ! -d "backup" ]; then',
            '    echo "错误：无法创建备份目录"',
            '    exit 1',
            'fi',
            ''
        ])
        # 移动大文件
        script_lines.append('# 移动大文件到备份目录')
        for file_path, _ in suggestions["must_move"]:
            backup_path = os.path.join("backup", os.path.basename(file_path))
            script_lines.extend([
                f'if [ -f "{file_path}" ]; then',
                f'    echo "移动文件：{file_path}"',
                f'    mv "{file_path}" "{backup_path}"',
                'else',
                f'    echo "警告：文件不存在 - {file_path}"',
                'fi'
            ])
        
        # 删除临时文件
        script_lines.append('\n# 删除临时文件')
        for file_path, _ in suggestions["can_delete"]:
            script_lines.extend([
                f'if [ -f "{file_path}" ]; then',
                f'    echo "删除文件：{file_path}"',
                f'    rm -f "{file_path}"',
                'else',
                f'    echo "警告：文件不存在 - {file_path}"',
                'fi'
            ])
    
    return '\n'.join(script_lines)

def main():
    """主函数"""
    if len(sys.argv) != 2:
        print("用法: python analyze_repo.py <repository_path>")
        sys.exit(1)
    
    repo_path = sys.argv[1]
    if not os.path.isdir(repo_path):
        print(f"错误: {repo_path} 不是有效目录")
        sys.exit(1)
    
    print(f"分析仓库: {repo_path}")
    file_sizes = analyze_directory(repo_path)
    suggestions = generate_cleanup_suggestions(file_sizes)
    
    # 生成报告
    report = generate_report(suggestions)
    with open('analysis_report.txt', 'w', encoding='utf-8') as f:
        f.write(report)
    
    # 生成清理脚本
    is_windows = platform.system() == 'Windows'
    script = generate_cleanup_script(suggestions, is_windows)
    script_name = 'cleanup_script.bat' if is_windows else 'cleanup_script.sh'
    
    with open(script_name, 'w', encoding='utf-8', newline='\n') as f:
        f.write(script)
    
    # 如果是Linux/macOS，设置脚本可执行权限
    if not is_windows:
        os.chmod(script_name, 0o755)
    
    print("\n分析完成！生成的文件：")
    print(f"- 分析报告：analysis_report.txt")
    print(f"- 清理脚本：{script_name}")
    print("\n注意: 执行清理前请仔细检查脚本内容！")

if __name__ == "__main__":
    main()
