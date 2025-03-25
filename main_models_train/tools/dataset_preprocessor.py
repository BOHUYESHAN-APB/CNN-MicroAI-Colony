"""
Dataset preprocessing tool for colony detection datasets
菌落检测数据集预处理工具
"""
import os
import json
import shutil
from pathlib import Path
import cv2
import numpy as np
from typing import Dict, List, Tuple, Optional
from tqdm import tqdm
import time

class DatasetPreprocessor:
    """
    Preprocess datasets for colony detection training
    预处理菌落检测训练数据集
    """
    def __init__(self, 
                 img_size: Tuple[int, int] = None,  # None means keep original size
                 split_ratio: Dict[str, float] = {"train": 0.8, "val": 0.1, "test": 0.1},
                 max_memory_mb: int = 4096  # Maximum memory usage in MB
                ):
        """
        Initialize dataset preprocessor
        初始化数据集预处理器

        Args:
            img_size: Target image size (width, height)
            split_ratio: Dataset split ratios
            max_memory_mb: Maximum memory usage in MB
        """
        target_dir = "main_models_train/data/processed_dataset"
        # Validate input parameters
        if img_size is not None and (not isinstance(img_size, (tuple, list)) or len(img_size) != 2):
            raise ValueError("img_size must be None or a tuple of (width, height)")
        if sum(split_ratio.values()) != 1.0:
            raise ValueError("Split ratios must sum to 1.0")
            
        self.target_dir = Path(target_dir)
        self.img_size = img_size
        self.split_ratio = split_ratio
        self.annotation_id = 0
        self.max_memory_mb = max_memory_mb
        
        # Track memory usage
        self.current_memory_usage = 0
        
        # Create target directories
        for split in ["train", "val", "test"]:
            (self.target_dir / split / "images").mkdir(parents=True, exist_ok=True)
            (self.target_dir / split / "annotations").mkdir(parents=True, exist_ok=True)

    def process_agar_json(self, json_path: Path) -> List[Dict]:
        """Process AGAR format JSON annotation"""
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        annotations = []
        if isinstance(data, dict) and 'shapes' in data:
            # Handle labelme format
            img_height = data.get('imageHeight', 0)
            img_width = data.get('imageWidth', 0)
            
            for shape in data['shapes']:
                if shape['shape_type'] == 'circle':
                    # Convert circle to bbox
                    center = shape['points'][0]
                    radius = np.linalg.norm(np.array(shape['points'][0]) - np.array(shape['points'][1]))
                    x = center[0] - radius
                    y = center[1] - radius
                    width = height = radius * 2
                    
                    self.annotation_id += 1
                    annotations.append({
                        'id': self.annotation_id,
                        'image_id': int(json_path.stem),
                        'category_id': 1,
                        'bbox': [x, y, width, height],
                        'area': width * height,
                        'iscrowd': 0
                    })
                    
        return annotations

    def process_agar_dataset(self, source_dir: str, split: str = "train"):
        """Process AGAR demo dataset"""
        source_path = Path(source_dir)
        images = []
        annotations = []
        image_id = 0
        
        # Recursively find all image and json pairs
        for img_path in source_path.rglob('*.jpg'):
            json_path = img_path.with_suffix('.json')
            if not json_path.exists():
                continue
                
            # Read and process image
            img = cv2.imread(str(img_path))
            if img is None:
                print(f"Warning: Failed to read image: {img_path}")
                continue
                
            # Get original dimensions
            h, w = img.shape[:2]
            
            # Resize image if specified
            if self.img_size:
                img = cv2.resize(img, self.img_size)
                out_width, out_height = self.img_size
            else:
                out_width, out_height = w, h
                
            # Save processed image
            out_img_file = self.target_dir / split / "images" / img_path.name
            cv2.imwrite(str(out_img_file), img)
            
            # Process annotations
            image_id += 1
            images.append({
                "id": image_id,
                "file_name": img_path.name,
                "width": out_width,
                "height": out_height
            })
            
            # Scale factors for bbox coordinates
            scale_x = out_width / w
            scale_y = out_height / h
            
            # Process annotations
            annos = self.process_agar_json(json_path)
            for anno in annos:
                anno['image_id'] = image_id
                # Scale bbox coordinates
                bbox = anno['bbox']
                bbox[0] *= scale_x
                bbox[1] *= scale_y
                bbox[2] *= scale_x
                bbox[3] *= scale_y
                anno['area'] = bbox[2] * bbox[3]
                annotations.append(anno)
                
        # Save COCO format annotations
        coco_data = {
            "images": images,
            "annotations": annotations,
            "categories": [{
                "id": 1,
                "name": "colony",
                "supercategory": "bacteria"
            }]
        }
        
        anno_file = self.target_dir / split / "annotations" / "_annotations.coco.json"
        with open(anno_file, "w", encoding="utf-8") as f:
            json.dump(coco_data, f, indent=2, ensure_ascii=False)

    def process_coco_dataset(self, source_dir: str, subset: str = "train", batch_size: int = 32):
        """Process COCO format dataset"""
        source_dir = Path(source_dir)
        possible_paths = [
            source_dir / subset / "_annotations.coco.json",
            source_dir / "_annotations.coco.json",
            source_dir / f"{subset}_annotations.coco.json",
            source_dir / "train" / "_annotations.coco.json"  # 尝试查找train子目录
        ]
        
        anno_file = None
        for path in possible_paths:
            if path.exists():
                anno_file = path
                print(f"找到标注文件: {path}")
                break
                
        if anno_file is None:
            raise FileNotFoundError(f"未找到标注文件: {source_dir}")
            
        with open(anno_file, "r", encoding="utf-8") as f:
            coco_data = json.load(f)
            
        images = {}
        annotations = {}
        
        # Group annotations by image
        for ann in coco_data.get("annotations", []):
            img_id = ann["image_id"]
            if img_id not in annotations:
                annotations[img_id] = []
            annotations[img_id].append(ann)
            
        # Process images in batches
        total_images = len(coco_data["images"])
        pbar = tqdm(total=total_images, desc=f"处理{subset}数据集")
        
        for i in range(0, total_images, batch_size):
            batch = coco_data["images"][i:i+batch_size]
            for img_info in batch:
                img_id = img_info["id"]
                img_file = source_dir / img_info["file_name"]
            
                if not img_file.exists():
                    # Try finding the image in the subset directory
                    img_file = source_dir / subset / img_info["file_name"]
                    if not img_file.exists():
                        # 尝试在train子目录中查找
                        img_file = source_dir / "train" / img_info["file_name"]
                        if not img_file.exists():
                            print(f"警告: 未找到图片文件: {img_info['file_name']}")
                            continue
                
                img = cv2.imread(str(img_file))
                if img is None:
                    print(f"警告: 读取图片失败: {img_file}")
                    continue
                    
                # Resize image if specified
                if self.img_size:
                    img = cv2.resize(img, self.img_size)
                    out_width, out_height = self.img_size
                else:
                    out_width, out_height = img.shape[1], img.shape[0]
                
                # Scale annotations
                scale_x = out_width / img_info["width"]
                scale_y = out_height / img_info["height"]
                
                if img_id in annotations:
                    for ann in annotations[img_id]:
                        bbox = ann["bbox"]
                        bbox[0] *= scale_x
                        bbox[1] *= scale_y
                        bbox[2] *= scale_x
                        bbox[3] *= scale_y
                        ann["area"] = bbox[2] * bbox[3]
                
                    # Save processed image
                    out_img_file = self.target_dir / subset / "images" / img_info["file_name"]
                    try:
                        cv2.imwrite(str(out_img_file), img)
                    except Exception as e:
                        print(f"\n保存图片出错 {img_info['file_name']}: {e}")
                        continue
                    
                    pbar.update(1)
                
            # Save checkpoint after each batch
            if i % (batch_size * 10) == 0:  # Save every 10 batches
                checkpoint_file = self.target_dir / f"{subset}_preprocessing_checkpoint.json"
                with open(checkpoint_file, "w") as f:
                    json.dump({"processed_count": i + len(batch)}, f)
            
            images[img_id] = {
                **img_info,
                "width": out_width,
                "height": out_height
            }
            
        # Save processed annotations
        processed_anno = {
            "images": list(images.values()),
            "annotations": [a for anns in annotations.values() for a in anns],
            "categories": coco_data.get("categories", [{
                "id": 1,
                "name": "colony",
                "supercategory": "bacteria"
            }])
        }
        
        out_anno_file = self.target_dir / subset / "annotations" / "_annotations.coco.json"
        with open(out_anno_file, "w", encoding="utf-8") as f:
            json.dump(processed_anno, f, indent=2, ensure_ascii=False)

    def process_mixed_dataset(self, source_dirs: List[str], progress_callback=None, batch_size: int = 32):
        """Process mixed datasets"""
        total_processed = 0
        total_files = sum(len(list(Path(d).rglob('*.[jp][pn][g]'))) for d in source_dirs)

        for source_dir in source_dirs:
            source_path = Path(source_dir)
            if not source_path.exists():
                print(f"错误: 数据集目录不存在: {source_dir}")
                continue

            # 首先查找所有包含训练数据的子目录
            dataset_dirs = []
            for subdir in source_path.glob("**/train"):
                if subdir.is_dir() and list(subdir.glob("*.jpg")) or list(subdir.glob("*.png")):
                    dataset_dirs.append(subdir.parent)
            
            if not dataset_dirs:
                print(f"警告: 在{source_dir}中未找到任何训练数据")
                continue
                
            print(f"找到{len(dataset_dirs)}个数据集:")
            for d in dataset_dirs:
                print(f"  - {d.name}")
            
            # 处理每个数据集
            for dataset_path in dataset_dirs:
                print(f"\n处理数据集: {dataset_path.name}")
                with tqdm(desc="检查数据集结构") as pbar:
                    subsets = []
                    if (dataset_path / "train").exists():
                        subsets.append("train")
                    pbar.update(1)
                    if (dataset_path / "valid").exists():
                        subsets.append("valid")
                    pbar.update(1)
                    if (dataset_path / "test").exists():
                        subsets.append("test")
                    pbar.update(1)
                
                print(f"找到数据分割: {', '.join(subsets)}")
                
                # 检查AGAR格式还是COCO格式
                is_agar = "AGAR_demo" in str(dataset_path)
                if is_agar:
                    print(f"处理AGAR数据集: {dataset_path}")
                    try:
                        self.process_agar_dataset(str(dataset_path), "train")
                        total_processed += len(list(dataset_path.rglob("*.jpg")))
                    except Exception as e:
                        print(f"处理AGAR数据集出错: {e}")
                        continue
                else:
                    print(f"处理COCO数据集: {dataset_path}")
                    try:
                        for subset in subsets:
                            print(f"\n处理{subset}数据集...")
                            self.process_coco_dataset(str(dataset_path), subset, batch_size)
                            if progress_callback:
                                progress_callback(dataset_path / subset)
                            total_processed += len(list((dataset_path / subset).glob("*.jpg")))
                    except KeyboardInterrupt:
                        print("\n处理被用户中断，保存当前进度...")
                        return
                    except Exception as e:
                        print(f"处理{subset}数据集出错: {e}")
                
                # 检查AGAR格式(单图单JSON)
                is_agar = False
                json_files = list(source_path.rglob('*.json'))
                if json_files:
                    try:
                        with open(json_files[0], 'r') as f:
                            data = json.load(f)
                            if isinstance(data, dict) and 'shapes' in data:
                                is_agar = True
                    except:
                        pass

                # 处理数据集
                if is_agar:
                    print(f"处理AGAR数据集: {source_dir}")
                    try:
                        for split in ["train", "val", "test"]:
                            self.process_agar_dataset(str(source_path), split)
                            if progress_callback:
                                progress_callback(source_path)
                            total_processed += 1
                    except Exception as e:
                        print(f"处理AGAR数据集出错 {source_dir}: {e}")
                        continue
                else:
                    print(f"处理COCO数据集: {source_dir}")
                    for subset in subsets:
                        try:
                            print(f"\n处理{subset}数据集...")
                            self.process_coco_dataset(str(source_path), subset, batch_size)
                            total_processed += 1
                            if progress_callback:
                                progress_callback(source_path / subset)
                        except KeyboardInterrupt:
                            print("\n处理被用户中断，保存当前进度...")
                            return
                        except Exception as e:
                            print(f"处理{subset}数据集出错: {e}")
                
        print(f"\n成功处理 {total_processed}/{total_files} 个文件")

    def validate_dataset(self):
        """Validate the preprocessed dataset"""
        for split in ["train", "val", "test"]:
            anno_file = self.target_dir / split / "annotations" / "_annotations.coco.json"
            if not anno_file.exists():
                print(f"警告: 未找到{split}集的标注文件")
                continue
                
            with open(anno_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            for img in data["images"]:
                img_file = self.target_dir / split / "images" / img["file_name"]
                if not img_file.exists():
                    print(f"警告: {split}集中缺少图片文件: {img['file_name']}")
                    continue
                    
                actual_img = cv2.imread(str(img_file))
                if actual_img.shape[:2] != (img["height"], img["width"]):
                    print(f"警告: {split}集中图片尺寸不匹配: {img['file_name']}")
                    
            image_ids = {img["id"] for img in data["images"]}
            for ann in data["annotations"]:
                if ann["image_id"] not in image_ids:
                    print(f"警告: {split}集中标注引用了不存在的图片")
                    
            print(f"验证{split}集:")
            print(f"  图片数量: {len(data['images'])}")
            print(f"  标注数量: {len(data['annotations'])}")
            print(f"  类别数量: {len(data['categories'])}")

if __name__ == "__main__":
    preprocessor = DatasetPreprocessor(
        img_size=None  # 保持原始图片尺寸
    )
    
    # Hardcoded source path from user instruction
    source_path = "D:/train/full_dataset"
    if not Path(source_path).exists():
        raise FileNotFoundError(f"Source dataset path not found: {source_path}")
    
    preprocessor.process_mixed_dataset([source_path])
    preprocessor.validate_dataset()
