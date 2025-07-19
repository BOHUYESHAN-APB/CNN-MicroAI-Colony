#!/usr/bin/env python3
"""
菌落检测数据集处理模块
"""

import os
import json
import numpy as np
from PIL import Image
import torch
from torch.utils.data import Dataset
import cv2

class ColonyDataset(Dataset):
    """菌落检测数据集类"""
    
    def __init__(self, data_root, split='train', transforms=None):
        """
        初始化数据集
        
        Args:
            data_root: 数据集根目录
            split: 数据集划分 ('train', 'val', 'test')
            transforms: 数据增强变换
        """
        self.data_root = data_root
        self.split = split
        self.transforms = transforms
        
        # 设置路径
        self.img_dir = os.path.join(data_root, split)
        self.ann_file = os.path.join(data_root, 'annotations', f'instances_{split}.json')
        
        # 加载标注
        with open(self.ann_file, 'r') as f:
            self.coco_data = json.load(f)
        
        # 创建图像id到文件名的映射
        self.img_map = {img['id']: img['file_name'] for img in self.coco_data['images']}
        
        # 创建图像id到标注的映射
        self.ann_map = {}
        for ann in self.coco_data['annotations']:
            img_id = ann['image_id']
            if img_id not in self.ann_map:
                self.ann_map[img_id] = []
            self.ann_map[img_id].append(ann)
        
        # 获取有效图像id列表
        self.img_ids = list(self.ann_map.keys())
        
        # 类别映射
        self.class_names = ['colony']
        self.class_to_idx = {name: idx + 1 for idx, name in enumerate(self.class_names)}
        
    def __len__(self):
        return len(self.img_ids)
    
    def __getitem__(self, idx):
        """获取单个样本"""
        img_id = self.img_ids[idx]
        
        # 加载图像
        img_path = os.path.join(self.img_dir, self.img_map[img_id])
        image = Image.open(img_path).convert('RGB')
        image = np.array(image)
        
        # 获取标注
        annotations = self.ann_map[img_id]
        
        # 提取边界框和标签
        boxes = []
        labels = []
        
        for ann in annotations:
            # COCO格式: [x, y, width, height]
            x, y, w, h = ann['bbox']
            boxes.append([x, y, x + w, y + h])
            labels.append(1)  # 菌落类别为1
        
        # 转换为numpy数组
        boxes = np.array(boxes, dtype=np.float32)
        labels = np.array(labels, dtype=np.int64)
        
        # 创建目标字典
        target = {
            'boxes': torch.as_tensor(boxes, dtype=torch.float32),
            'labels': torch.as_tensor(labels, dtype=torch.int64),
            'image_id': torch.tensor([img_id])
        }
        
        # 应用变换
        if self.transforms:
            image = self.transforms(image)
        
        return image, target
    
    def get_image_info(self, idx):
        """获取图像信息"""
        img_id = self.img_ids[idx]
        img_info = next(img for img in self.coco_data['images'] if img['id'] == img_id)
        return img_info
    
    def visualize_sample(self, idx, save_path=None):
        """可视化样本"""
        image, target = self[idx]
        
        # 如果是tensor，转换为numpy
        if isinstance(image, torch.Tensor):
            image = image.permute(1, 2, 0).numpy()
            image = (image * 255).astype(np.uint8)
        
        # 绘制边界框
        img_vis = image.copy()
        boxes = target['boxes'].numpy()
        
        for box in boxes:
            x1, y1, x2, y2 = box.astype(int)
            cv2.rectangle(img_vis, (x1, y1), (x2, y2), (0, 255, 0), 2)
        
        if save_path:
            cv2.imwrite(save_path, cv2.cvtColor(img_vis, cv2.COLOR_RGB2BGR))
        
        return img_vis

class ColonyDataModule:
    """菌落检测数据模块"""
    
    def __init__(self, data_root, batch_size=2, num_workers=4):
        self.data_root = data_root
        self.batch_size = batch_size
        self.num_workers = num_workers
        
    def train_dataloader(self):
        """训练数据加载器"""
        dataset = ColonyDataset(
            self.data_root, 
            split='train',
            transforms=self.get_train_transforms()
        )
        return torch.utils.data.DataLoader(
            dataset,
            batch_size=self.batch_size,
            shuffle=True,
            num_workers=self.num_workers,
            collate_fn=self.collate_fn
        )
    
    def val_dataloader(self):
        """验证数据加载器"""
        dataset = ColonyDataset(
            self.data_root,
            split='val',
            transforms=self.get_val_transforms()
        )
        return torch.utils.data.DataLoader(
            dataset,
            batch_size=self.batch_size,
            shuffle=False,
            num_workers=self.num_workers,
            collate_fn=self.collate_fn
        )
    
    def test_dataloader(self):
        """测试数据加载器"""
        dataset = ColonyDataset(
            self.data_root,
            split='test',
            transforms=self.get_val_transforms()
        )
        return torch.utils.data.DataLoader(
            dataset,
            batch_size=self.batch_size,
            shuffle=False,
            num_workers=self.num_workers,
            collate_fn=self.collate_fn
        )
    
    def get_train_transforms(self):
        """训练数据增强"""
        import torchvision.transforms as T
        
        return T.Compose([
            T.ToPILImage(),
            T.Resize((640, 640)),
            T.RandomHorizontalFlip(0.5),
            T.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2, hue=0.1),
            T.ToTensor(),
            T.Normalize(mean=[0.485, 0.456, 0.406], 
                       std=[0.229, 0.224, 0.225])
        ])
    
    def get_val_transforms(self):
        """验证数据变换"""
        import torchvision.transforms as T
        
        return T.Compose([
            T.ToPILImage(),
            T.Resize((640, 640)),
            T.ToTensor(),
            T.Normalize(mean=[0.485, 0.456, 0.406], 
                       std=[0.229, 0.224, 0.225])
        ])
    
    @staticmethod
    def collate_fn(batch):
        """自定义批处理函数"""
        images, targets = zip(*batch)
        return list(images), list(targets)

def create_sample_data(data_root, num_samples=100):
    """创建示例数据集"""
    """创建示例数据集"""
    os.makedirs(os.path.join(data_root, 'train'), exist_ok=True)
    os.makedirs(os.path.join(data_root, 'val'), exist_ok=True)
    os.makedirs(os.path.join(data_root, 'test'), exist_ok=True)
    os.makedirs(os.path.join(data_root, 'annotations'), exist_ok=True)
    
    # 为每个分割创建示例数据
    for split in ['train', 'val', 'test']:
        images = []
        annotations = []
        img_id = 0
        ann_id = 0
        
        for i in range(num_samples // 3):
            # 创建示例图像
            img_name = f'{split}_{i:06d}.jpg'
            img_path = os.path.join(data_root, split, img_name)
            
            # 生成随机图像
            img = np.random.randint(0, 255, (512, 512, 3), dtype=np.uint8)
            Image.fromarray(img).save(img_path)
            
            # 添加图像信息
            images.append({
                'id': img_id,
                'file_name': img_name,
                'width': 512,
                'height': 512
            })
            
            # 添加标注
            num_colonies = np.random.randint(1, 10)
            for _ in range(num_colonies):
                x = np.random.randint(0, 400)
                y = np.random.randint(0, 400)
                w = np.random.randint(20, 100)
                h = np.random.randint(20, 100)
                
                annotations.append({
                    'id': ann_id,
                    'image_id': img_id,
                    'category_id': 1,
                    'bbox': [x, y, w, h],
                    'area': w * h,
                    'iscrowd': 0
                })
                ann_id += 1
            
            img_id += 1
        
        # 保存标注文件
        coco_format = {
            'images': images,
            'annotations': annotations,
            'categories': [{'id': 1, 'name': 'colony', 'supercategory': 'none'}]
        }
        
        with open(os.path.join(data_root, 'annotations', f'instances_{split}.json'), 'w') as f:
            json.dump(coco_format, f, indent=2)

if __name__ == '__main__':
    # 测试数据集
    data_root = '/merged_dataset'
    dataset = ColonyDataset(data_root, split='train')
    print(f"数据集大小: {len(dataset)}")
    
    # 可视化样本
    sample = dataset.visualize_sample(0, 'sample.jpg')
    print("样本已保存为 sample.jpg")