import argparse
import json
import os
import torch
from torch.utils.data import DataLoader
from models.yolov5 import YOLOv5
from data.dataset import ColonyDataset
from utils.logger import Logger

def train(config_path):
    # 加载配置文件
    with open(config_path) as f:
        config = json.load(f)
    
    # 初始化模型
    model = YOLOv5(config['model'])
    
    # 数据加载
    dataset = ColonyDataset(config['data'])
    dataloader = DataLoader(dataset, batch_size=config['batch_size'], shuffle=True)
    
    # 训练设置
    optimizer = torch.optim.Adam(model.parameters(), lr=config['lr'])
    logger = Logger(config['log_dir'])
    
    # 断点恢复
    if config['resume']:
        checkpoint = torch.load(config['checkpoint'])
        model.load_state_dict(checkpoint['model'])
        optimizer.load_state_dict(checkpoint['optimizer'])
        start_epoch = checkpoint['epoch']
    else:
        start_epoch = 0
    
    # 训练循环
    for epoch in range(start_epoch, config['epochs']):
        for batch_idx, (images, targets) in enumerate(dataloader):
            # 前向传播
            outputs = model(images)
            
            # 计算损失
            loss = model.compute_loss(outputs, targets)
            
            # 反向传播
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            
            # 记录日志
            logger.log({
                'epoch': epoch,
                'batch': batch_idx,
                'loss': loss.item(),
                'lr': optimizer.param_groups[0]['lr']
            })
            
            # 定期保存检查点
            if batch_idx % config['save_interval'] == 0:
                torch.save({
                    'model': model.state_dict(),
                    'optimizer': optimizer.state_dict(),
                    'epoch': epoch
                }, os.path.join(config['checkpoint_dir'], f'checkpoint_{epoch}_{batch_idx}.pth'))
    
    # 保存最终模型
    torch.save(model.state_dict(), os.path.join(config['model_output'], 'final_model.pth'))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', type=str, required=True, help='Path to config file')
    args = parser.parse_args()
    
    train(args.config)