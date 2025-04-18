import cpuinfo
import platform
import subprocess
import torch

def get_cpu_info():
    info = cpuinfo.get_cpu_info()
    print("\nCPU Information:")
    print(f"Brand: {info['brand_raw']}")
    print(f"Architecture: {info['arch']}")
    print(f"Cores: {info['count']} ({platform.processor()})")

def get_torch_devices():
    print("\nPyTorch Devices:")
    print(f"PyTorch version: {torch.__version__}")
    print(f"Available devices: {'cuda' if torch.cuda.is_available() else 'cpu'}")
    
def get_intel_gpu_info():
    print("\nIntel GPU/NPU Information:")
    try:
        import intel_extension_for_pytorch as ipex
        print("Intel Extension for PyTorch is available")
        print(f"IPEX version: {ipex.__version__}")
    except ImportError:
        print("Intel Extension for PyTorch is not installed")

if __name__ == "__main__":
    get_cpu_info()
    get_torch_devices()
    get_intel_gpu_info()
