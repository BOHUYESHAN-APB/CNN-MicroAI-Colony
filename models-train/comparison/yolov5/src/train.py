import argparse
import json
import os
import sys
import yaml
import torch
from torch.utils.data import DataLoader

# 添加当前目录到 Python 路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 修改导入路径
try:
    from models.yolov5 import YOLOv5
    from data.dataset import ColonyDataset
    from utils.logger import Logger
except ImportError as e:
    print(f"导入错误: {e}")
    print(f"当前 Python 路径: {sys.path}")
    print(f"当前工作目录: {os.getcwd()}")
    print(f"脚本目录: {os.path.dirname(os.path.abspath(__file__))}")
    sys.exit(1)

def train(config_path, test_mode=False):
    # 在测试模式下，只打印信息，不实际执行训练
    if test_mode:
        print(f"测试模式：将使用配置文件 {config_path} 进行训练")
        return
        
    # 加载配置文件
    with open(config_path) as f:
        config = yaml.safe_load(f)
    
    # 初始化模型
    model = YOLOv5(config['model'])
    
    # 数据加载
    dataset = ColonyDataset(config['data'])
    dataloader = DataLoader(dataset, batch_size=config['training']['batch_size'], shuffle=True)
    
    # 训练设置
    optimizer = torch.optim.Adam(model.parameters(), lr=config['optimizer']['lr'], weight_decay=config['optimizer']['weight_decay'])
    logger = Logger(os.path.join('logs', 'yolov5'))
    
    # 断点恢复
    start_epoch = 0
    if 'resume' in config.get('training', {}) and config['training']['resume']:
        checkpoint_path = config['training'].get('checkpoint', '')
        if os.path.exists(checkpoint_path):
            checkpoint = torch.load(checkpoint_path)
            model.load_state_dict(checkpoint['model'])
            optimizer.load_state_dict(checkpoint['optimizer'])
            start_epoch = checkpoint['epoch'] + 1
    
    # 训练循环
    for epoch in range(start_epoch, config['training']['epochs']):
        for batch_idx, (images, targets) in enumerate(dataloader):
            # 前向传播
            loss = model(images, targets)
            
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
            if batch_idx % config['training']['save_interval'] == 0:
                torch.save({
                    'model': model.state_dict(),
                    'optimizer': optimizer.state_dict(),
                    'epoch': epoch
                }, os.path.join('checkpoints', f'checkpoint_{epoch}_{batch_idx}.pth'))
    
    # 保存最终模型
    torch.save(model.state_dict(), os.path.join('model_output', 'final_model.pth'))

# 此处已删除重复的 train 函数定义

if __name__ == '__main__':
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument('--config', type=str, required=True, help='Path to config file')
        parser.add_argument('--test-mode', action='store_true', help='Run in test mode')
        args = parser.parse_args()
        
        print(f"配置文件路径: {args.config}")
        print(f"测试模式: {args.test_mode}")
        
        if not os.path.exists(args.config):
            print(f"错误: 配置文件 {args.config} 不存在")
            sys.exit(1)
            
        train(args.config, args.test_mode)
    except Exception as e:
        import traceback
        print(f"发生错误: {e}")
        print(traceback.format_exc())
        sys.exit(1)