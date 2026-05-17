#!/usr/bin/env python3
"""分析训练数据集的类别和规模"""
import json
from pathlib import Path
from collections import defaultdict

train_root = Path("G:/train")

datasets_info = []

for dataset_dir in sorted(train_root.iterdir()):
    if not dataset_dir.is_dir():
        continue

    train_json = dataset_dir / "train" / "_annotations.coco.json"
    valid_json = dataset_dir / "valid" / "_annotations.coco.json"

    if not train_json.exists():
        continue

    # 读取训练集标注
    with open(train_json, 'r', encoding='utf-8') as f:
        train_data = json.load(f)

    # 读取验证集标注（如果存在）
    valid_data = None
    if valid_json.exists():
        with open(valid_json, 'r', encoding='utf-8') as f:
            valid_data = json.load(f)

    # 统计信息
    info = {
        'name': dataset_dir.name,
        'train_images': len(train_data['images']),
        'train_annotations': len(train_data['annotations']),
        'valid_images': len(valid_data['images']) if valid_data else 0,
        'valid_annotations': len(valid_data['annotations']) if valid_data else 0,
        'categories': train_data['categories'],
        'num_categories': len(train_data['categories'])
    }

    datasets_info.append(info)

# 打印报告
print("=" * 80)
print("训练数据集分析报告")
print("=" * 80)

for info in datasets_info:
    print(f"\n数据集: {info['name']}")
    print(f"  训练集: {info['train_images']} 张图像, {info['train_annotations']} 个标注")
    print(f"  验证集: {info['valid_images']} 张图像, {info['valid_annotations']} 个标注")
    print(f"  类别数: {info['num_categories']}")
    print(f"  类别列表:")
    for cat in info['categories']:
        print(f"    - {cat['id']}: {cat['name']}")

print("\n" + "=" * 80)
print("推荐数据集（按规模排序）:")
print("=" * 80)

sorted_datasets = sorted(datasets_info, key=lambda x: x['train_images'], reverse=True)
for i, info in enumerate(sorted_datasets[:5], 1):
    total_images = info['train_images'] + info['valid_images']
    total_annots = info['train_annotations'] + info['valid_annotations']
    print(f"{i}. {info['name']}")
    print(f"   总计: {total_images} 张图像, {total_annots} 个标注, {info['num_categories']} 个类别")
