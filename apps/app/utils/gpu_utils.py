"""
GPU utilities for hardware acceleration
GPU硬件加速工具模块
"""
import logging
import torch

logger = logging.getLogger(__name__)

def check_gpu_available():
    """
    Check if CUDA GPU is available for acceleration
    检查CUDA GPU是否可用于加速
    
    Returns:
        bool: True if GPU is available, False otherwise
        如果GPU可用返回True，否则返回False
    """
    try:
        if torch.cuda.is_available():
            device_count = torch.cuda.device_count()
            device_name = torch.cuda.get_device_name(0)
            logger.info(f"Found {device_count} CUDA GPU(s)")
            logger.info(f"Using GPU: {device_name}")
            return True
        else:
            logger.info("No CUDA GPU available, using CPU")
            return False
    except Exception as e:
        logger.error(f"Error checking GPU availability: {e}")
        return False

def get_device():
    """
    Get the optimal computing device (GPU if available, otherwise CPU)
    获取最优计算设备(如果可用则使用GPU，否则使用CPU)
    
    Returns:
        torch.device: The computing device to use
        返回要使用的计算设备
    """
    try:
        if check_gpu_available():
            return torch.device("cuda")
        return torch.device("cpu")
    except Exception as e:
        logger.error(f"Error getting device: {e}")
        return torch.device("cpu")

def get_gpu_memory_info():
    """
    Get GPU memory usage information if GPU is available
    如果GPU可用，获取GPU内存使用信息
    
    Returns:
        dict: GPU memory information or None if not available
        返回GPU内存信息，如果不可用则返回None
    """
    try:
        if not check_gpu_available():
            return None
            
        gpu_memory = {
            "total": torch.cuda.get_device_properties(0).total_memory,
            "allocated": torch.cuda.memory_allocated(),
            "cached": torch.cuda.memory_reserved()
        }
        return gpu_memory
    except Exception as e:
        logger.error(f"Error getting GPU memory info: {e}")
        return None

def optimize_gpu_memory():
    """
    Optimize GPU memory usage by clearing cache and garbage collection
    通过清理缓存和垃圾回收优化GPU内存使用
    """
    try:
        if check_gpu_available():
            torch.cuda.empty_cache()
            torch.cuda.memory_allocated()
            logger.info("GPU memory optimized")
    except Exception as e:
        logger.error(f"Error optimizing GPU memory: {e}")

# Optional: Add more GPU related utility functions as needed
# 可选：根据需要添加更多GPU相关的工具函数
