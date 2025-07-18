import argparse
import os
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

def train_epoch(model, dataloader, criterion, optimizer, device):
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
            logging.info(f'Batch {batch_idx}/{len(dataloader)}, Loss: {loss.item():.4f}')
    
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
    parser.add_argument('--config', required=True, help='config file path')
    parser.add_argument('--resume', help='checkpoint to resume from')
    parser.add_argument('--epochs', type=int, default=100)
    parser.add_argument('--batch-size', type=int, default=8)
    parser.add_argument('--lr', type=float, default=0.001)
    parser.add_argument('--save-interval', type=int, default=5)
    
    args = parser.parse_args()
    
    # 加载配置
    with open(args.config) as f:
        config = json.load(f)
    
    # 设备配置
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    
    # 创建输出目录
    os.makedirs(config['output_dir'], exist_ok=True)
    logger = setup_logging(config['output_dir'])
    
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
    
    train_loader = DataLoader(train_dataset, batch_size=args.batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=args.batch_size, shuffle=False)
    
    # 模型
    model = UNet(n_channels=3, n_classes=config['num_classes'])
    model = model.to(device)
    
    # 优化器和损失函数
    optimizer = optim.Adam(model.parameters(), lr=args.lr)
    criterion = nn.BCEWithLogitsLoss()
    
    # 恢复训练
    start_epoch = 0
    if args.resume:
        start_epoch, _ = load_checkpoint(model, optimizer, args.resume, device)
        logger.info(f'Resumed from epoch {start_epoch}')
    
    # 训练循环
    try:
        for epoch in range(start_epoch, args.epochs):
            train_loss = train_epoch(model, train_loader, criterion, optimizer, device)
            val_loss = validate(model, val_loader, criterion, device)
            
            logger.info(f'Epoch {epoch+1}/{args.epochs} - Train Loss: {train_loss:.4f}, Val Loss: {val_loss:.4f}')
            
            # 保存检查点
            if (epoch + 1) % args.save_interval == 0:
                metrics = {'train_loss': train_loss, 'val_loss': val_loss}
                save_checkpoint(model, optimizer, epoch + 1, config['output_dir'], metrics)
                
    except KeyboardInterrupt:
        logger.info("Training interrupted by user")
        save_checkpoint(model, optimizer, epoch + 1, config['output_dir'])
        logger.info(f"Saved checkpoint before exiting at epoch {epoch + 1}")

if __name__ == '__main__':
    main()