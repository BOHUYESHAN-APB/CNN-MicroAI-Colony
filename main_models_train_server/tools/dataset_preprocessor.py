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

class DatasetPreprocessor:
    """
    Preprocess datasets for colony detection training
    预处理菌落检测训练数据集
    """
    def __init__(self, 
                 target_dir: str,
                 img_size: Tuple[int, int] = (1280, 1280),
                 split_ratio: Dict[str, float] = {"train": 0.7, "val": 0.15, "test": 0.15}
                ):
        """
        Initialize dataset preprocessor
        初始化数据集预处理器

        Args:
            target_dir: Target directory for preprocessed dataset
                       预处理后的数据存储目录
            img_size: Target image size (width, height)
                     目标图片尺寸（宽，高）
            split_ratio: Dataset split ratios for train/val/test
                        训练/验证/测试集的划分比例
        """
        self.target_dir = Path(target_dir)
        self.img_size = img_size
        self.split_ratio = split_ratio
        
        # Create target directories
        # 创建目标目录
        for split in ["train", "val", "test"]:
            (self.target_dir / split / "images").mkdir(parents=True, exist_ok=True)
            (self.target_dir / split / "annotations").mkdir(parents=True, exist_ok=True)

    def process_image_folder(self, folder_path: str, split: str = "train"):
        """
        Process a folder of images without annotations
        处理没有标注的图片文件夹

        Args:
            folder_path: Path to the folder containing images
                        包含图片的文件夹路径
            split: Dataset split to save the images (train/val/test)
                  保存图片的数据集划分（训练/验证/测试）
        """
        folder_path = Path(folder_path)
        if not folder_path.exists():
            raise FileNotFoundError(f"Folder not found: {folder_path}")

        # Supported image extensions
        # 支持的图片格式
        img_extensions = ['.jpg', '.jpeg', '.png', '.bmp']
        
        # Collect and process images
        # 收集并处理图片
        processed_images = []
        image_id = 0
        
        for img_path in folder_path.rglob('*'):
            if img_path.suffix.lower() not in img_extensions:
                continue
                
            try:
                # Read and process image
                # 读取并处理图片
                img = cv2.imread(str(img_path))
                if img is None:
                    print(f"Warning: Failed to read image: {img_path}")
                    continue
                    
                # Resize image
                # 调整图片大小
                img = cv2.resize(img, self.img_size)
                
                # Save processed image
                # 保存处理后的图片
                out_img_file = self.target_dir / split / "images" / img_path.name
                cv2.imwrite(str(out_img_file), img)
                
                # Add to processed images list
                # 添加到已处理图片列表
                processed_images.append({
                    "id": image_id,
                    "file_name": img_path.name,
                    "width": self.img_size[0],
                    "height": self.img_size[1]
                })
                
                image_id += 1
                
            except Exception as e:
                print(f"Error processing image {img_path}: {e}")
                continue
        
        # Create dummy annotations file
        # 创建空标注文件
        anno_data = {
            "images": processed_images,
            "annotations": [],  # Empty annotations
            "categories": [{
                "id": 1,
                "name": "colony",
                "supercategory": "bacteria"
            }]
        }
        
        # Save annotations
        # 保存标注
        out_anno_file = self.target_dir / split / "annotations" / "_annotations.coco.json"
        with open(out_anno_file, "w", encoding="utf-8") as f:
            json.dump(anno_data, f, indent=2, ensure_ascii=False)
            
        return len(processed_images)

    def process_coco_dataset(self, source_dir: str, subset: str = "train"):
        """
        Process COCO format dataset
        处理COCO格式数据集

        Args:
            source_dir: Source directory containing COCO format dataset
                       源数据目录（包含COCO格式数据集）
            subset: Dataset subset to process (train/val/test)
                   要处理的数据集子集（训练/验证/测试）
        """
        source_dir = Path(source_dir)
        # Load COCO annotations
        # 加载COCO标注文件
        anno_file = source_dir / subset / "_annotations.coco.json"
        if not anno_file.exists():
            raise FileNotFoundError(f"Annotation file not found: {anno_file}")
            
        with open(anno_file, "r", encoding="utf-8") as f:
            coco_data = json.load(f)
            
        # Process images and annotations
        # 处理图片和标注
        images = {}  # image_id -> image_info
        annotations = {}  # image_id -> [annotations]
        
        # Group annotations by image
        # 按图片分组标注
        for ann in coco_data["annotations"]:
            img_id = ann["image_id"]
            if img_id not in annotations:
                annotations[img_id] = []
            annotations[img_id].append(ann)
            
        # Process each image
        # 处理每张图片
        for img_info in coco_data["images"]:
            img_id = img_info["id"]
            img_file = source_dir / subset / img_info["file_name"]
            
            if not img_file.exists():
                print(f"Warning: Image file not found: {img_file}")
                continue
                
            # Read and resize image
            # 读取并调整图片大小
            img = cv2.imread(str(img_file))
            if img is None:
                print(f"Warning: Failed to read image: {img_file}")
                continue
                
            img = cv2.resize(img, self.img_size)
            
            # Scale annotations
            # 缩放标注框
            scale_x = self.img_size[0] / img_info["width"]
            scale_y = self.img_size[1] / img_info["height"]
            
            if img_id in annotations:
                for ann in annotations[img_id]:
                    bbox = ann["bbox"]
                    bbox[0] *= scale_x  # x
                    bbox[1] *= scale_y  # y
                    bbox[2] *= scale_x  # width
                    bbox[3] *= scale_y  # height
            
            # Save processed data
            # 保存处理后的数据
            out_img_file = self.target_dir / subset / "images" / img_info["file_name"]
            cv2.imwrite(str(out_img_file), img)
            
            images[img_id] = {
                **img_info,
                "width": self.img_size[0],
                "height": self.img_size[1]
            }
            
        # Save processed annotations
        # 保存处理后的标注
        processed_anno = {
            "images": list(images.values()),
            "annotations": [a for anns in annotations.values() for a in anns],
            "categories": coco_data["categories"]
        }
        
        out_anno_file = self.target_dir / subset / "annotations" / "_annotations.coco.json"
        with open(out_anno_file, "w", encoding="utf-8") as f:
            json.dump(processed_anno, f, indent=2, ensure_ascii=False)

    def process_mixed_dataset(self, source_dirs: List[str]):
        """
        Process a mixed dataset containing both COCO and non-COCO data
        处理包含COCO和非COCO数据的混合数据集

        Args:
            source_dirs: List of source dataset directories
                       源数据集目录列表
        """
        for source_dir in source_dirs:
            source_path = Path(source_dir)
            
            # Check if it's a COCO dataset
            # 检查是否为COCO数据集
            is_coco = False
            for subset in ["train", "valid", "test"]:
                if (source_path / subset / "_annotations.coco.json").exists():
                    is_coco = True
                    break
            
            if is_coco:
                print(f"Processing COCO dataset: {source_dir}")
                # Process COCO dataset
                # 处理COCO数据集
                for subset in ["train", "valid", "test"]:
                    try:
                        self.process_coco_dataset(source_dir, subset)
                    except FileNotFoundError:
                        continue
            else:
                # Process as image folder
                # 作为图片文件夹处理
                print(f"Processing image folder: {source_dir}")
                # Get all image folders
                # 获取所有图片文件夹
                image_folders = []
                for root, dirs, files in os.walk(source_dir):
                    if any(f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp')) for f in files):
                        image_folders.append(root)
                
                # Split folders into train/val/test
                # 将文件夹划分为训练/验证/测试集
                np.random.shuffle(image_folders)
                total = len(image_folders)
                train_size = int(total * self.split_ratio["train"])
                val_size = int(total * self.split_ratio["val"])
                
                splits = {
                    "train": image_folders[:train_size],
                    "val": image_folders[train_size:train_size+val_size],
                    "test": image_folders[train_size+val_size:]
                }
                
                # Process each split
                # 处理每个划分
                for split, folders in splits.items():
                    for folder in folders:
                        self.process_image_folder(folder, split)

    def validate_dataset(self):
        """
        Validate the preprocessed dataset
        验证预处理后的数据集
        """
        for split in ["train", "val", "test"]:
            anno_file = self.target_dir / split / "annotations" / "_annotations.coco.json"
            if not anno_file.exists():
                print(f"Warning: Annotation file not found for {split} set")
                continue
                
            with open(anno_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            # Check image files
            # 检查图片文件
            for img in data["images"]:
                img_file = self.target_dir / split / "images" / img["file_name"]
                if not img_file.exists():
                    print(f"Warning: Image file missing in {split} set: {img['file_name']}")
                    continue
                    
                # Verify image dimensions
                # 验证图片尺寸
                actual_img = cv2.imread(str(img_file))
                if actual_img.shape[:2] != (img["height"], img["width"]):
                    print(f"Warning: Image dimensions mismatch in {split} set: {img['file_name']}")
                    
            # Check annotations
            # 检查标注
            image_ids = {img["id"] for img in data["images"]}
            for ann in data["annotations"]:
                if ann["image_id"] not in image_ids:
                    print(f"Warning: Annotation refers to non-existent image in {split} set")
                    
            print(f"Validated {split} set:")
            print(f"  Images: {len(data['images'])}")
            print(f"  Annotations: {len(data['annotations'])}")
            print(f"  Categories: {len(data['categories'])}")

if __name__ == "__main__":
    # Example usage
    # 使用示例
    preprocessor = DatasetPreprocessor(
        target_dir="main_models_train/data/processed_dataset",
        img_size=(1280, 1280)
    )
    
    # Process mixed dataset
    # 处理混合数据集
    source_datasets = [
        "D:/train/S. Aureus Plates V3.v3i.coco-mmdetection",
        "D:/train/AGAR_demo"
    ]
    
    preprocessor.process_mixed_dataset(source_datasets)
    preprocessor.validate_dataset()
