import os
import sys
import torch
from torch.utils.data import DataLoader
from src.data.dataset import ColonyDataset
from src.models.colony_detector import ColonyDetector

def main():
    # 初始化配置
    config = {
        'batch_size': 4,
        'num_epochs': 50,
        'learning_rate': 0.001,
        'data_path': 'data/images',
        'checkpoint_dir': 'checkpoints',
        'model_output_dir': 'model_output',
        'resume_checkpoint': None  # 设置为 checkpoint 路径以恢复训练
    }

    # 创建目录
    os.makedirs(config['checkpoint_dir'], exist_ok=True)
    os.makedirs(config['model_output_dir'], exist_ok=True)

    # 初始化模型和数据
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = ColonyDetector().to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=config['learning_rate'])
    start_epoch = 0

    # 恢复训练
    if config['resume_checkpoint']:
        checkpoint = torch.load(config['resume_checkpoint'])
        model.load_state_dict(checkpoint['model_state_dict'])
        optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        start_epoch = checkpoint['epoch'] + 1
        print(f"从 checkpoint 恢复训练，起始 epoch: {start_epoch}")

    dataset = ColonyDataset(config['data_path'])
    dataloader = DataLoader(dataset, batch_size=config['batch_size'], shuffle=True)

    # 训练循环
    for epoch in range(start_epoch, config['num_epochs']):
        model.train()
        epoch_loss = 0
        for batch in dataloader:
            # 假设 batch 包括输入和标签
            inputs, labels = batch
            inputs, labels = inputs.to(device), labels.to(device)

            optimizer.zero_grad()
            outputs = model(inputs)
            loss = torch.nn.functional.cross_entropy(outputs, labels)
            loss.backward()
            optimizer.step()

            epoch_loss += loss.item()

        # 保存 checkpoint
        checkpoint_path = os.path.join(config['checkpoint_dir'], f'checkpoint_epoch_{epoch}.pth')
        torch.save({
            'epoch': epoch,
            'model_state_dict': model.state_dict(),
            'optimizer_state_dict': optimizer.state_dict(),
            'loss': epoch_loss
        }, checkpoint_path)

        # 输出训练信息
        print(f"Epoch [{epoch}/{config['num_epochs']}], Loss: {epoch_loss:.4f}")

    # 保存最终模型
    torch.save(model.state_dict(),
               os.path.join(config['model_output_dir'], 'final_model.pth'))

if __name__ == '__main__':
    main()
# 添加记录详细训练参数的功能
# 添加实时显示训练参数的功能