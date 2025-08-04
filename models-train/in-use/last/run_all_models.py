import os
import subprocess
import json
import importlib.util
import sys
import traceback
from pathlib import Path

# 启用详细调试
debug_mode = True

def debug_print(*args, **kwargs):
    if debug_mode:
        print("[DEBUG]", *args, **kwargs)

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

def check_dependencies(model_name):
    """检查模型所需的依赖库是否已安装"""
    # 常见模型依赖库映射
    model_dependencies = {
        "yolov5": ["torch", "yaml"],
        "yolov8": ["torch", "yaml", "ultralytics"],
        "yolov12": ["torch", "yaml"],
        "yolov13": ["torch", "yaml"],
        "faster_rcnn_resnet50": ["torch", "torchvision"],
        "cascade_rcnn": ["torch", "mmdet"],
        "detectors": ["torch", "mmdet"],
        "htc": ["torch", "mmdet"],
        "mask_rcnn": ["torch", "torchvision"],
        "unet": ["torch"],
        "ppyolo": ["paddle", "yaml"],
    }
    
    # 获取模型依赖
    dependencies = model_dependencies.get(model_name, ["torch"])
    missing_deps = []
    
    # 检查依赖是否已安装
    for dep in dependencies:
        if importlib.util.find_spec(dep) is None:
            missing_deps.append(dep)
    
    return missing_deps

def run_model(model_path, status, test_mode=False):
    """运行单个模型"""
    model_name = Path(model_path).name
    debug_print(f"处理模型: {model_name}, 路径: {model_path}")
    
    if status.get(model_name, {}).get("completed", False):
        print(f"模型 {model_name} 已完成，跳过...")
        return

    print(f"运行模型: {model_name}")
    
    # 检查依赖
    missing_deps = check_dependencies(model_name)
    debug_print(f"模型 {model_name} 的依赖检查结果: {missing_deps}")
    
    if missing_deps:
        print(f"模型 {model_name} 缺少依赖库: {', '.join(missing_deps)}")
        print(f"请使用命令安装: pip install {' '.join(missing_deps)}")
        status[model_name] = {"completed": False, "missing_deps": missing_deps}
        save_status(status)
        return
    
    try:
        # 检查训练脚本是否存在
        train_script = f"{model_path}/src/train.py"
        debug_print(f"检查训练脚本: {train_script}, 存在: {os.path.exists(train_script)}")
        
        if not os.path.exists(train_script):
            print(f"错误: 训练脚本 {train_script} 不存在")
            status[model_name] = {"completed": False, "error": "训练脚本不存在"}
            save_status(status)
            return
        
        command = ["python", train_script]
        
        # 添加配置文件参数
        if "yolov8" in model_name:
            config_path = os.path.join(model_path, "configs", "yolov8_coco.yaml")
            command.extend(["--config", config_path])
        elif "yolov5" in model_name:
            config_path = os.path.join(model_path, "configs", "yolov5_coco.yaml")
            command.extend(["--config", config_path])
        elif "yolov13" in model_name:
            config_path = os.path.join(model_path, "configs", "yolov13_coco.yaml")
            command.extend(["--config", config_path])
        elif "yolov12" in model_name:
            config_path = os.path.join(model_path, "configs", "yolov12_coco.yaml")
            command.extend(["--config", config_path])
            
        if test_mode:
            command.append("--test-mode")
        
        debug_print(f"执行命令: {' '.join(command)}")
        try:
            # 捕获标准输出和标准错误，使用 UTF-8 编码
            result = subprocess.run(command, check=True, capture_output=True, text=True, encoding='utf-8')
            print(result.stdout)
        except subprocess.CalledProcessError as e:
            print(f"命令执行失败，退出码: {e.returncode}")
            print(f"标准输出: {e.stdout}")
            print(f"标准错误: {e.stderr}")
            raise
        status[model_name] = {"completed": True}
    except subprocess.CalledProcessError as e:
        print(f"模型 {model_name} 运行失败: {e}")
        debug_print(f"运行失败详情: {traceback.format_exc()}")
        status[model_name] = {"completed": False}
    except Exception as e:
        print(f"模型 {model_name} 出现未知错误: {e}")
        debug_print(f"未知错误详情: {traceback.format_exc()}")
        status[model_name] = {"completed": False}

    save_status(status)

def main():
    """主函数"""
    print("启动 run_all_models.py 脚本...")
    debug_print("进入 main() 函数")
    
    # 检查是否有命令行参数
    if len(sys.argv) > 1 and sys.argv[1] == "--test-mode":
        test_mode = True
        debug_print("通过命令行参数设置测试模式")
    else:
        try:
            # 尝试获取用户输入，如果失败则默认使用测试模式
            if sys.stdin.isatty():  # 检查是否在交互式环境
                debug_print("检测到交互式环境，请求用户输入")
                mode = input("请选择运行模式 (1: 执行, 2: 测试): ")
                test_mode = mode == '2'
            else:
                debug_print("检测到非交互式环境，默认使用测试模式")
                print("非交互式环境，默认使用测试模式")
                test_mode = True
        except Exception as e:
            debug_print(f"获取用户输入时出错: {e}")
            print(f"输入错误: {e}")
            test_mode = True  # 默认使用测试模式

    if test_mode:
        print("进入测试模式，将仅检查脚本有效性...")
    else:
        print("开始批量运行所有模型训练...")
    
    debug_print("加载运行状态")
    status = load_status()

    # 检查目录是否存在
    last_path = Path(LAST_MODELS_PATH)
    comparison_path = Path(COMPARISON_MODELS_PATH)
    
    debug_print(f"检查目录: LAST_MODELS_PATH={last_path}, 存在={last_path.exists()}")
    debug_print(f"检查目录: COMPARISON_MODELS_PATH={comparison_path}, 存在={comparison_path.exists()}")
    
    if not last_path.exists():
        print(f"错误: 目录 {LAST_MODELS_PATH} 不存在")
    if not comparison_path.exists():
        print(f"错误: 目录 {COMPARISON_MODELS_PATH} 不存在")
    
    # 运行 last 目录中的模型
    if last_path.exists():
        print("运行 last 目录中的模型...")
        try:
            for model_dir in last_path.iterdir():
                debug_print(f"检查 last 目录中的项目: {model_dir}, 是目录={model_dir.is_dir()}")
                if model_dir.is_dir():
                    train_script = model_dir / "src/train.py"
                    debug_print(f"检查训练脚本: {train_script}, 存在={train_script.exists()}")
                    if train_script.exists():
                        run_model(model_dir, status, test_mode)
        except Exception as e:
            debug_print(f"遍历 last 目录时出错: {e}\n{traceback.format_exc()}")
            print(f"遍历 last 目录时出错: {e}")

    # 运行 comparison 目录中的模型
    if comparison_path.exists():
        print("运行 comparison 目录中的模型...")
        try:
            for model_dir in comparison_path.iterdir():
                debug_print(f"检查 comparison 目录中的项目: {model_dir}, 是目录={model_dir.is_dir()}")
                if model_dir.is_dir():
                    train_script = model_dir / "src/train.py"
                    debug_print(f"检查训练脚本: {train_script}, 存在={train_script.exists()}")
                    if train_script.exists():
                        run_model(model_dir, status, test_mode)
        except Exception as e:
            debug_print(f"遍历 comparison 目录时出错: {e}\n{traceback.format_exc()}")
            print(f"遍历 comparison 目录时出错: {e}")

    # 显示依赖检查摘要
    missing_deps_summary = {}
    for model_name, model_status in status.items():
        if not model_status.get("completed", False) and "missing_deps" in model_status:
            missing_deps_summary[model_name] = model_status["missing_deps"]
    
    if missing_deps_summary:
        print("\n依赖检查摘要:")
        print("以下模型缺少依赖库:")
        for model_name, deps in missing_deps_summary.items():
            print(f"  - {model_name}: {', '.join(deps)}")
        print("\n您可以使用以下命令安装所有缺少的依赖:")
        all_deps = set()
        for deps in missing_deps_summary.values():
            all_deps.update(deps)
        print(f"pip install {' '.join(all_deps)}")
    
    print("所有模型训练完成！")

if __name__ == "__main__":
    try:
        print("开始执行 main() 函数...")
        print(f"Python 版本: {sys.version}")
        print(f"命令行参数: {sys.argv}")
        print(f"当前工作目录: {os.getcwd()}")
        main()
        print("main() 函数执行完成")
    except Exception as e:
        import traceback
        print(f"执行过程中出现错误: {e}")
        traceback.print_exc()