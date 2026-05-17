#!/usr/bin/env python3
"""将COCO格式数据集转换为YOLO11格式"""
import json
import shutil
from pathlib import Path

def coco_to_yolo(coco_json_path, output_dir, split_name):
    """转换单个COCO JSON到YOLO格式"""
    with open(coco_json_path, 'r', encoding='utf-8') as f:
        coco = json.load(f)

    output_dir = Path(output_dir)
    images_dir = output_dir / 'images' / split_name
    labels_dir = output_dir / 'labels' / split_name
    images_dir.mkdir(parents=True, exist_ok=True)
    labels_dir.mkdir(parents=True, exist_ok=True)

    # 图像ID到信息映射
    img_id_to_info = {img['id']: img for img in coco['images']}

    # 按图像分组标注
    img_annotations = {}
    for ann in coco['annotations']:
        img_id = ann['image_id']
        if img_id not in img_annotations:
            img_annotations[img_id] = []
        img_annotations[img_id].append(ann)

    # 转换每张图像
    for img_id, anns in img_annotations.items():
        img_info = img_id_to_info[img_id]
        img_w, img_h = img_info['width'], img_info['height']
        img_filename = img_info['file_name']

        # 复制图像
        src_img = Path(coco_json_path).parent / img_filename
        if src_img.exists():
            shutil.copy(src_img, images_dir / img_filename)

        # 写入YOLO标注
        label_path = labels_dir / f"{Path(img_filename).stem}.txt"
        with open(label_path, 'w') as f:
            for ann in anns:
                # COCO: [x, y, width, height] -> YOLO: [class x_center y_center width height] (归一化)
                x, y, w, h = ann['bbox']
                x_center = (x + w / 2) / img_w
                y_center = (y + h / 2) / img_h
                w_norm = w / img_w
                h_norm = h / img_h

                class_id = ann['category_id'] - 1  # YOLO从0开始
                f.write(f"{class_id} {x_center:.6f} {y_center:.6f} {w_norm:.6f} {h_norm:.6f}\n")

    return len(img_annotations)

def convert_dataset(dataset_path, output_path):
    """转换完整数据集"""
    dataset_path = Path(dataset_path)
    output_path = Path(output_path)

    print(f"转换数据集: {dataset_path.name}")

    # 读取类别信息
    train_json = dataset_path / 'train' / '_annotations.coco.json'
    with open(train_json, 'r', encoding='utf-8') as f:
        coco = json.load(f)

    categories = coco['categories']
    class_names = [cat['name'] for cat in sorted(categories, key=lambda x: x['id'])]

    # 转换训练集
    print("  转换训练集...")
    train_count = coco_to_yolo(train_json, output_path, 'train')
    print(f"    OK {train_count} 张图像")

    # 转换验证集
    valid_json = dataset_path / 'valid' / '_annotations.coco.json'
    if valid_json.exists():
        print("  转换验证集...")
        valid_count = coco_to_yolo(valid_json, output_path, 'val')
        print(f"    OK {valid_count} 张图像")

    # 生成data.yaml
    yaml_content = f"""# YOLO11训练配置
path: {output_path.absolute()}
train: images/train
val: images/val

nc: {len(class_names)}
names: {class_names}
"""

    with open(output_path / 'data.yaml', 'w', encoding='utf-8') as f:
        f.write(yaml_content)

    print(f"  OK 生成 data.yaml")
    print(f"  类别: {class_names}")

if __name__ == "__main__":
    # 转换Fase.v2i数据集（小数据集）
    print("=" * 60)
    convert_dataset(
        "G:/train/Fase.v2i.coco-mmdetection",
        "G:/train/yolo11_fase_v2"
    )

    print("\n" + "=" * 60)
    # 转换new colony数据集（大数据集）
    convert_dataset(
        "G:/train/new colony.v1i.coco-mmdetection",
        "G:/train/yolo11_new_colony"
    )

    print("\n" + "=" * 60)
    print("转换完成！")
    print("\n上传到启智平台的目录:")
    print("  1. G:/train/yolo11_fase_v2/")
    print("  2. G:/train/yolo11_new_colony/")
