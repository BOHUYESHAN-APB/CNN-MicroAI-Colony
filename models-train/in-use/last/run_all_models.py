import os
import subprocess
import json
from pathlib import Path

# 配置路径
LAST_MODELS_PATH = "models-train/in-use/last"
COMPARISON_MODELS_PATH = "models-train/comparison"
STATUS_FILE = "run_status.json"

def load_status():
    """加载运行状态"""
    if os.path.exists(STATUS_FILE):
        with open(STATUS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_status(status):
    """保存运行状态"""
    with open(STATUS_FILE, "w") as f:
        json.dump(status, f, indent=4)

def run_model(model_path, status):
    """运行单个模型"""
    model_name = Path(model_path).name
    if status.get(model_name, {}).get("completed", False):
        print(f"模型 {model_name} 已完成，跳过...")
        return

    print(f"运行模型: {model_name}")
    try:
        subprocess.run(["python", f"{model_path}/src/train.py"], check=True)
        status[model_name] = {"completed": True}
    except subprocess.CalledProcessError as e:
        print(f"模型 {model_name} 运行失败: {e}")
        status[model_name] = {"completed": False}

    save_status(status)

def main():
    """主函数"""
    print("开始批量运行所有模型训练...")
    status = load_status()

    # 运行 last 目录中的模型
    print("运行 last 目录中的模型...")
    for model_dir in Path(LAST_MODELS_PATH).iterdir():
        if model_dir.is_dir() and (model_dir / "src/train.py").exists():
            run_model(model_dir, status)

    # 运行 comparison 目录中的模型
    print("运行 comparison 目录中的模型...")
    for model_dir in Path(COMPARISON_MODELS_PATH).iterdir():
        if model_dir.is_dir() and (model_dir / "src/train.py").exists():
            run_model(model_dir, status)

    print("所有模型训练完成！")

if __name__ == "__main__":
    main()