import argparse
import os
import yaml
from ultralytics import YOLO
# 在测试模式下不需要 ColonyDataset
# from data.dataset import ColonyDataset

def train_model(config_path, test_mode=False):
    # 在测试模式下，只打印信息，不实际执行训练
    if test_mode:
        print(f"测试模式：将使用配置文件 {config_path} 进行训练")
        return
    
    # 以下代码在非测试模式下执行
    # 加载配置文件
    with open(config_path) as f:
        config = yaml.safe_load(f)
    
    # 初始化模型
    model = YOLO(config['model']['architecture'])
    
    # 准备数据集
    dataset = ColonyDataset(
        data_dir=config['data']['path'],
        img_size=config['data']['img_size'],
        batch_size=config['train']['batch_size']
    )
    
    # 训练配置
    train_args = {
        'data': dataset.get_config(),
        'epochs': config['train']['epochs'],
        'imgsz': config['data']['img_size'][0] if isinstance(config['data']['img_size'], list) else config['data']['img_size'],
        'batch': config['train']['batch_size'],
        'device': config['train']['device']
    }
    
    if test_mode:
        print("--- 测试模式: 跳过训练 ---")
        return None

    # 开始训练
    results = model.train(**train_args)
    
    # 保存最佳模型
    model.save(os.path.join(config['output']['path'], 'best.pt'))
    
    return results

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', type=str, required=True, 
                       help='Path to config file')
    parser.add_argument('--test-mode', action='store_true', 
                       help='Run in test mode')
    args = parser.parse_args()
    
    train_model(args.config, args.test_mode)
# 添加支持从 checkpoint 恢复训练的功能
# 添加记录详细训练参数的功能
# 添加实时显示训练参数的功能