"""
Training performance estimation tool
训练性能评估工具
"""
import os
import time
import platform
import psutil
import torch
import numpy as np
from pathlib import Path

class PerformanceEstimator:
    """
    Estimate training time and manage device selection
    评估训练时间并管理设备选择
    """
    def __init__(self):
        self.device = self._select_device()
        self.system_info = self._get_system_info()
        
    def _select_device(self) -> torch.device:
        """
        Select the best available device for training
        选择最佳可用训练设备
        """
        if torch.cuda.is_available():
            # Get GPU memory and compute capability
            # 获取GPU内存和计算能力
            gpu_properties = []
            for i in range(torch.cuda.device_count()):
                props = torch.cuda.get_device_properties(i)
                total_memory = props.total_memory / 1024**3  # Convert to GB
                gpu_properties.append({
                    'index': i,
                    'name': props.name,
                    'memory': total_memory,
                    'compute_capability': f"{props.major}.{props.minor}",
                    'multi_processor_count': props.multi_processor_count
                })
                
            # Select GPU with most memory and highest compute capability
            # 选择内存最大且计算能力最强的GPU
            best_gpu = max(gpu_properties, 
                          key=lambda x: (x['memory'], float(x['compute_capability'])))
            
            print(f"使用GPU: {best_gpu['name']}")
            print(f"显存大小: {best_gpu['memory']:.1f}GB")
            print(f"计算能力: {best_gpu['compute_capability']}")
            
            return torch.device(f"cuda:{best_gpu['index']}")
        else:
            print("未检测到GPU，使用CPU训练")
            return torch.device('cpu')
            
    def _get_system_info(self) -> dict:
        """
        Get system information
        获取系统信息
        """
        cpu_count = psutil.cpu_count(logical=False)
        cpu_freq = psutil.cpu_freq()
        memory = psutil.virtual_memory()
        
        return {
            'platform': platform.platform(),
            'processor': platform.processor(),
            'cpu_count': cpu_count,
            'cpu_freq': cpu_freq.max if cpu_freq else "Unknown",
            'memory_total': memory.total / (1024**3),  # GB
            'memory_available': memory.available / (1024**3),  # GB
            'device': self.device
        }
        
    def estimate_training_time(self, 
                             dataset_path: str, 
                             batch_size: int,
                             epochs: int,
                             image_size: tuple) -> dict:
        """
        Estimate training time based on system performance and dataset size
        基于系统性能和数据集大小估算训练时间

        Args:
            dataset_path: Path to the dataset
                        数据集路径
            batch_size: Training batch size
                       训练批次大小
            epochs: Number of training epochs
                   训练轮数
            image_size: Input image size (height, width)
                       输入图像尺寸（高度，宽度）
        """
        # Count number of images
        # 统计图像数量
        dataset_path = Path(dataset_path)
        n_images = sum(1 for _ in dataset_path.rglob('*.jpg'))
        n_images += sum(1 for _ in dataset_path.rglob('*.jpeg'))
        n_images += sum(1 for _ in dataset_path.rglob('*.png'))
        
        # Estimate memory requirements
        # 估算内存需求
        image_memory = np.prod(image_size) * 3 * 4  # RGB float32
        batch_memory = image_memory * batch_size / (1024**3)  # GB
        
        # Estimate processing speed (images/second)
        # 估算处理速度（图像/秒）
        if self.device.type == 'cuda':
            # GPU estimation based on compute capability and memory
            # 基于计算能力和内存的GPU估算
            props = torch.cuda.get_device_properties(self.device)
            compute_power = props.multi_processor_count * (float(f"{props.major}.{props.minor}"))
            base_speed = compute_power * 5  # Empirical factor
            estimated_speed = min(base_speed, props.total_memory / (batch_memory * 1024**3))
        else:
            # CPU estimation based on cores and frequency
            # 基于核心数和频率的CPU估算
            cpu_power = psutil.cpu_count(logical=False) * (psutil.cpu_freq().max / 2000 if psutil.cpu_freq() else 1)
            estimated_speed = cpu_power * 2  # Empirical factor
            
        # Calculate total time
        # 计算总时间
        iterations_per_epoch = n_images / batch_size
        total_iterations = iterations_per_epoch * epochs
        estimated_hours = total_iterations / (estimated_speed * 3600)
        
        # Memory requirement check
        # 内存需求检查
        if self.device.type == 'cuda':
            available_memory = torch.cuda.get_device_properties(self.device).total_memory / (1024**3)
            memory_warning = batch_memory > available_memory * 0.8
        else:
            available_memory = psutil.virtual_memory().available / (1024**3)
            memory_warning = batch_memory > available_memory * 0.5
            
        return {
            'device': self.device.type,
            'dataset_size': n_images,
            'batch_memory_gb': batch_memory,
            'total_iterations': total_iterations,
            'estimated_hours': estimated_hours,
            'memory_warning': memory_warning,
            'estimated_speed': estimated_speed,
            'system_info': self.system_info
        }
        
    def print_estimate_report(self, estimate_results: dict):
        """
        Print a formatted estimation report
        打印格式化的估算报告
        """
        print("\n训练时间估算报告")
        print("="*50)
        print(f"设备类型: {estimate_results['device'].upper()}")
        print(f"数据集大小: {estimate_results['dataset_size']} 图像")
        print(f"每批次内存需求: {estimate_results['batch_memory_gb']:.2f}GB")
        print(f"总训练迭代次数: {estimate_results['total_iterations']:.0f}")
        print(f"预计训练时间: {estimate_results['estimated_hours']:.1f}小时")
        print(f"预计处理速度: {estimate_results['estimated_speed']:.1f}图像/秒")
        
        if estimate_results['memory_warning']:
            print("\n⚠️ 警告: 批次大小可能导致内存不足，建议减小批次大小")
            
        print("\n系统信息:")
        print(f"平台: {estimate_results['system_info']['platform']}")
        print(f"处理器: {estimate_results['system_info']['processor']}")
        print(f"CPU核心数: {estimate_results['system_info']['cpu_count']}")
        print(f"CPU频率: {estimate_results['system_info']['cpu_freq']}MHz")
        print(f"系统内存: {estimate_results['system_info']['memory_total']:.1f}GB")
        print(f"可用内存: {estimate_results['system_info']['memory_available']:.1f}GB")

if __name__ == "__main__":
    # Example usage
    # 使用示例
    estimator = PerformanceEstimator()
    estimate = estimator.estimate_training_time(
        dataset_path="main_models_train_server/train",
        batch_size=4,
        epochs=12,
        image_size=(1280, 1280)
    )
    estimator.print_estimate_report(estimate)
