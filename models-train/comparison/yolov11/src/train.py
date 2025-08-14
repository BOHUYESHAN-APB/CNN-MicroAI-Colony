import argparse
import os
import yaml
from ultralytics import YOLO

def train_model(config_path, test_mode=False):
    # 在测试模式下，只打印信息，不实际执行训练
    if test_mode:
        print(f"测试模式：将使用配置文件 {config_path} 进行训练")
        return
    
    # 以下代码在非测试模式下执行
    # 加载配置文件
    try:
        with open(config_path, encoding='utf-8') as f:
            config = yaml.safe_load(f)
    except Exception as e:
        print(f"加载配置文件时出错: {e}")
        return

    # 初始化模型
    model_name = config['model']['type'] + '.pt'
    try:
        model = YOLO(model_name)
    except FileNotFoundError:
        print(f"警告: 未找到 '{model_name}'。将回退到 'yolov8n.pt'。")
        try:
            model = YOLO('yolov8n.pt')
        except ConnectionError as e:
            print(f"下载预训练模型时出错: {e}")
            print("请检查您的网络连接，或手动下载 'yolov8n.pt' 模型。")
            return
        except Exception as e:
            print(f"初始化备用模型时出错: {e}")
            return
    except ConnectionError as e:
        print(f"下载预训练模型时出错: {e}")
        print(f"请检查您的网络连接，或手动下载 '{model_name}' 模型。")
        return
    except Exception as e:
        print(f"初始化模型时出错: {e}")
        return
    
    # 训练配置
    train_args = {
        'data': config['dataset']['train']['ann_file'],
        'epochs': config['train_cfg']['epochs'],
        'imgsz': config['dataset']['img_size'],
        'batch': config['dataset']['batch_size'],
        'device': 0
    }
    
    if test_mode:
        print("--- 测试模式: 跳过训练 ---")
        return None

    # 开始训练
    try:
        results = model.train(**train_args)
    except Exception as e:
        print(f"训练过程中出错: {e}")
        return

    # 保存最佳模型
    output_path = config['work_dir']
    os.makedirs(output_path, exist_ok=True)
    model.save(os.path.join(output_path, 'best.pt'))
    
    return results

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', type=str, required=True, 
                       help='Path to config file')
    parser.add_argument('--test-mode', action='store_true', 
                       help='Run in test mode')
    args = parser.parse_args()
    
    train_model(args.config, args.test_mode)