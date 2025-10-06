import os
import json
import subprocess
import glob
import re

# 获取脚本所在的目录
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# 状态文件的路径
STATE_FILE = os.path.join(SCRIPT_DIR, 'training_state.json')

# 模型训练根目录
MODELS_BASE_DIR = os.path.join(SCRIPT_DIR, 'models-train', 'comparison')

def get_models_to_train():
    """获取所有需要训练的模型目录列表"""
    if not os.path.exists(MODELS_BASE_DIR):
        print(f"错误: 模型目录 '{MODELS_BASE_DIR}' 不存在。请确保脚本位于项目根目录。")
        return []
    return [d for d in os.listdir(MODELS_BASE_DIR) if os.path.isdir(os.path.join(MODELS_BASE_DIR, d))]

def load_state():
    """加载训练状态"""
    if not os.path.exists(STATE_FILE):
        return {'last_completed_model': None}
    try:
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {'last_completed_model': None}

def save_state(last_completed_model):
    """保存训练状态"""
    with open(STATE_FILE, 'w') as f:
        json.dump({'last_completed_model': last_completed_model}, f, indent=4)

def find_latest_checkpoint(model_dir):
    """在模型目录中查找最新的检查点文件"""
    # 检查 mmdetection 的 'latest.pth'
    latest_pth = os.path.join(model_dir, 'latest.pth')
    if os.path.exists(latest_pth):
        return latest_pth

    # 检查 ppyolo 的 'latest_model.pdparams'
    latest_pdparams = os.path.join(model_dir, 'output', 'latest_model.pdparams')
    if os.path.exists(latest_pdparams):
        return latest_pdparams
        
    # 检查 ultralytics 的检查点
    yolo_runs_dir = os.path.join(model_dir, 'runs', 'detect')
    if os.path.exists(yolo_runs_dir):
        # 查找最新的 'train' 目录
        exp_dirs = sorted(glob.glob(os.path.join(yolo_runs_dir, 'train*')), key=os.path.getmtime, reverse=True)
        if exp_dirs:
            weights_dir = os.path.join(exp_dirs[0], 'weights')
            last_pt = os.path.join(weights_dir, 'last.pt')
            if os.path.exists(last_pt):
                return last_pt

    return None

def run():
    """主执行函数"""
    state = load_state()
    all_models = sorted(get_models_to_train())
    
    if not all_models:
        return # 如果没有找到模型目录，则退出

    start_index = 0
    if state['last_completed_model'] in all_models:
        start_index = all_models.index(state['last_completed_model']) + 1
        if start_index < len(all_models):
            print(f"上次训练完成到 '{state['last_completed_model']}'。从 '{all_models[start_index]}' 开始继续。")
        else:
            print("所有模型都已训练完成。")
            return

    if start_index >= len(all_models):
        print("所有模型都已训练完成。")
        return

    models_to_run = all_models[start_index:]

    for model_name in models_to_run:
        print(f"\n{'='*60}\n准备训练模型: {model_name}\n{'='*60}")
        
        model_dir = os.path.join(MODELS_BASE_DIR, model_name)
        command = []
        
        # 查找最新的检查点
        checkpoint_path = find_latest_checkpoint(model_dir)
        
        # 根据模型类型构建命令
        if model_name == 'ppyolo':
            script = os.path.join(model_dir, 'tools', 'train.py')
            config = os.path.join(model_dir, 'configs', 'ppyolo_coco.yaml')
            command = ['python', script, '-c', config]
            if checkpoint_path:
                command.extend(['-r', checkpoint_path])
        else: # 所有其他模型
            script = os.path.join(model_dir, 'src', 'train.py')
            
            # 查找配置文件
            config_file = next(glob.iglob(os.path.join(model_dir, 'configs', '*.*')), None)
            
            if os.path.exists(script) and config_file:
                if model_name.startswith('yolo') or model_name == 'unet':
                    command = ['python', script, '--config', config_file]
                else: # mmdetection 系列
                    command = ['python', script, config_file]
                
                if checkpoint_path:
                    if not model_name.startswith('yolo'): # YOLO 的 resume 由脚本内部处理
                         command.append(f'--resume-from {checkpoint_path}')
                    else:
                        print(f"检测到 YOLO 检查点，将尝试从 '{checkpoint_path}' 恢复。")
            else:
                print(f"警告: 在 '{model_dir}' 中未找到训练脚本或配置文件。")
                continue

        if not command:
            print(f"无法为模型 '{model_name}' 构建命令。跳过。")
            continue
            
        print(f"执行命令: {' '.join(command)}")
        
        try:
            # 在模型自己的目录中执行命令
            result = subprocess.run(command, check=True, cwd=model_dir)
            if result.returncode == 0:
                print(f"模型 '{model_name}' 训练成功。")
                save_state(model_name)
            else:
                print(f"模型 '{model_name}' 训练失败，返回码: {result.returncode}。脚本将终止。")
                break
        except subprocess.CalledProcessError as e:
            print(f"模型 '{model_name}' 训练期间发生错误: {e}。脚本将终止。")
            break
        except KeyboardInterrupt:
            print(f"\n用户中断。在模型 '{model_name}' 处停止。")
            break
            
    else: # for 循环正常结束
        print("\n所有模型训练任务已成功执行完毕。")

if __name__ == '__main__':
    run()