#!/usr/bin/env python3
"""
Faster R-CNN ResNet101 训练脚本
用于菌落检测任务
"""

import os
import sys
import argparse
import logging
from pathlib import Path

import torch
from mmcv import Config
from mmdet.apis import train_detector
from mmdet.models import build_detector
from mmdet.datasets import build_dataset

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.data.dataset import ColonyDataset
from src.models.colony_detector import ColonyFasterRCNN

def setup_logging(log_dir):
    """设置日志配置"""
    os.makedirs(log_dir, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(os.path.join(log_dir, 'train.log')),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='Train Faster R-CNN ResNet101 for colony detection')
    parser.add_argument('--config', default='configs/faster_rcnn_resnet101_coco.py',
                        help='训练配置文件路径')
    parser.add_argument('--work-dir', default='./checkpoints',
                        help='工作目录，用于保存日志和模型')
    parser.add_argument('--resume-from', help='从检查点恢复训练')
    parser.add_argument('--no-validate', action='store_true',
                        help='训练期间不验证')
    parser.add_argument('--gpus', type=int, default=1, help='使用的GPU数量')
    parser.add_argument('--seed', type=int, default=42, help='随机种子')
    parser.add_argument('--deterministic', action='store_true',
                        help='是否使用确定性训练')
    parser.add_argument('--local_rank', type=int, default=0)
    
    return parser.parse_args()

def main():
    """主训练函数"""
    args = parse_args()
    
    # 设置工作目录
    work_dir = args.work_dir
    os.makedirs(work_dir, exist_ok=True)
    
    # 设置日志
    logger = setup_logging(work_dir)
    logger.info("开始 Faster R-CNN ResNet101 训练")
    logger.info(f"工作目录: {work_dir}")
    logger.info(f"配置文件: {args.config}")
    
    # 加载配置
    cfg = Config.fromfile(args.config)
    
    # 更新配置
    cfg.work_dir = work_dir
    if args.resume_from:
        cfg.resume_from = args.resume_from
    
    # 设置GPU
    if args.gpus is not None:
        cfg.gpu_ids = range(args.gpus)
    
    # 创建模型
    logger.info("创建 Faster R-CNN ResNet101 模型...")
    model = build_detector(cfg.model)
    model.init_weights()
    
    # 创建数据集
    logger.info("创建数据集...")
    datasets = [build_dataset(cfg.data.train)]
    
    # 如果是恢复训练，验证数据集
    if len(cfg.workflow) == 2:
        val_dataset = copy.deepcopy(cfg.data.val)
        val_dataset.pipeline = cfg.data.train.pipeline
        datasets.append(build_dataset(val_dataset))
    
    # 设置随机种子
    if args.seed is not None:
        import numpy as np
        import random
        random.seed(args.seed)
        np.random.seed(args.seed)
        torch.manual_seed(args.seed)
        torch.cuda.manual_seed_all(args.seed)
        if args.deterministic:
            torch.backends.cudnn.deterministic = True
            torch.backends.cudnn.benchmark = False
    
    # 开始训练
    logger.info("开始训练...")
    try:
        train_detector(
            model,
            datasets,
            cfg,
            distributed=False,
            validate=(not args.no_validate),
            timestamp=None,
            meta=dict()
        )
        logger.info("训练完成！")
    except Exception as e:
        logger.error(f"训练过程中出现错误: {str(e)}")
        raise

if __name__ == '__main__':
    main()
# 添加记录详细训练参数的功能
# 添加实时显示训练参数的功能