import os
import sys
import torch
import psutil
import time
import json
import numpy as np
import traceback

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

# 现在导入ColonyDetector
try:
    from faster_rcnn_resnet50.src.models.colony_detector import ColonyDetector
    print("成功导入ColonyDetector")
except Exception as e:
    print(f"导入ColonyDetector失败: {e}")
    print("Python路径:", sys.path)
    traceback.print_exc()
    sys.exit(1)

def get_memory_usage():
    """获取当前进程的内存使用情况"""
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()
    return {
        'rss': memory_info.rss / 1024 / 1024,  # MB
        'vms': memory_info.vms / 1024 / 1024   # MB
    }

def get_gpu_memory():
    """获取GPU显存使用情况"""
    if torch.cuda.is_available():
        return {
            'allocated': torch.cuda.memory_allocated() / 1024 / 1024,  # MB
            'cached': torch.cuda.memory_reserved() / 1024 / 1024       # MB
        }
    return None

class MemoryTester:
    def __init__(self):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        print(f"使用设备: {self.device}\n")
        
    def load_and_test(self, model_path):
        """加载模型并测试内存占用"""
        print(f"\n开始测试模型: {model_path}")
        
        # 记录初始内存状态
        initial_mem = get_memory_usage()
        initial_gpu = get_gpu_memory()
        
        print("\n初始状态:")
        print(f"CPU内存: RSS={initial_mem['rss']:.2f}MB, VMS={initial_mem['vms']:.2f}MB")
        if initial_gpu:
            print(f"GPU显存: 已分配={initial_gpu['allocated']:.2f}MB, 缓存={initial_gpu['cached']:.2f}MB")
            
        try:
            # 加载模型
            print("\n加载模型...")
            
            # 创建模型实例
            model = ColonyDetector()
            
            # 加载权重
            print(f"加载权重文件: {model_path}")
            try:
                # 先尝试安全加载
                import torch.serialization
                with torch.serialization.safe_globals(['getattr']):
                    model_data = torch.load(model_path, map_location='cpu', weights_only=False)
                    print("使用安全模式加载成功")
            except Exception as e1:
                print(f"安全模式加载失败: {str(e1)}")
                try:
                    # 如果失败，尝试直接加载
                    print("尝试直接加载...")
                    model_data = torch.load(model_path, map_location='cpu', pickle_module=None, weights_only=False)
                    print("直接加载成功")
                except Exception as e2:
                    print(f"直接加载也失败了: {str(e2)}")
                    raise
            
            print(f"权重文件加载成功，大小: {os.path.getsize(model_path) / (1024*1024):.2f}MB")
            model.load_state_dict(model_data['model_state_dict'])
            print("权重加载成功")
            
            # 移动到相应设备并设置为评估模式
            model = model.to(self.device)
            model.eval()
            print(f"模型已移动到{self.device}并设置为评估模式")
            
            # 记录加载后的内存状态
            loaded_mem = get_memory_usage()
            loaded_gpu = get_gpu_memory()
            
            print("\n加载后状态:")
            print(f"CPU内存: RSS={loaded_mem['rss']:.2f}MB, VMS={loaded_mem['vms']:.2f}MB")
            if loaded_gpu:
                print(f"GPU显存: 已分配={loaded_gpu['allocated']:.2f}MB, 缓存={loaded_gpu['cached']:.2f}MB")
            
            # 计算差值
            mem_diff = {
                'rss': loaded_mem['rss'] - initial_mem['rss'],
                'vms': loaded_mem['vms'] - initial_mem['vms']
            }
            
            print("\n内存增加:")
            print(f"RSS增加: {mem_diff['rss']:.2f}MB")
            print(f"VMS增加: {mem_diff['vms']:.2f}MB")
            
            if initial_gpu and loaded_gpu:
                gpu_diff = {
                    'allocated': loaded_gpu['allocated'] - initial_gpu['allocated'],
                    'cached': loaded_gpu['cached'] - initial_gpu['cached']
                }
                print(f"GPU显存增加: 已分配={gpu_diff['allocated']:.2f}MB, 缓存={gpu_diff['cached']:.2f}MB")
            
            # 进行一次推理以确保模型正常工作
            dummy_input = torch.randn(1, 3, 800, 800).to(self.device)
            print("\n执行测试推理...")
            with torch.no_grad():
                _ = model(dummy_input)
            print("测试推理成功")
            
            return {
                'model_size': os.path.getsize(model_path) / 1024 / 1024,  # MB
                'initial_memory': initial_mem,
                'loaded_memory': loaded_mem,
                'memory_increase': mem_diff,
                'initial_gpu': initial_gpu,
                'loaded_gpu': loaded_gpu,
                'gpu_increase': gpu_diff if (initial_gpu and loaded_gpu) else None
            }
            
        except Exception as e:
            print(f"测试失败: {str(e)}")
            traceback.print_exc()
            return None

def main():
    # 测试完整版模型
    model_path = "D:/train/faster_rcnn_colony_epoch12.pth"
    
    print(f"项目根目录: {project_root}")
    print(f"模型路径: {model_path}")
    
    tester = MemoryTester()
    
    # 检查文件是否存在
    if not os.path.exists(model_path):
        print(f"错误: 模型文件不存在: {model_path}")
        return
        
    print(f"\n模型大小: {os.path.getsize(model_path) / (1024*1024):.2f} MB")
    
    # 测试模型
    print("\n=== 测试完整版模型性能 ===")
    result = tester.load_and_test(model_path)
    
    # 保存结果
    results = {'model': result}
    with open('memory_test_results_full.json', 'w') as f:
        json.dump(results, f, indent=4)
    
    print("\n测试结果已保存到 memory_test_results_full.json")

if __name__ == "__main__":
    main()
