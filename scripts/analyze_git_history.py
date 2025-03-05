#!/usr/bin/env python3
"""
Git历史分析脚本
用于分析Git仓库历史中的大文件
"""

import os
import sys
import subprocess
import json
from collections import defaultdict

def get_git_root():
    """获取Git仓库根目录"""
    try:
        git_root = subprocess.check_output(
            ['git', 'rev-parse', '--show-toplevel'],
            universal_newlines=True
        ).strip()
        return git_root
    except subprocess.CalledProcessError:
        print("错误: 当前目录不是Git仓库")
        sys.exit(1)

def analyze_git_objects():
    """分析Git对象大小"""
    try:
        # 获取所有Git对象
        cmd = (
            'git rev-list --objects --all | '
            'git cat-file --batch-check="%(objecttype) %(objectname) %(objectsize) %(rest)"'
        )
        output = subprocess.check_output(cmd, shell=True, universal_newlines=True)
    except subprocess.CalledProcessError:
        print("错误: 无法分析Git对象")
        sys.exit(1)

    # 解析输出
    objects = defaultdict(list)
    for line in output.splitlines():
        parts = line.split()
        if len(parts) >= 4 and parts[0] == 'blob':
            obj_type, obj_hash, size, *name_parts = parts
            name = ' '.join(name_parts)
            size_mb = int(size) / (1024 * 1024)  # 转换为MB
            objects[name].append((obj_hash, size_mb))

    return objects

def generate_report(objects, min_size_mb=1):
    """生成分析报告"""
    report = ["=== Git历史大文件分析报告 ===\n"]
    
    # 按文件大小排序
    sorted_files = sorted(
        [(name, max(versions, key=lambda x: x[1])) 
         for name, versions in objects.items()],
        key=lambda x: x[1][1],
        reverse=True
    )

    # 筛选大文件
    large_files = [(name, version) for name, version in sorted_files 
                   if version[1] >= min_size_mb]

    if not large_files:
        report.append("未发现大于 {}MB 的文件".format(min_size_mb))
        return '\n'.join(report)

    total_size = 0
    for name, (obj_hash, size) in large_files:
        report.append(f"文件: {name}")
        report.append(f"  大小: {size:.2f}MB")
        report.append(f"  对象Hash: {obj_hash}")
        report.append("")
        total_size += size

    report.append(f"\n总计大文件大小: {total_size:.2f}MB")
    report.append("\n清理建议：")
    report.append("1. 使用以下命令清理特定文件：")
    report.append("   git filter-repo --invert-paths --path-match 'path/to/large/file'")
    report.append("\n2. 或使用BFG清理所有大文件：")
    report.append("   java -jar bfg.jar --strip-blobs-bigger-than 100M .")
    
    return '\n'.join(report)

def main():
    """主函数"""
    if len(sys.argv) == 2:
        try:
            min_size = float(sys.argv[1])
        except ValueError:
            print("错误: 请提供有效的大小阈值（MB）")
            sys.exit(1)
    else:
        min_size = 1  # 默认1MB

    git_root = get_git_root()
    os.chdir(git_root)
    
    print("分析Git仓库：", git_root)
    objects = analyze_git_objects()
    report = generate_report(objects, min_size)
    
    # 保存报告
    report_file = 'git_analysis_report.txt'
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n分析完成！报告已保存到：{report_file}")

if __name__ == "__main__":
    main()
