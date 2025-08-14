import sys
import os

# Add the 'unet' model directory to the Python path to resolve module imports
unet_model_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if unet_model_root not in sys.path:
    sys.path.insert(0, unet_model_root)

import argparse
import json
import logging
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from torchvision import transforms
from src.data.dataset import ColonyDataset
from src.models.unet import UNet
from datetime import datetime

def setup_logging(save_dir):
    """配置日志记录"""
    log_file = os.path.join(save_dir, 'training.log')
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
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

def train_epoch(model, dataloader, criterion, optimizer, device, logger):
    """训练一个epoch"""
    model.train()
    total_loss = 0
    for batch_idx, (images, masks) in enumerate(dataloader):
        images, masks = images.to(device), masks.to(device)
        
        optimizer.zero_grad()
        outputs = model(images)
        loss = criterion(outputs, masks)
        loss.backward()
        optimizer.step()
        
        total_loss += loss.item()
        
        # 可视化进度
        if batch_idx % 10 == 0:
            logger.info(f'Batch {batch_idx}/{len(dataloader)}, Loss: {loss.item():.4f}')
    
    return total_loss / len(dataloader)

def validate(model, dataloader, criterion, device):
    """验证"""
    model.eval()
    total_loss = 0
    with torch.no_grad():
        for images, masks in dataloader:
            images, masks = images.to(device), masks.to(device)
            outputs = model(images)
            loss = criterion(outputs, masks)
            total_loss += loss.item()
    return total_loss / len(dataloader)

def main():
    parser = argparse.ArgumentParser(description='Train U-Net for colony segmentation')
    parser.add_argument('--config', default='../configs/unet_config.json', help='config file path')
    parser.add_argument('--resume', help='checkpoint to resume from')
    
    args = parser.parse_args()
    
    # 加载配置
    config_path = args.config
    script_dir = os.path.dirname(__file__)
    if not os.path.isabs(config_path):
        config_path = os.path.join(script_dir, config_path)

    with open(config_path) as f:
        config = json.load(f)
    
    # 将data_dir转换为绝对路径
    if not os.path.isabs(config['data_dir']):
        config['data_dir'] = os.path.abspath(os.path.join(os.path.dirname(config_path), config['data_dir']))

    # 设备配置
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    
    # 创建输出目录
    output_dir = config['output_dir']
    if not os.path.isabs(output_dir):
        output_dir = os.path.join(script_dir, output_dir)
    os.makedirs(output_dir, exist_ok=True)
    logger = setup_logging(output_dir)
    
    logger.info(f"Config: {json.dumps(config, indent=4)}")

    # 数据集
    train_dataset = ColonyDataset(
        data_dir=config['data_dir'],
        split='train',
        img_size=config['img_size']
    )
    val_dataset = ColonyDataset(
        data_dir=config['data_dir'],
        split='val',
        img_size=config['img_size']
    )
    
    if len(train_dataset) == 0:
        logger.warning("Training dataset is empty. Please check your data and configuration. Exiting.")
        return

    train_loader = DataLoader(train_dataset, batch_size=config['batch_size'], shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=config['batch_size'], shuffle=False)
    
    # 模型
    model = UNet(n_channels=3, n_classes=config['num_classes'])
    model = model.to(device)
    
    # 优化器和损失函数
    optimizer = optim.Adam(model.parameters(), lr=config['lr'])
    criterion = nn.BCEWithLogitsLoss()
    
    # 恢复训练
    start_epoch = 0
    if args.resume:
        start_epoch, _ = load_checkpoint(model, optimizer, args.resume, device)
        logger.info(f'Resumed from epoch {start_epoch}')
    
    # 训练循环
    try:
        for epoch in range(start_epoch, config['epochs']):
            train_loss = train_epoch(model, train_loader, criterion, optimizer, device, logger)
            val_loss = validate(model, val_loader, criterion, device)
            
            logger.info(f"Epoch {epoch+1}/{config['epochs']} - Train Loss: {train_loss:.4f}, Val Loss: {val_loss:.4f}")
            
            # 保存检查点
            if (epoch + 1) % config['save_interval'] == 0:
                metrics = {'train_loss': train_loss, 'val_loss': val_loss}
                save_checkpoint(model, optimizer, epoch + 1, output_dir, metrics)
                
    except KeyboardInterrupt:
        logger.info("Training interrupted by user")
        save_checkpoint(model, optimizer, epoch + 1, output_dir)
        logger.info(f"Saved checkpoint before exiting at epoch {epoch + 1}")

if __name__ == '__main__':
    main()