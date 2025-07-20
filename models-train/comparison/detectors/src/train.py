#!/usr/bin/env python3
"""
DetectoRS 菌落检测训练脚本
基于MMDetection框架实现
"""

import os
import sys
import argparse
import torch
from mmcv import Config
from mmdet.apis import train_detector
from mmdet.datasets import build_dataset
from mmdet.models import build_detector
from mmdet.utils import get_device

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.data.dataset import ColonyDataset
from src.models.colony_detector import DetectoRSColonyDetector


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='Train DetectoRS for colony detection')
    parser.add_argument('--config', default='configs/detectors_coco.py',
                        help='训练配置文件路径')
    parser.add_argument('--work-dir', default='./work_dirs',
                        help='工作目录，用于保存日志和模型')
    parser.add_argument('--resume-from', help='从指定checkpoint恢复训练')
    parser.add_argument('--no-validate', action='store_true',
                        help='训练时不验证')
    parser.add_argument('--gpus', type=int, default=1,
                        help='使用的GPU数量')
    parser.add_argument('--seed', type=int, default=42,
                        help='随机种子')
    parser.add_argument('--deterministic', action='store_true',
                        help='确定性训练')
    parser.add_argument('--local_rank', type=int, default=0)
    
    return parser.parse_args()


def setup_environment():
    """设置训练环境"""
    # 设置CUDA环境
    if torch.cuda.is_available():
        torch.backends.cudnn.benchmark = True
        print(f"使用GPU: {torch.cuda.get_device_name(0)}")
    else:
        print("警告: 未检测到GPU，将使用CPU训练")
    
    # 创建工作目录
    os.makedirs('work_dirs', exist_ok=True)
    os.makedirs('checkpoints', exist_ok=True)


def create_config(args):
    """创建训练配置"""
    cfg = Config.fromfile(args.config)
    
    # 设置工作目录
    cfg.work_dir = args.work_dir
    
    # 设置GPU数量
    cfg.gpu_ids = list(range(args.gpus))
    
    # 设置随机种子
    cfg.seed = args.seed
    
    # 设置确定性训练
    if args.deterministic:
        cfg.deterministic = True
    
    # 设置恢复训练
    if args.resume_from:
        cfg.resume_from = args.resume_from
    
    # 设置数据集路径
    cfg.data_root = '/merged_dataset/'
    cfg.data.train.ann_file = cfg.data_root + 'annotations/instances_train.json'
    cfg.data.train.img_prefix = cfg.data_root + 'train/'
    cfg.data.val.ann_file = cfg.data_root + 'annotations/instances_val.json'
    cfg.data.val.img_prefix = cfg.data_root + 'val/'
    cfg.data.test.ann_file = cfg.data_root + 'annotations/instances_test.json'
    cfg.data.test.img_prefix = cfg.data_root + 'test/'
    
    # 设置类别数
    cfg.model.roi_head.bbox_head[0].num_classes = 85
    cfg.model.roi_head.bbox_head[1].num_classes = 85
    cfg.model.roi_head.bbox_head[2].num_classes = 85
    
    # 设置训练参数
    cfg.total_epochs = 12  # 修改为统一的训练轮数
    cfg.checkpoint_config.interval = 1
    cfg.log_config.interval = 50
    
    return cfg


def main():
    """主训练函数"""
    args = parse_args()
    
    # 设置环境
    setup_environment()
    
    # 创建配置
    cfg = create_config(args)
    
    print("=" * 60)
    print("DetectoRS 菌落检测训练")
    print("=" * 60)
    print(f"配置文件: {args.config}")
    print(f"工作目录: {cfg.work_dir}")
    print(f"GPU数量: {args.gpus}")
    print(f"训练周期: {cfg.total_epochs}")
    print("=" * 60)
    
    # 构建数据集
    datasets = [build_dataset(cfg.data.train)]
    
    # 构建模型
    model = build_detector(
        cfg.model,
        train_cfg=cfg.get('train_cfg'),
        test_cfg=cfg.get('test_cfg'))
    
    # 添加类别信息
    model.CLASSES = datasets[0].CLASSES
    
    # 开始训练
    train_detector(
        model,
        datasets,
        cfg,
        distributed=False,
        validate=not args.no_validate,
        timestamp=None,
        meta=dict())
    
    print("训练完成！")


if __name__ == '__main__':
    main()