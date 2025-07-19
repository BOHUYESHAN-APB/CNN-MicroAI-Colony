import argparse
import os
import yaml
import torch
from ultralytics import YOLO
from src.data.dataset import ColonyDataset
import logging
from datetime import datetime
import json

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

def save_checkpoint(model, epoch, save_dir, metrics=None):
    """保存检查点"""
    checkpoint = {
        'epoch': epoch,
        'model_state_dict': model.state_dict(),
        'metrics': metrics or {}
    }
    path = os.path.join(save_dir, f'checkpoint_epoch_{epoch}.pt')
    torch.save(checkpoint, path)
    return path

def load_checkpoint(model, checkpoint_path):
    """加载检查点"""
    checkpoint = torch.load(checkpoint_path, map_location='cpu')
    model.load_state_dict(checkpoint['model_state_dict'])
    return checkpoint['epoch'], checkpoint.get('metrics', None)

def train_model(config_path, resume_from=None):
    # 加载配置
    with open(config_path) as f:
        config = yaml.safe_load(f)
    
    # 创建输出目录
    os.makedirs(config['output']['path'], exist_ok=True)
    logger = setup_logging(config['output']['path'])
    
    # 初始化模型
    model = YOLO(config['model']['architecture'])
    
    # 数据集配置
    data_config = {
        'path': config['data']['path'],
        'train': config['data']['train'],
        'val': config['data']['val'],
        'test': config['data']['test'],
        'nc': config['model']['num_classes'],
        'names': [f'class_{i}' for i in range(config['model']['num_classes'])]
    }
    
    # 保存数据配置
    data_yaml = os.path.join(config['output']['path'], 'data.yaml')
    with open(data_yaml, 'w') as f:
        yaml.dump(data_config, f)
    
    # 训练参数
    train_args = {
        'data': data_yaml,
        'epochs': config['train']['epochs'],
        'imgsz': config['data']['img_size'][0],
        'batch': config['train']['batch_size'],
        'device': config['train']['device'],
        'workers': config['train']['workers'],
        'lr0': config['train']['lr0'],
        'lrf': config['train']['lrf'],
        'momentum': config['train']['momentum'],
        'weight_decay': config['train']['weight_decay'],
        'save_period': config['output']['save_interval'],
        'project': config['output']['path'],
        'name': 'yolov13_training'
    }
    
    # 恢复训练
    start_epoch = 0
    if resume_from:
        logger.info(f'Resuming from checkpoint: {resume_from}')
        start_epoch, _ = load_checkpoint(model, resume_from)
    
    # 开始训练
    results = model.train(**train_args)
    
    # 保存最终模型
    model.save(os.path.join(config['output']['path'], 'best.pt'))
    
    return results

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', type=str, required=True, help='Path to config file')
    parser.add_argument('--resume', type=str, help='Path to checkpoint to resume from')
    args = parser.parse_args()
    
    train_model(args.config, args.resume)
# 添加记录详细训练参数的功能
# 添加实时显示训练参数的功能