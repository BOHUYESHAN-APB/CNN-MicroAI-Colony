import os
import json
import cv2
import numpy as np
import torch
from torch.utils.data import Dataset
import albumentations as A
from albumentations.pytorch import ToTensorV2

class ColonyDataset(Dataset):
    def __init__(self, img_dir, transform=None, split='train'):
        """
        Args:
            img_dir (str): Directory with all the images and json files
            transform (callable, optional): Optional transform to be applied on images
            split (str): 'train' or 'val' or 'test'
        """
        self.img_dir = img_dir
        self.transform = transform if transform else self._get_default_transforms(split)
        self.split = split
        
        # Get all image files and their corresponding json files
        self.img_files = []
        self.json_files = []
        for dirpath, _, filenames in os.walk(img_dir):
            for f in filenames:
                if f.endswith('.jpg'):
                    img_path = os.path.join(dirpath, f)
                    json_path = os.path.join(dirpath, f.replace('.jpg', '.json'))
                    if os.path.exists(json_path):
                        self.img_files.append(img_path)
                        self.json_files.append(json_path)

    def __len__(self):
        return len(self.img_files)

    def _get_default_transforms(self, split):
        if split == 'train':
            return A.Compose([
                A.Resize(height=512, width=512),
                A.RandomCrop(height=480, width=480),
                A.HorizontalFlip(p=0.5),
                A.VerticalFlip(p=0.5),
                A.RandomBrightnessContrast(p=0.2),
                A.Normalize(
                    mean=[0.485, 0.456, 0.406],
                    std=[0.229, 0.224, 0.225]
                ),
                ToTensorV2()
            ], bbox_params=A.BboxParams(format='pascal_voc', label_fields=['class_labels']))
        else:
            return A.Compose([
                A.Resize(height=512, width=512),
                A.Normalize(
                    mean=[0.485, 0.456, 0.406],
                    std=[0.229, 0.224, 0.225]
                ),
                ToTensorV2()
            ], bbox_params=A.BboxParams(format='pascal_voc', label_fields=['class_labels']))

    def _load_json(self, json_path):
        with open(json_path, 'r') as f:
            data = json.load(f)
        return data
    
    def _convert_to_pascal_voc(self, boxes, image_shape):
        """Convert from [x, y, w, h] to [x1, y1, x2, y2] format"""
        if len(boxes) == 0:
            return boxes
        
        boxes = np.array(boxes)
        converted_boxes = np.zeros_like(boxes)
        
        # Convert from [x, y, w, h] to [x1, y1, x2, y2]
        converted_boxes[:, 0] = boxes[:, 0]  # x1
        converted_boxes[:, 1] = boxes[:, 1]  # y1
        converted_boxes[:, 2] = boxes[:, 0] + boxes[:, 2]  # x2 = x1 + w
        converted_boxes[:, 3] = boxes[:, 1] + boxes[:, 3]  # y2 = y1 + h
        
        # Clip to image boundaries
        converted_boxes[:, [0, 2]] = np.clip(converted_boxes[:, [0, 2]], 0, image_shape[1])
        converted_boxes[:, [1, 3]] = np.clip(converted_boxes[:, [1, 3]], 0, image_shape[0])
        
        return converted_boxes

    def __getitem__(self, idx):
        # Load image
        img_path = self.img_files[idx]
        image = cv2.imread(img_path)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Get image shape for box conversion
        height, width = image.shape[:2]

        # Load annotations
        json_data = self._load_json(self.json_files[idx])
        
        # Extract bounding boxes and labels
        boxes = []
        class_labels = []
        
        for label in json_data['labels']:
            x, y = label['x'], label['y']
            w, h = label['width'], label['height']
            boxes.append([x, y, w, h])
            class_labels.append(1)  # Binary classification (colony vs background)
        
        # Convert boxes to Pascal VOC format
        boxes = self._convert_to_pascal_voc(boxes, (height, width))
        class_labels = np.array(class_labels)

        # Apply transformations
        if self.transform:
            transformed = self.transform(
                image=image,
                bboxes=boxes,
                class_labels=class_labels
            )
            image = transformed['image']  # Already a tensor from ToTensorV2
            boxes = transformed['bboxes']
            class_labels = transformed['class_labels']

        # Remove any boxes that became invalid after transformation
        valid_boxes = []
        valid_labels = []
        for box, label in zip(boxes, class_labels):
            # Check if box coordinates are valid
            if box[2] > box[0] and box[3] > box[1]:  # x2 > x1 and y2 > y1
                valid_boxes.append(box)
                valid_labels.append(label)

        if len(valid_boxes) == 0:
            # If no valid boxes, create a dummy box to prevent errors
            valid_boxes = [[0, 0, 1, 1]]
            valid_labels = [0]  # Background class

        # Convert boxes and labels to tensors
        boxes = torch.as_tensor(np.array(valid_boxes), dtype=torch.float32)
        class_labels = torch.as_tensor(valid_labels, dtype=torch.int64)

        return {
            'image': image,
            'boxes': boxes,
            'labels': class_labels,
            'img_path': img_path,
            'total_count': json_data['colonies_number']
        }
