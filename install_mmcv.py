import os
import torch
import subprocess
import sys
import argparse

def get_cuda_version():
    """获取 CUDA 版本"""
    if torch.cuda.is_available():
        return torch.version.cuda
    return None

def get_pytorch_version():
    """获取 PyTorch 版本"""
    return torch.__version__.split('+')[0]

def install_mmcv(cuda_version=None, torch_version=None):
    """安装与当前环境匹配的 mmcv-full"""
    print("开始安装 mmcv-full...")
    
    # 卸载现有的 mmcv
    subprocess.check_call([sys.executable, "-m", "pip", "uninstall", "-y", "mmcv", "mmcv-full"])
    
    # 如果未指定版本，则自动检测
    if cuda_version is None:
        cuda_version = get_cuda_version()
    if torch_version is None:
        torch_version = get_pytorch_version()
    
    print(f"使用 PyTorch 版本: {torch_version}")
    print(f"使用 CUDA 版本: {cuda_version}")
    
    # 构建安装命令
    if cuda_version:
        # 处理CUDA 12.0等较新版本 - 回退到11.8作为兼容版本
        if cuda_version.startswith("12."):
            print(f"CUDA {cuda_version} 可能没有官方预编译包，尝试使用CUDA 11.8兼容包")
            cuda_suffix = "cu118"
        else:
            # 将 CUDA 版本格式化为 mmcv 需要的格式 (例如 10.2 -> cu102)
            cuda_suffix = 'cu' + ''.join(cuda_version.split('.')[:2])
        
        torch_version_short = '.'.join(torch_version.split('.')[:2])
        
        install_cmd = f"pip install mmcv-full -f https://download.openmmlab.com/mmcv/dist/{cuda_suffix}/torch{torch_version_short}/index.html"
    else:
        # CPU 版本
        torch_version_short = '.'.join(torch_version.split('.')[:2])
        install_cmd = f"pip install mmcv-full -f https://download.openmmlab.com/mmcv/dist/cpu/torch{torch_version_short}/index.html"
    
    print(f"执行安装命令: {install_cmd}")
    result = os.system(install_cmd)
    
    if result != 0:
        print("\n安装失败！尝试以下替代方案：")
        print("1. 访问 https://mmcv.readthedocs.io/en/latest/get_started/installation.html 查看官方安装指南")
        print("2. 尝试手动编译安装: pip install mmcv-full")
        print("3. 尝试使用旧版本 MMCV: pip install mmcv-full==1.5.0")
    else:
        print("安装完成，请尝试重新运行您的程序")

def check_and_prepare_config():
    """检查并准备配置文件"""
    try:
        from config_finder import check_for_configs
        config_path = check_for_configs()
        print(f"配置文件就绪: {config_path}")
    except ImportError:
        print("未找到config_finder.py，跳过配置检查")
    except Exception as e:
        print(f"检查配置时出错: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='安装与环境匹配的MMCV')
    parser.add_argument('--cuda', type=str, help='手动指定CUDA版本，如11.8、12.0等')
    parser.add_argument('--torch', type=str, help='手动指定PyTorch版本，如2.0.1')
    parser.add_argument('--config', action='store_true', help='检查并准备配置文件')
    args = parser.parse_args()
    
    install_mmcv(args.cuda, args.torch)
    
    if args.config:
        check_and_prepare_config()
