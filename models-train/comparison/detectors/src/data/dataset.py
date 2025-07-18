"""
菌落检测数据集处理模块
基于MMDetection的CocoDataset扩展
"""

import os
import json
import numpy as np
from mmdet.datasets import CocoDataset
from mmdet.datasets.builder import DATASETS


@DATASETS.register_module()
class ColonyDataset(CocoDataset):
    """菌落检测数据集类"""
    
    CLASSES = ('colony', 'bacterial_colony', 'fungal_colony', 'yeast_colony',
               'mold_colony', 'actinomycetes_colony', 'mixed_colony')
    
    def __init__(self,
                 ann_file,
                 pipeline,
                 data_root=None,
                 img_prefix='',
                 seg_prefix=None,
                 proposal_file=None,
                 test_mode=False,
                 filter_empty_gt=True):
        super().__init__(
            ann_file=ann_file,
            pipeline=pipeline,
            data_root=data_root,
            img_prefix=img_prefix,
            seg_prefix=seg_prefix,
            proposal_file=proposal_file,
            test_mode=test_mode,
            filter_empty_gt=filter_empty_gt)
    
    def load_annotations(self, ann_file):
        """加载标注文件"""
        with open(ann_file, 'r') as f:
            data = json.load(f)
        
        # 验证类别信息
        if 'categories' in data:
            self.cat_ids = [cat['id'] for cat in data['categories']]
            self.cat2label = {cat_id: i for i, cat_id in enumerate(self.cat_ids)}
            self.label2cat = {i: cat_id for i, cat_id in enumerate(self.cat_ids)}
        
        return data
    
    def get_ann_info(self, idx):
        """获取标注信息"""
        img_id = self.data_infos[idx]['id']
        ann_ids = self.coco.get_ann_ids(img_ids=[img_id])
        ann_info = self.coco.load_anns(ann_ids)
        
        return self._parse_ann_info(self.data_infos[idx], ann_info)
    
    def _filter_imgs(self, min_size=32):
        """过滤太小的图像"""
        valid_inds = []
        for i, img_info in enumerate(self.data_infos):
            if min(img_info['width'], img_info['height']) >= min_size:
                valid_inds.append(i)
        return valid_inds
    
    def evaluate(self,
                 results,
                 metric='bbox',
                 logger=None,
                 jsonfile_prefix=None,
                 classwise=False,
                 proposal_nums=(100, 300, 1000),
                 iou_thrs=None,
                 metric_items=None):
        """评估模型性能"""
        if iou_thrs is None:
            iou_thrs = np.linspace(.5, 0.95, int(np.round((0.95 - .5) / .05)) + 1, endpoint=True)
        
        eval_results = super().evaluate(
            results=results,
            metric=metric,
            logger=logger,
            jsonfile_prefix=jsonfile_prefix,
            classwise=classwise,
            proposal_nums=proposal_nums,
            iou_thrs=iou_thrs,
            metric_items=metric_items)
        
        return eval_results


class ColonyDataProcessor:
    """菌落数据预处理类"""
    
    @staticmethod
    def check_dataset_structure(data_root):
        """检查数据集结构"""
        required_dirs = ['train', 'val', 'test', 'annotations']
        required_files = [
            'annotations/instances_train.json',
            'annotations/instances_val.json',
            'annotations/instances_test.json'
        ]
        
        missing = []
        for dir_name in required_dirs:
            if not os.path.exists(os.path.join(data_root, dir_name)):
                missing.append(dir_name)
        
        for file_path in required_files:
            if not os.path.exists(os.path.join(data_root, file_path)):
                missing.append(file_path)
        
        return missing
    
    @staticmethod
    def analyze_dataset(data_root):
        """分析数据集统计信息"""
        stats = {
            'train_images': 0,
            'val_images': 0,
            'test_images': 0,
            'total_colonies': 0,
            'categories': {}
        }
        
        splits = ['train', 'val', 'test']
        for split in splits:
            ann_file = os.path.join(data_root, f'annotations/instances_{split}.json')
            if os.path.exists(ann_file):
                with open(ann_file, 'r') as f:
                    data = json.load(f)
                
                stats[f'{split}_images'] = len(data['images'])
                
                # 统计标注信息
                if 'annotations' in data:
                    colonies = [ann for ann in data['annotations'] if ann.get('category_id', 1) == 1]
                    stats['total_colonies'] += len(colonies)
                
                # 统计类别
                if 'categories' in data:
                    for cat in data['categories']:
                        cat_name = cat['name']
                        if cat_name not in stats['categories']:
                            stats['categories'][cat_name] = 0
        
        return stats
    
    @staticmethod
    def create_sample_config():
        """创建示例配置"""
        return {
            'dataset_type': 'ColonyDataset',
            'data_root': '/merged_dataset/',
            'img_norm_cfg': {
                'mean': [123.675, 116.28, 103.53],
                'std': [58.395, 57.12, 57.375],
                'to_rgb': True
            },
            'train_pipeline': [
                {'type': 'LoadImageFromFile'},
                {'type': 'LoadAnnotations', 'with_bbox': True},
                {'type': 'Resize', 'img_scale': [(640, 640), (2048, 2048)], 'keep_ratio': True},
                {'type': 'RandomFlip', 'flip_ratio': 0.5},
                {'type': 'Normalize', 'mean': [123.675, 116.28, 103.53], 'std': [58.395, 57.12, 57.375], 'to_rgb': True},
                {'type': 'Pad', 'size_divisor': 32},
                {'type': 'DefaultFormatBundle'},
                {'type': 'Collect', 'keys': ['img', 'gt_bboxes', 'gt_labels']}
            ],
            'test_pipeline': [
                {'type': 'LoadImageFromFile'},
                {'type': 'MultiScaleFlipAug', 'img_scale': [(640, 640), (2048, 2048)], 'flip': False,
                 'transforms': [
                     {'type': 'Resize', 'keep_ratio': True},
                     {'type': 'RandomFlip'},
                     {'type': 'Normalize', 'mean': [123.675, 116.28, 103.53], 'std': [58.395, 57.12, 57.375], 'to_rgb': True},
                     {'type': 'Pad', 'size_divisor': 32},
                     {'type': 'ImageToTensor', 'keys': ['img']},
                     {'type': 'Collect', 'keys': ['img']}
                 ]}
            ]
        }


if __name__ == '__main__':
    # 测试数据集处理
    processor = ColonyDataProcessor()
    
    # 检查数据集结构
    data_root = '/merged_dataset/'
    missing = processor.check_dataset_structure(data_root)
    
    if missing:
        print(f"缺失的文件或目录: {missing}")
    else:
        print("数据集结构完整")
        
        # 分析数据集
        stats = processor.analyze_dataset(data_root)
        print("数据集统计信息:")
        for key, value in stats.items():
            print(f"  {key}: {value}")