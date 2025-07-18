import os
import json
import numpy as np
from PIL import Image
import torch
from torch.utils.data import Dataset
import torchvision.transforms as transforms

class ColonyDataset(Dataset):
    def __init__(self, data_dir, split='train', img_size=[640, 2048]):
        self.data_dir = data_dir
        self.split = split
        self.img_size = img_size
        
        # 加载COCO格式标注
        ann_file = os.path.join(data_dir, f'annotations/instances_{split}.json')
        with open(ann_file) as f:
            self.coco_data = json.load(f)
            
        # 建立图像索引
        self.image_ids = [img['id'] for img in self.coco_data['images']]
        
        # 数据增强
        if split == 'train':
            self.transform = transforms.Compose([
                transforms.Resize((img_size[0], img_size[0])),
                transforms.RandomHorizontalFlip(0.5),
                transforms.RandomRotation(10),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
            ])
        else:
            self.transform = transforms.Compose([
                transforms.Resize((img_size[0], img_size[0])),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
            ])
    
    def __getitem__(self, idx):
        img_info = self.coco_data['images'][idx]
        img_path = os.path.join(self.data_dir, 'images', img_info['file_name'])
        
        # 加载图像
        image = Image.open(img_path).convert('RGB')
        image = self.transform(image)
        
        # 创建分割掩码
        mask = np.zeros((image.shape[1], image.shape[2]), dtype=np.float32)
        
        # 获取该图像的所有标注
        annotations = [ann for ann in self.coco_data['annotations'] 
                      if ann['image_id'] == img_info['id']]
        
        # 生成掩码
        for ann in annotations:
            # 这里简化处理，实际应用中需要更复杂的掩码生成
            bbox = ann['bbox']
            x, y, w, h = [int(v) for v in bbox]
            mask[y:y+h, x:x+w] = 1.0
        
        mask = torch.from_numpy(mask).unsqueeze(0)
        
        return image, mask
    
    def __len__(self):
        return len(self.image_ids)