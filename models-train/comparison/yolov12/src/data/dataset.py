import os
import yaml
from pathlib import Path

class ColonyDataset:
    """
    用于处理菌落数据集的类
    """
    def __init__(self, data_dir=None, img_size=640, batch_size=16, test_mode=False):
        self.test_mode = test_mode
        
        if test_mode:
            # 测试模式下使用虚拟数据
            self.data_dir = "./test_data"
            print(f"测试模式: 使用虚拟数据目录 {self.data_dir}")
            # 创建测试数据目录
            os.makedirs(self.data_dir, exist_ok=True)
        else:
            self.data_dir = data_dir
            # 确保数据目录存在
            if not os.path.exists(data_dir):
                print(f"警告: 数据目录 {data_dir} 不存在")
        
        self.img_size = img_size
        self.batch_size = batch_size
    
    def get_config(self):
        """
        返回YOLO格式的数据集配置
        """
        # 创建临时YAML配置
        config = {
            'path': self.data_dir,
            'train': 'train/images',
            'val': 'val/images',
            'test': 'test/images',
            'nc': 80,  # COCO数据集类别数
            'names': self._get_class_names()
        }
        
        # 确保数据目录存在
        os.makedirs(self.data_dir, exist_ok=True)
        
        # 如果是测试模式，创建必要的子目录
        if self.test_mode:
            for subdir in ['train/images', 'val/images', 'test/images',
                          'train/labels', 'val/labels', 'test/labels']:
                os.makedirs(os.path.join(self.data_dir, subdir), exist_ok=True)
        
        # 保存临时配置文件
        config_path = Path(self.data_dir) / 'dataset.yaml'
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f)
        
        print(f"已创建数据集配置文件: {config_path}")
        return str(config_path)
    
    def _get_class_names(self):
        """
        获取类别名称
        """
        # 这里简化处理，实际应从数据集中读取
        # 返回COCO数据集的类别名称
        return ['person', 'bicycle', 'car', '...']  # 简化示例

    def __len__(self):
        """
        返回数据集大小
        """
        # 实际应计算训练集图像数量
        return 1000  # 示例值