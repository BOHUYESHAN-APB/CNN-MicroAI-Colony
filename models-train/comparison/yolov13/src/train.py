import argparse
import os
import sys
import yaml
from ultralytics import YOLO

# 将项目根目录添加到 Python 路径中，以确保可以正确导入模块
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

def create_dataset_yaml(data_path, train_dir, val_dir, class_names):
    """动态创建 ultralytics 所需的 data.yaml 文件"""
    dataset_yaml_path = os.path.join(data_path, 'data.yaml')
    
    # 从 class_names 派生 num_classes
    num_classes = len(class_names)
    
    yaml_content = {
        'path': os.path.abspath(data_path),
        'train': os.path.join(train_dir),
        'val': os.path.join(val_dir),
        'names': {i: name for i, name in enumerate(class_names)}
    }
    
    with open(dataset_yaml_path, 'w', encoding='utf-8') as f:
        yaml.dump(yaml_content, f, allow_unicode=True, default_flow_style=False)
        
    return dataset_yaml_path

def train_yolov13(config_path):
    """
    使用指定的配置文件训练 YOLOv13 模型。
    """
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
    except FileNotFoundError:
        print(f"错误: 配置文件 '{config_path}' 未找到。")
        return
    except Exception as e:
        print(f"错误: 加载配置文件时出错: {e}")
        return

    # 创建 data.yaml 文件
    # 假设 class_names 在此项目中是固定的
    class_names = ['class1', 'class2'] 
    dataset_yaml = create_dataset_yaml(
        config['data']['path'],
        'images/train',
        'images/val',
        class_names
    )

    # 初始化模型，并处理模型文件不存在的情况
    model_name = config['model']['architecture']
    try:
        model = YOLO(model_name)
    except FileNotFoundError:
        print(f"警告: 未找到模型 '{model_name}'。将回退到 'yolov8n.pt'。")
        try:
            model = YOLO('yolov8n.pt')
        except Exception as e:
            print(f"错误: 回退模型 'yolov8n.pt' 也无法加载: {e}")
            return
    except Exception as e:
        print(f"错误: 初始化模型时出错: {e}")
        return

    # 开始训练
    try:
        model.train(
            data=dataset_yaml,
            epochs=config['train']['epochs'],
            batch=config['train']['batch_size'],
            imgsz=config['data']['img_size'],
            device=config['train']['device'],
            resume=config['train'].get('resume', False) # 使用 .get() 避免 KeyError
        )
    except Exception as e:
        print(f"错误: 训练过程中发生错误: {e}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Train YOLOv13 model.")
    parser.add_argument('--config', type=str, required=True, help='Path to the configuration file.')
    args = parser.parse_args()
    
    train_yolov13(args.config)