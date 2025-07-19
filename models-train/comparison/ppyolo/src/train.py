import argparse
import os
import yaml
import paddle
from src.data.dataset import ColonyDataset

def train_model(config_path):
    # 加载配置文件
    with open(config_path) as f:
        config = yaml.safe_load(f)
    
    # 设置PaddlePaddle环境
    paddle.set_device(config['train']['device'])
    
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

    # 训练配置
    optimizer = paddle.optimizer.Adam(
        learning_rate=config['train']['learning_rate'],
        parameters=model.parameters()
    )

    # 训练循环
    for epoch in range(config['train']['epochs']):
        model.train()
        for batch_id, data in enumerate(train_dataset):
            outputs = model(data['image'], data['target'])
            loss = outputs['loss']
            loss.backward()
            optimizer.step()
            optimizer.clear_grad()

        # 验证
        model.eval()
        # ... 验证代码 ...

    # 保存模型
    paddle.save(model.state_dict(), 
               os.path.join(config['output']['path'], 'model_final.pdparams'))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', required=True, help='Path to config file')
    args = parser.parse_args()
    train_model(args.config)
# 添加支持从 checkpoint 恢复训练的功能
# 添加记录详细训练参数的功能
# 添加实时显示训练参数的功能