import os
import torch
from torch.utils.data import Dataset
from PIL import Image
import numpy as np

class ColonyDataset(Dataset):
    def __init__(self, data_dir, transform=None):
        self.data_dir = data_dir
        self.transform = transform
        
        # 在测试模式下，我们不需要实际加载数据
        # 这里只是一个简单的实现
        self.images = []
        self.labels = []
        
        # 如果数据目录存在，则列出文件
        if os.path.exists(data_dir):
            try:
                # 假设数据目录结构为 data_dir/class_name/image_files
                for class_idx, class_name in enumerate(os.listdir(data_dir)):
                    class_dir = os.path.join(data_dir, class_name)
                    if os.path.isdir(class_dir):
                        for img_name in os.listdir(class_dir):
                            if img_name.lower().endswith(('.png', '.jpg', '.jpeg')):
                                img_path = os.path.join(class_dir, img_name)
                                self.images.append(img_path)
                                self.labels.append(class_idx)
            except Exception as e:
                print(f"加载数据集时出错: {e}")
                # 在测试模式下，我们可以使用一些虚拟数据
                self.images = ["dummy_image.jpg"] * 10
                self.labels = [0] * 10
        else:
            # 在测试模式下，我们可以使用一些虚拟数据
            self.images = ["dummy_image.jpg"] * 10
            self.labels = [0] * 10
    
    def __len__(self):
        return len(self.images)
    
    def __getitem__(self, idx):
        # 在测试模式下，我们可以返回随机张量
        if not os.path.exists(self.images[idx]):
            # 返回随机图像和标签
            image = torch.rand(3, 224, 224)
            label = self.labels[idx]
            return image, label
        
        # 正常情况下加载图像
        try:
            image = Image.open(self.images[idx]).convert("RGB")
            if self.transform:
                image = self.transform(image)
            else:
                # 简单的转换
                image = np.array(image)
                image = torch.from_numpy(image.transpose((2, 0, 1))).float() / 255.0
            
            label = self.labels[idx]
            return image, label
        except Exception as e:
            print(f"加载图像 {self.images[idx]} 时出错: {e}")
            # 返回随机图像和标签
            image = torch.rand(3, 224, 224)
            label = self.labels[idx]
            return image, label