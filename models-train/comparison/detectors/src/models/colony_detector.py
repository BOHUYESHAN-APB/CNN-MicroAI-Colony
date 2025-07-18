"""
DetectoRS 菌落检测模型定义
基于MMDetection的DetectoRS实现
"""

import torch
import torch.nn as nn
from mmdet.models import DetectoRS
from mmdet.models.builder import DETECTORS


@DETECTORS.register_module()
class DetectoRSColonyDetector(DetectoRS):
    """专为菌落检测优化的DetectoRS模型"""
    
    def __init__(self,
                 backbone,
                 neck=None,
                 rpn_head=None,
                 roi_head=None,
                 train_cfg=None,
                 test_cfg=None,
                 pretrained=None,
                 init_cfg=None):
        super().__init__(
            backbone=backbone,
            neck=neck,
            rpn_head=rpn_head,
            roi_head=roi_head,
            train_cfg=train_cfg,
            test_cfg=test_cfg,
            pretrained=pretrained,
            init_cfg=init_cfg)
        
        # 菌落检测特定配置
        self.num_classes = 85  # 包括背景类
        
    def forward_train(self,
                      img,
                      img_metas,
                      gt_bboxes,
                      gt_labels,
                      gt_bboxes_ignore=None,
                      gt_masks=None,
                      proposals=None,
                      **kwargs):
        """前向传播训练"""
        return super().forward_train(
            img=img,
            img_metas=img_metas,
            gt_bboxes=gt_bboxes,
            gt_labels=gt_labels,
            gt_bboxes_ignore=gt_bboxes_ignore,
            gt_masks=gt_masks,
            proposals=proposals,
            **kwargs)
    
    def simple_test(self, img, img_metas, proposals=None, rescale=False):
        """简单测试模式"""
        return super().simple_test(
            img=img,
            img_metas=img_metas,
            proposals=proposals,
            rescale=rescale)
    
    def aug_test(self, imgs, img_metas, rescale=False):
        """增强测试模式"""
        return super().aug_test(
            imgs=imgs,
            img_metas=img_metas,
            rescale=rescale)
    
    def extract_feat(self, img):
        """提取特征"""
        return super().extract_feat(img)


class DetectoRSColonyPredictor:
    """菌落检测预测器"""
    
    def __init__(self, checkpoint_path, config_path, device='cuda'):
        """初始化预测器"""
        self.device = torch.device(device if torch.cuda.is_available() else 'cpu')
        
        # 加载模型
        from mmcv import Config
        from mmdet.apis import init_detector
        
        self.model = init_detector(config_path, checkpoint_path, device=self.device)
        self.model.eval()
    
    def predict(self, img_path, score_thr=0.5):
        """预测单张图像"""
        from mmdet.apis import inference_detector
        
        result = inference_detector(self.model, img_path)
        
        # 过滤低置信度检测
        if isinstance(result, tuple):
            bbox_result, segm_result = result
        else:
            bbox_result, segm_result = result, None
        
        bboxes = np.vstack(bbox_result)
        labels = [
            np.full(bbox.shape[0], i, dtype=np.int32)
            for i, bbox in enumerate(bbox_result)
        ]
        labels = np.concatenate(labels)
        
        # 过滤
        scores = bboxes[:, -1]
        inds = scores > score_thr
        bboxes = bboxes[inds]
        labels = labels[inds]
        
        return {
            'bboxes': bboxes,
            'labels': labels,
            'scores': scores[inds]
        }
    
    def predict_batch(self, img_paths, score_thr=0.5):
        """批量预测"""
        results = []
        for img_path in img_paths:
            result = self.predict(img_path, score_thr)
            results.append(result)
        return results
    
    def get_model_info(self):
        """获取模型信息"""
        return {
            'model_type': 'DetectoRS',
            'backbone': 'ResNet50 + RFP + SAC',
            'num_classes': len(self.model.CLASSES),
            'device': str(self.device),
            'input_size': '640-2048 (multi-scale)'
        }


def create_model_config():
    """创建模型配置"""
    return {
        'type': 'DetectoRSColonyDetector',
        'backbone': {
            'type': 'DetectoRS_ResNet',
            'depth': 50,
            'num_stages': 4,
            'out_indices': (0, 1, 2, 3),
            'frozen_stages': 1,
            'norm_cfg': {'type': 'BN', 'requires_grad': True},
            'norm_eval': True,
            'style': 'pytorch',
            'conv_cfg': {'type': 'ConvAWS'},
            'sac': {'type': 'SAC', 'use_deform': True},
            'stage_with_sac': (False, True, True, True),
            'output_img': True,
            'init_cfg': {'type': 'Pretrained', 'checkpoint': 'torchvision://resnet50'}
        },
        'neck': {
            'type': 'RFP',
            'in_channels': [256, 512, 1024, 2048],
            'out_channels': 256,
            'num_outs': 5,
            'rfp_steps': 2,
            'aspp_out_channels': 64,
            'aspp_dilations': (1, 3, 6, 1),
            'rfp_backbone': {
                'type': 'DetectoRS_ResNet',
                'depth': 50,
                'num_stages': 4,
                'out_indices': (0, 1, 2, 3),
                'frozen_stages': 1,
                'norm_cfg': {'type': 'BN', 'requires_grad': True},
                'norm_eval': True,
                'style': 'pytorch',
                'conv_cfg': {'type': 'ConvAWS'},
                'sac': {'type': 'SAC', 'use_deform': True},
                'stage_with_sac': (False, True, True, True),
                'pretrained': 'torchvision://resnet50',
                'output_img': False
            }
        },
        'rpn_head': {
            'type': 'RPNHead',
            'in_channels': 256,
            'feat_channels': 256,
            'anchor_generator': {
                'type': 'AnchorGenerator',
                'scales': [8],
                'ratios': [0.5, 1.0, 2.0],
                'strides': [4, 8, 16, 32, 64]
            },
            'bbox_coder': {
                'type': 'DeltaXYWHBBoxCoder',
                'target_means': [0.0, 0.0, 0.0, 0.0],
                'target_stds': [1.0, 1.0, 1.0, 1.0]
            },
            'loss_cls': {
                'type': 'CrossEntropyLoss',
                'use_sigmoid': True,
                'loss_weight': 1.0
            },
            'loss_bbox': {
                'type': 'L1Loss',
                'loss_weight': 1.0
            }
        },
        'roi_head': {
            'type': 'CascadeRoIHead',
            'num_stages': 3,
            'stage_loss_weights': [1, 0.5, 0.25],
            'bbox_roi_extractor': {
                'type': 'SingleRoIExtractor',
                'roi_layer': {'type': 'RoIAlign', 'output_size': 7, 'sampling_ratio': 0},
                'out_channels': 256,
                'featmap_strides': [4, 8, 16, 32]
            },
            'bbox_head': [
                {
                    'type': 'Shared2FCBBoxHead',
                    'in_channels': 256,
                    'fc_out_channels': 1024,
                    'roi_feat_size': 7,
                    'num_classes': 85,
                    'bbox_coder': {
                        'type': 'DeltaXYWHBBoxCoder',
                        'target_means': [0.0, 0.0, 0.0, 0.0],
                        'target_stds': [0.1, 0.1, 0.2, 0.2]
                    },
                    'reg_class_agnostic': True,
                    'loss_cls': {
                        'type': 'CrossEntropyLoss',
                        'use_sigmoid': False,
                        'loss_weight': 1.0
                    },
                    'loss_bbox': {
                        'type': 'L1Loss',
                        'loss_weight': 1.0
                    }
                },
                {
                    'type': 'Shared2FCBBoxHead',
                    'in_channels': 256,
                    'fc_out_channels': 1024,
                    'roi_feat_size': 7,
                    'num_classes': 85,
                    'bbox_coder': {
                        'type': 'DeltaXYWHBBoxCoder',
                        'target_means': [0.0, 0.0, 0.0, 0.0],
                        'target_stds': [0.05, 0.05, 0.1, 0.1]
                    },
                    'reg_class_agnostic': True,
                    'loss_cls': {
                        'type': 'CrossEntropyLoss',
                        'use_sigmoid': False,
                        'loss_weight': 1.0
                    },
                    'loss_bbox': {
                        'type': 'L1Loss',
                        'loss_weight': 1.0
                    }
                },
                {
                    'type': 'Shared2FCBBoxHead',
                    'in_channels': 256,
                    'fc_out_channels': 1024,
                    'roi_feat_size': 7,
                    'num_classes': 85,
                    'bbox_coder': {
                        'type': 'DeltaXYWHBBoxCoder',
                        'target_means': [0.0, 0.0, 0.0, 0.0],
                        'target_stds': [0.033, 0.033, 0.067, 0.067]
                    },
                    'reg_class_agnostic': True,
                    'loss_cls': {
                        'type': 'CrossEntropyLoss',
                        'use_sigmoid': False,
                        'loss_weight': 1.0
                    },
                    'loss_bbox': {
                        'type': 'L1Loss',
                        'loss_weight': 1.0
                    }
                }
            ]
        }
    }


if __name__ == '__main__':
    import numpy as np
    
    # 测试模型配置
    config = create_model_config()
    print("DetectoRS模型配置创建成功")
    print(f"模型类型: {config['type']}")
    print(f"骨干网络: {config['backbone']['type']}")
    print(f"类别数: {config['roi_head']['bbox_head'][0]['num_classes']}")