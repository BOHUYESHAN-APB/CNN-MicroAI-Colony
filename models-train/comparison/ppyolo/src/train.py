import argparse
import os
import yaml
import paddle
import logging
from src.data.dataset import ColonyDataset

def setup_logging(save_dir):
    """设置日志记录"""
    log_file = os.path.join(save_dir, 'training.log')
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger()

def train_model(config_path, resume_checkpoint=None):
    # 加载配置文件
    with open(config_path) as f:
        config = yaml.safe_load(f)
    
    # 创建输出目录
    output_dir = config['output']['path']
    os.makedirs(output_dir, exist_ok=True)

    # 设置日志
    logger = setup_logging(output_dir)
    
    # 设置PaddlePaddle环境
    paddle.set_device(config['train']['device'])
    
    # 记录配置信息
    logger.info(f'Config:\n{yaml.dump(config, allow_unicode=True)}')

    # 准备数据集
    train_dataset = ColonyDataset(
        data_dir=os.path.join(config['data']['path'], config['data']['train']),
        img_size=config['data']['img_size'],
        is_train=True
    )
    
    val_dataset = ColonyDataset(
        data_dir=os.path.join(config['data']['path'], config['data']['val']),
        img_size=config['data']['img_size'],
        is_train=False
    )

    # 创建模型
    model = paddle.vision.models.detection.PPYOLO(
        num_classes=config['model']['num_classes'],
        backbone=config['model']['architecture']
    )

    # 从 checkpoint 恢复训练
    if resume_checkpoint and os.path.exists(resume_checkpoint):
        model.set_state_dict(paddle.load(resume_checkpoint))
        logger.info(f"从 {resume_checkpoint} 恢复训练")

    # 训练配置
    optimizer = paddle.optimizer.Adam(
        learning_rate=config['train']['learning_rate'],
        parameters=model.parameters()
    )

    # 训练循环
    for epoch in range(config['train']['epochs']):
        model.train()
        total_loss = 0
        for batch_id, data in enumerate(train_dataset):
            outputs = model(data['image'], data['target'])
            loss = outputs['loss']
            loss.backward()
            optimizer.step()
            optimizer.clear_grad()
            total_loss += loss.item()
        
        avg_loss = total_loss / len(train_dataset)
        logger.info(f"Epoch {epoch + 1}/{config['train']['epochs']}, Loss: {avg_loss:.4f}")

        # 验证
        model.eval()
        # ... 验证代码 ...

    # 保存模型
    save_path = os.path.join(output_dir, 'model_final.pdparams')
    paddle.save(model.state_dict(), save_path)
    logger.info(f"模型已保存到 {save_path}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', required=True, help='Path to config file')
    parser.add_argument('--resume', help='Path to checkpoint to resume from')
    args = parser.parse_args()
    train_model(args.config, args.resume)