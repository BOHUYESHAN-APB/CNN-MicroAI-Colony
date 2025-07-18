import argparse
import os
import json
import logging
from datetime import datetime
import torch
from mmcv import Config
from mmdet.apis import train_detector
from mmdet.models import build_detector
from mmdet.datasets import build_dataset
from mmdet.utils import collect_env

def setup_logging(save_dir):
    """配置日志记录"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(os.path.join(save_dir, 'training.log')),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description='Train HTC for colony detection')
    parser.add_argument('config', help='train config file path')
    parser.add_argument('--work-dir', help='the dir to save logs and models')
    parser.add_argument('--resume-from', help='the checkpoint file to resume from')
    parser.add_argument('--epochs', type=int, default=50)
    parser.add_argument('--gpu-ids', type=int, nargs='+', default=[0])
    
    args = parser.parse_args()
    
    # 加载配置
    cfg = Config.fromfile(args.config)
    
    # 工作目录设置
    if args.work_dir is not None:
        cfg.work_dir = args.work_dir
    elif cfg.get('work_dir', None) is None:
        cfg.work_dir = os.path.join('./work_dirs', 
                                  os.path.splitext(os.path.basename(args.config))[0])
    os.makedirs(cfg.work_dir, exist_ok=True)
    
    # 初始化日志
    logger = setup_logging(cfg.work_dir)
    logger.info('Starting HTC training...')
    
    # 记录环境信息
    env_info_dict = collect_env()
    env_info = '\n'.join([f'{k}: {v}' for k, v in env_info_dict.items()])
    logger.info('Environment info:\n' + env_info)
    
    # 构建数据集
    datasets = [build_dataset(cfg.data.train)]
    
    # 构建模型
    model = build_detector(cfg.model)
    model.init_weights()
    
    # 训练
    train_detector(
        model,
        datasets,
        cfg,
        distributed=False,
        validate=True,
        timestamp=datetime.now().strftime('%Y%m%d_%H%M%S'),
        meta=dict(
            mmdet_version='2.x',
            config=cfg.pretty_text
        )
    )

if __name__ == '__main__':
    main()