import sys
import os
import time
import json
import numpy as np
import torch
import traceback
from openvino.runtime import Core, serialize
import logging

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)
print(f"Adding root directory to sys.path: {project_root}")

# 显示 Python 版本
print(f"Python version: {sys.version}")
print(f"Current working directory: {os.getcwd()}")

# 显示 OpenVINO 版本
from openvino import runtime as ov
print(f"OpenVINO version: {ov.__version__}")

# 显示 PyTorch 版本
print(f"PyTorch version: {torch.__version__}")

# 尝试导入 ColonyDetector
try:
    print("Trying to import ColonyDetector...")
    from faster_rcnn_resnet50.src.models.colony_detector import ColonyDetector
    print("Successfully imported ColonyDetector")
except Exception as e:
    print(f"Failed to import ColonyDetector: {e}")
    traceback.print_exc()
    sys.exit(1)

class NPUTester:
    def __init__(self):
        """初始化 NPU 测试器"""
        self.core = Core()
        print("NPU测试器初始化成功\n")
        
    def convert_to_openvino(self, model_path):
        """将 PyTorch 模型转换为 OpenVINO 格式"""
        print("\n开始模型转换...")
        try:
            print(f"开始转换模型: {model_path}")
            input_shape = [1, 3, 800, 800]
            print(f"输入形状: {input_shape}")
            
            # 加载 PyTorch 模型
            print("正在加载PyTorch模型...")
            checkpoint = torch.load(model_path, map_location='cpu')
            print(f"模型加载成功，checkpoint键: {checkpoint.keys()}")
            
            # 初始化模型
            print("初始化ColonyDetector...")
            model = ColonyDetector()
            
            # 加载权重
            print("加载模型权重...")
            model.load_state_dict(checkpoint['model_state_dict'])
            print("模型权重加载成功")
            
            # 设置为评估模式
            model.eval()
            print("模型设置为评估模式")
            
            # 转换为 ONNX
            onnx_path = model_path.replace('.pth', '.onnx')
            print(f"准备转换为ONNX格式: {onnx_path}")
            dummy_input = torch.randn(input_shape)
            torch.onnx.export(model, dummy_input, onnx_path, 
                            input_names=['input'],
                            output_names=['output'],
                            opset_version=11,
                            do_constant_folding=True,
                            export_params=True,
                            training=torch.onnx.TrainingMode.EVAL)
            print("ONNX转换成功，转换为OpenVINO格式...")
            
            # 转换为 OpenVINO IR
            output_path = model_path.replace('.pth', '_openvino.xml')
            
            # 直接读取ONNX模型
            ov_model = self.core.read_model(onnx_path)
            
            # 保存为OpenVINO格式
            serialize(ov_model, output_path)
            print(f"OpenVINO模型保存成功: {output_path}")
            
            # 删除临时 ONNX 文件
            os.remove(onnx_path)
            print("已清理临时ONNX文件\n")
            
            return output_path
            
        except Exception as e:
            print(f"模型转换失败: {str(e)}")
            traceback.print_exc()
            raise

    def load_model(self, model_path, device="CPU"):
        """加载模型到指定设备"""
        try:
            print(f"加载模型: {model_path} 到设备: {device}")
            model = self.core.read_model(model_path)
            
            # NPU特定配置
            if device == "NPU":
                config = {
                    "PERFORMANCE_HINT": "LATENCY",
                    "INFERENCE_PRECISION_HINT": "FP16",
                    "ENABLE_PERFORMANCE_COUNTERS": "YES"
                }
            else:
                config = {}
                
            compiled_model = self.core.compile_model(model, device, config)
            print("模型加载成功")
            return compiled_model
        except Exception as e:
            print(f"模型加载失败: {str(e)}")
            traceback.print_exc()
            raise

    def benchmark(self, model_path, device, iterations=100):
        """对模型进行基准测试"""
        print(f"\n开始对设备 {device} 进行基准测试")
        print(f"模型: {model_path}")
        print(f"迭代次数: {iterations}")
        
        try:
            # 加载并编译模型
            model = self.load_model(model_path, device)
            
            # 创建随机输入数据
            input_shape = [1, 3, 800, 800]
            input_data = np.random.random(input_shape).astype(np.float32)
            
            # 预热
            print("开始预热...")
            for i in range(5):
                model(input_data)
                print(f"预热迭代 {i+1}/5 完成")
            print()
            
            # 性能测试
            print(f"开始性能测试，迭代次数：{iterations}")
            latencies = []
            
            for i in range(iterations):
                if i % 10 == 0:
                    print(f"进度: {i}/{iterations}")
                
                start_time = time.time()
                model(input_data)
                latency = (time.time() - start_time) * 1000  # 转换为毫秒
                latencies.append(latency)
            
            # 计算统计数据
            latencies = np.array(latencies)
            mean_latency = np.mean(latencies)
            std_latency = np.std(latencies)
            min_latency = np.min(latencies)
            max_latency = np.max(latencies)
            
            print("\n测试结果:")
            print(f"平均延迟: {mean_latency:.2f} ms")
            print(f"标准差: {std_latency:.2f} ms")
            print(f"最小延迟: {min_latency:.2f} ms")
            print(f"最大延迟: {max_latency:.2f} ms")
            print(f"平均推理时间: {mean_latency:.2f}±{std_latency:.2f} ms\n")
            
            return {
                "device": device,
                "mean_latency": float(mean_latency),
                "std_latency": float(std_latency),
                "min_latency": float(min_latency),
                "max_latency": float(max_latency)
            }
            
        except Exception as e:
            print(f"基准测试失败: {str(e)}")
            traceback.print_exc()
            raise

    def test_model(self, model_path):
        """测试模型在不同设备上的性能"""
        print("开始性能比较测试")
        print(f"模型路径: {model_path}")
        
        # 获取输入形状
        input_shape = [1, 3, 800, 800]
        print(f"输入形状: {input_shape}")
        
        # 检测可用设备
        available_devices = self.core.available_devices
        print(f"检测到的设备: {available_devices}")
        
        # 显示设备信息
        for device in available_devices:
            device_info = self.core.get_property(device, "FULL_DEVICE_NAME")
            print(f"设备 {device} 信息: {device_info}")
        
        # 转换模型为 OpenVINO 格式
        openvino_model = self.convert_to_openvino(model_path)
        
        results = {}
        for device in available_devices:
            try:
                result = self.benchmark(openvino_model, device)
                results[device] = result
            except Exception as e:
                print(f"设备 {device} 测试失败: {str(e)}")
                results[device] = {"error": str(e)}
        
        # 保存结果
        with open("npu_test_results.json", "w") as f:
            json.dump(results, f, indent=4)
        print("结果已保存到: npu_test_results.json")

def main():
    """主函数"""
    checkpoint_path = os.path.join(project_root, "faster_rcnn_resnet50", "checkpoints", "checkpoint_epoch_31.pth")
    print(f"\n开始测试轻量版模型: {checkpoint_path}")
    
    tester = NPUTester()
    tester.test_model(checkpoint_path)

if __name__ == "__main__":
    main()
