"""
Combined training script for colony detection models with interrupt/resume support
支持中断/恢复训练的菌落检测模型训练脚本
"""

import os
import sys
import argparse
import logging
import json
from datetime import datetime
import torch
from torch.utils.data import DataLoader
from mmcv import Config
from mmdet.apis import train_detector
from mmdet.models import build_detector
from mmdet.datasets import build_dataset
from mmdet.utils import collect_env, get_root_logger

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

def save_checkpoint(model, optimizer, epoch, save_dir, metrics=None):
    """保存检查点"""
    checkpoint = {
        'epoch': epoch,
        'model_state_dict': model.state_dict(),
        'optimizer_state_dict': optimizer.state_dict(),
        'metrics': metrics or {}
    }
    path = os.path.join(save_dir, f'checkpoint_epoch_{epoch}.pth')
    torch.save(checkpoint, path)
    return path

def load_checkpoint(model, optimizer, checkpoint_path, device):
    """加载检查点"""
    checkpoint = torch.load(checkpoint_path, map_location=device)
    model.load_state_dict(checkpoint['model_state_dict'])
    optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
    return checkpoint['epoch'], checkpoint.get('metrics', None)

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='Train combined colony detector')
    parser.add_argument('config', help='train config file path')
    parser.add_argument('--work-dir', help='the dir to save logs and models')
    parser.add_argument('--resume-from', help='the checkpoint file to resume from')
    parser.add_argument('--epochs', type=int, default=50, help='total training epochs')
    parser.add_argument('--save-interval', type=int, default=1, help='save checkpoint every N epochs')
    parser.add_argument('--seed', type=int, default=None, help='random seed')
    parser.add_argument('--gpu-ids', type=int, nargs='+', help='ids of gpus to use')
    return parser.parse_args()

def main():
    args = parse_args()
    
    # 设备配置
    device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
    
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
    logger.info(f'Training on device: {device}')
    
    # 记录环境信息
    env_info_dict = collect_env()
    env_info = '\n'.join([f'{k}: {v}' for k, v in env_info_dict.items()])
    logger.info('Environment info:\n' + env_info)
    
    # 设置随机种子
    if args.seed is not None:
        logger.info(f'Set random seed to {args.seed}')
        torch.manual_seed(args.seed)
        torch.cuda.manual_seed_all(args.seed)
    
    # 构建数据集
    train_dataset = build_dataset(cfg.data.train)
    val_dataset = build_dataset(cfg.data.val)
    
    # 构建模型
    model = build_detector(cfg.model)
    model.init_weights()
    model = model.to(device)
    
    # 优化器配置
    optimizer = torch.optim.AdamW(model.parameters(), lr=cfg.optimizer.lr)
    
    # 恢复训练
    start_epoch = 0
    metrics_history = []
    if args.resume_from:
        logger.info(f'Resuming from checkpoint: {args.resume_from}')
        start_epoch, metrics_history = load_checkpoint(model, optimizer, args.resume_from, device)
        start_epoch += 1  # 从下一轮开始
    
    # 训练循环
    try:
        for epoch in range(start_epoch, args.epochs):
            logger.info(f'Epoch {epoch+1}/{args.epochs}')
            
            # 训练阶段
            train_detector(
                model,
                train_dataset,
                cfg,
                distributed=False,
                validate=False,
                timestamp=datetime.now().strftime('%Y%m%d_%H%M%S'),
                meta=dict(
                    mmdet_version='2.x',
                    config=cfg.pretty_text
                )
            )
            
            # 验证阶段
            val_outputs = train_detector(
                model,
                val_dataset,
                cfg,
                distributed=False,
                validate=True
            )
            
            # 记录指标
            metrics = {
                'epoch': epoch + 1,
                'train_loss': val_outputs.get('loss', -1),
                'val_accuracy': val_outputs.get('accuracy', -1),
                'learning_rate': cfg.optimizer.lr
            }
            metrics_history.append(metrics)
            
            # 保存检查点
            if (epoch + 1) % args.save_interval == 0:
                save_checkpoint(model, optimizer, epoch + 1, cfg.work_dir, metrics)
                logger.info(f'Saved checkpoint for epoch {epoch + 1}')
            
            # 保存指标历史
            with open(os.path.join(cfg.work_dir, 'metrics_history.json'), 'w') as f:
                json.dump(metrics_history, f, indent=4)
                
    except KeyboardInterrupt:
        logger.info("Training interrupted by user")
        save_checkpoint(model, optimizer, epoch + 1, cfg.work_dir, metrics)
        logger.info(f"Saved checkpoint before exiting at epoch {epoch + 1}")
    except Exception as e:
        logger.error(f"Error occurred: {str(e)}")
        raise e

if __name__ == '__main__':
    main()