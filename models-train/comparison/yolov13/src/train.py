import argparse
import os
import yaml
import torch
import sys

# 添加当前目录到 Python 路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from ultralytics import YOLO
except ImportError as e:
    print(f"导入错误: {e}")
    print("ultralytics 库可能未安装，在测试模式下将模拟其功能")

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

def train_model(config_path, resume_from=None, test_mode=False):
    # 加载配置
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
    except FileNotFoundError:
        print(f"错误：配置文件 {config_path} 不存在")
        return None
    except Exception as e:
        print(f"加载配置文件时出错: {e}")
        return None
    
    if test_mode:
        print(f"测试模式：将使用配置文件 {config_path} 进行训练")
        print(f"配置信息: {config}")
        return "测试模式下的模拟结果"
    
    # 创建输出目录
    os.makedirs(config['output']['path'], exist_ok=True)
    logger = setup_logging(config['output']['path'])
    
    # 初始化模型
    try:
        model = YOLO(config['model']['architecture'])
    except Exception as e:
        print(f"初始化模型时出错: {e}")
        return None
    
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
        'epochs': 12,  # 修改为统一的训练轮数
        'imgsz': config['data']['img_size'][0],
        'batch': config['train']['batch_size'],
        'device': config['train']['device'],
        'workers': config['train']['workers'],
        'lr0': config['train']['lr0'],
        'lrf': config['train']['lrf'],
        'momentum': config['train']['momentum'],
        'weight_decay': config['train']['weight_decay'],
        'save_period': 1,  # 每轮保存一次
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
    parser.add_argument('--test-mode', action='store_true', help='Run in test mode without actual training')
    args = parser.parse_args()
    
    try:
        print(f"配置文件路径: {args.config}")
        print(f"测试模式: {args.test_mode}")
        
        result = train_model(args.config, args.resume, args.test_mode)
        if result is None:
            print("训练失败")
            sys.exit(1)
    except Exception as e:
        print(f"运行时出错: {e}")
        sys.exit(1)