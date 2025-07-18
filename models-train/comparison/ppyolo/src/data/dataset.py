import os
import json
import paddle
import numpy as np
from PIL import Image
from paddle.vision.transforms import functional as F

class ColonyDataset(paddle.io.Dataset):
    def __init__(self, data_dir, img_size, is_train=True):
        self.data_dir = data_dir
        self.img_size = img_size
        self.is_train = is_train
        
        # 加载COCO格式标注
        ann_file = os.path.join(data_dir, 'annotations/instances.json')
        with open(ann_file) as f:
            self.coco_data = json.load(f)
            
        # 建立图像索引
        self.image_ids = [img['id'] for img in self.coco_data['images']]
        
    def __getitem__(self, idx):
        img_info = self.coco_data['images'][idx]
        img_path = os.path.join(self.data_dir, 'images', img_info['file_name'])
        
        # 加载图像
        img = Image.open(img_path).convert('RGB')
        img = F.to_tensor(img)
        
        # 多尺度调整
        if isinstance(self.img_size, list):
            target_size = np.random.randint(self.img_size[0], self.img_size[1])
            img = F.resize(img, (target_size, target_size))
        
        # 获取标注
        ann_ids = [ann['id'] for ann in self.coco_data['annotations'] 
                  if ann['image_id'] == img_info['id']]
        annotations = [ann for ann in self.coco_data['annotations'] 
                      if ann['id'] in ann_ids]
        
        # 转换为Paddle格式
        boxes = []
        labels = []
        for ann in annotations:
            boxes.append(ann['bbox'])
            labels.append(ann['category_id'])
            
        target = {
            'boxes': paddle.to_tensor(boxes, dtype='float32'),
            'labels': paddle.to_tensor(labels, dtype='int64')
        }
        
        return img, target
    
    def __len__(self):
        return len(self.image_ids)