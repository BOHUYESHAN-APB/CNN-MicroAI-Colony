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
        self.target_dir = Path(target_dir)
        self.img_size = img_size
        self.split_ratio = split_ratio
        self.annotation_id = 0
        
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
            
            # Resize image
            img = cv2.resize(img, self.img_size)
            
            # Save processed image
            out_img_file = self.target_dir / split / "images" / img_path.name
            cv2.imwrite(str(out_img_file), img)
            
            # Process annotations
            image_id += 1
            images.append({
                "id": image_id,
                "file_name": img_path.name,
                "width": self.img_size[0],
                "height": self.img_size[1]
            })
            
            # Scale factors for bbox coordinates
            scale_x = self.img_size[0] / w
            scale_y = self.img_size[1] / h
            
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

    def process_coco_dataset(self, source_dir: str, subset: str = "train"):
        """Process COCO format dataset"""
        source_dir = Path(source_dir)
        possible_paths = [
            source_dir / subset / "_annotations.coco.json",
            source_dir / "_annotations.coco.json",
            source_dir / f"{subset}_annotations.coco.json"
        ]
        
        anno_file = None
        for path in possible_paths:
            if path.exists():
                anno_file = path
                print(f"Found annotation file: {path}")
                break
                
        if anno_file is None:
            raise FileNotFoundError(f"No annotation file found in {source_dir}")
            
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
            
        # Process each image
        for img_info in coco_data["images"]:
            img_id = img_info["id"]
            img_file = source_dir / img_info["file_name"]
            
            if not img_file.exists():
                # Try finding the image in the subset directory
                img_file = source_dir / subset / img_info["file_name"]
                if not img_file.exists():
                    print(f"Warning: Image file not found: {img_info['file_name']}")
                    continue
                
            img = cv2.imread(str(img_file))
            if img is None:
                print(f"Warning: Failed to read image: {img_file}")
                continue
                
            img = cv2.resize(img, self.img_size)
            
            # Scale annotations
            scale_x = self.img_size[0] / img_info["width"]
            scale_y = self.img_size[1] / img_info["height"]
            
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
            cv2.imwrite(str(out_img_file), img)
            
            images[img_id] = {
                **img_info,
                "width": self.img_size[0],
                "height": self.img_size[1]
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

    def process_mixed_dataset(self, source_dirs: List[str]):
        """Process mixed datasets"""
        for source_dir in source_dirs:
            source_path = Path(source_dir)
            
            if "AGAR_demo" in str(source_path):
                print(f"Processing AGAR dataset: {source_dir}")
                # Split AGAR dataset
                all_images = list(source_path.rglob("*.jpg"))
                np.random.shuffle(all_images)
                
                total = len(all_images)
                train_size = int(total * self.split_ratio["train"])
                val_size = int(total * self.split_ratio["val"])
                
                train_imgs = all_images[:train_size]
                val_imgs = all_images[train_size:train_size+val_size]
                test_imgs = all_images[train_size+val_size:]
                
                for split, imgs in [("train", train_imgs), ("val", val_imgs), ("test", test_imgs)]:
                    for img_path in imgs:
                        self.process_agar_dataset(img_path.parent, split)
                        
            else:
                print(f"Processing COCO dataset: {source_dir}")
                for subset in ["train", "valid", "test"]:
                    try:
                        self.process_coco_dataset(source_dir, subset)
                    except FileNotFoundError:
                        continue

    def validate_dataset(self):
        """Validate the preprocessed dataset"""
        for split in ["train", "val", "test"]:
            anno_file = self.target_dir / split / "annotations" / "_annotations.coco.json"
            if not anno_file.exists():
                print(f"Warning: Annotation file not found for {split} set")
                continue
                
            with open(anno_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            for img in data["images"]:
                img_file = self.target_dir / split / "images" / img["file_name"]
                if not img_file.exists():
                    print(f"Warning: Image file missing in {split} set: {img['file_name']}")
                    continue
                    
                actual_img = cv2.imread(str(img_file))
                if actual_img.shape[:2] != (img["height"], img["width"]):
                    print(f"Warning: Image dimensions mismatch in {split} set: {img['file_name']}")
                    
            image_ids = {img["id"] for img in data["images"]}
            for ann in data["annotations"]:
                if ann["image_id"] not in image_ids:
                    print(f"Warning: Annotation refers to non-existent image in {split} set")
                    
            print(f"Validated {split} set:")
            print(f"  Images: {len(data['images'])}")
            print(f"  Annotations: {len(data['annotations'])}")
            print(f"  Categories: {len(data['categories'])}")

if __name__ == "__main__":
    preprocessor = DatasetPreprocessor(
        target_dir="main_models_train/data/processed_dataset",
        img_size=(1280, 1280)
    )
    
    source_datasets = [
        "D:/train/S. Aureus Plates V3.v3i.coco-mmdetection",
        "D:/train/AGAR_demo"
    ]
    
    preprocessor.process_mixed_dataset(source_datasets)
    preprocessor.validate_dataset()
