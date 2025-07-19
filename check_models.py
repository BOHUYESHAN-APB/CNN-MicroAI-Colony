#!/usr/bin/env python3
"""
菌落检测模型对比架构完整性检查脚本
"""

import os
import sys
from pathlib import Path

# 模型列表
MODELS = [
    'faster_rcnn_resnet50',
    'faster_rcnn_resnet101', 
    'cascade_rcnn',
    'detectors',
    'mask_rcnn',
    'htc',
    'yolov5',
    'yolov8',
    'yolov11',
    'yolov12',
    'yolov13',
    'ppyolo',
    'unet'
]

# 标准目录结构
STANDARD_DIRS = [
    'configs',
    'src',
    'src/data',
    'src/models', 
    'src/utils',
    'checkpoints',
    'model_output'
]

# 标准文件
STANDARD_FILES = [
    'src/train.py',
    'src/data/dataset.py',
    'src/models/colony_detector.py',
    'README.md'
]

def check_model_structure(model_name, base_path='models-train/comparison'):
    """检查单个模型的完整性"""
    model_path = Path(base_path) / model_name
    print(f"\n=== 检查模型: {model_name} ===")
    
    # 检查目录
    missing_dirs = []
    for dir_path in STANDARD_DIRS:
        full_path = model_path / dir_path
        if not full_path.exists():
            missing_dirs.append(dir_path)
            print(f"  ❌ 缺失目录: {dir_path}")
        else:
            print(f"  ✅ 目录存在: {dir_path}")
    
    # 检查文件
    missing_files = []
    for file_path in STANDARD_FILES:
        full_path = model_path / file_path
        if not full_path.exists():
            missing_files.append(file_path)
            print(f"  ❌ 缺失文件: {file_path}")
        else:
            print(f"  ✅ 文件存在: {file_path}")
    
    # 检查配置文件
    configs_dir = model_path / 'configs'
    config_files = []
    if configs_dir.exists():
        config_files = list(configs_dir.glob('*.py')) + list(configs_dir.glob('*.yaml')) + list(configs_dir.glob('*.json'))
        print(f"  📁 配置文件: {len(config_files)} 个")
        for cf in config_files:
            print(f"    - {cf.name}")
    
    # 总结
    total_missing = len(missing_dirs) + len(missing_files)
    if total_missing == 0:
        print(f"  🎉 {model_name} 结构完整")
    else:
        print(f"  ⚠️ {model_name} 缺失 {total_missing} 项")
    
    return {
        'model': model_name,
        'missing_dirs': missing_dirs,
        'missing_files': missing_files,
        'config_files': len(config_files),
        'is_complete': total_missing == 0
    }

def main():
    """主函数"""
    print("=== 菌落检测模型对比架构完整性检查 ===")
    
    base_path = 'models-train/comparison'
    if not os.path.exists(base_path):
        print(f"错误: 基础路径 {base_path} 不存在")
        return
    
    results = []
    for model in MODELS:
        result = check_model_structure(model, base_path)
        results.append(result)
    
    # 汇总报告
    print("\n" + "="*50)
    print("=== 汇总报告 ===")
    
    complete_models = [r for r in results if r['is_complete']]
    incomplete_models = [r for r in results if not r['is_complete']]
    
    print(f"总模型数: {len(MODELS)}")
    print(f"完整模型: {len(complete_models)}")
    print(f"不完整模型: {len(incomplete_models)}")
    
    if incomplete_models:
        print("\n需要补全的模型:")
        for model in incomplete_models:
            print(f"  - {model['model']}: 缺失 {len(model['missing_dirs'])} 目录, {len(model['missing_files'])} 文件")
    
    # 详细缺失信息
    if incomplete_models:
        print("\n详细缺失信息:")
        for model in incomplete_models:
            print(f"\n{model['model']}:")
            for d in model['missing_dirs']:
                print(f"  目录: {d}")
            for f in model['missing_files']:
                print(f"  文件: {f}")

if __name__ == '__main__':
    main()