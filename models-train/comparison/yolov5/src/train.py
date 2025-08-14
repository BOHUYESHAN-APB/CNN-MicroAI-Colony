import sys
import os

# Add the 'yolov5' model directory to the Python path to resolve module imports
yolov5_model_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if yolov5_model_root not in sys.path:
    sys.path.insert(0, yolov5_model_root)

import argparse
import yaml
import os
import torch
import torch.optim as optim
from torch.utils.data import DataLoader
from src.models.yolov5 import YOLOv5
from src.data.dataset import ColonyDataset
from src.utils.logger import Logger

def train(config_path, test_mode=False):
    """
    训练YOLOv5模型。

    Args:
        config_path (str): 配置文件路径。
        test_mode (bool): 是否为测试模式。
    """
    print(f"配置文件路径: {config_path}")
    print(f"测试模式: {test_mode}")

    try:
        # 加载配置文件
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        # 初始化日志记录器
        logger = Logger(config['logging'])

        # 设备配置
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

        # 数据加载
        train_dataset = ColonyDataset(config['data']['train_path'])
        train_loader = DataLoader(train_dataset, batch_size=config['training']['batch_size'], shuffle=True)

        # 模型、优化器、损失函数
        model = YOLOv5(num_classes=int(config['model']['num_classes'])).to(device)
        optimizer = optim.Adam(model.parameters(), lr=config['optimizer']['lr'])
        criterion = torch.nn.CrossEntropyLoss()

        # 恢复训练
        if config['training']['resume']:
            checkpoint = torch.load(config['training']['checkpoint'])
            model.load_state_dict(checkpoint['model_state_dict'])
            optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
            start_epoch = checkpoint['epoch']
            logger.log(f"从 epoch {start_epoch} 恢复训练。")
        else:
            start_epoch = 0

        # 训练循环
        for epoch in range(start_epoch, config['training']['epochs']):
            for images, labels in train_loader:
                images, labels = images.to(device), labels.to(device)

                # 前向传播
                outputs = model(images)
                loss = criterion(outputs, labels)

                # 反向传播和优化
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()

            # 记录日志
            logger.log(f"Epoch [{epoch+1}/{config['training']['epochs']}], Loss: {loss.item():.4f}")

            # 保存模型
            if (epoch + 1) % config['training']['save_interval'] == 0:
                checkpoint_path = os.path.join(logger.checkpoint_dir, f'yolov5_epoch_{epoch+1}.pth')
                torch.save({
                    'epoch': epoch + 1,
                    'model_state_dict': model.state_dict(),
                    'optimizer_state_dict': optimizer.state_dict(),
                    'loss': loss,
                }, checkpoint_path)

        # 保存最终模型
        final_model_path = os.path.join(logger.model_output_dir, 'yolov5_final.pth')
        model.save(final_model_path)
        logger.log(f"训练完成，最终模型保存在: {final_model_path}")

    except Exception as e:
        print(f"发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', type=str, required=True, help='配置文件路径')
    parser.add_argument('--test-mode', action='store_true', help='是否在测试模式下运行')
    args = parser.parse_args()
    train(args.config, args.test_mode)