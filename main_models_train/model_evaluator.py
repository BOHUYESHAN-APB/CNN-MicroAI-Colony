import time
import torch
import torchvision
import random
import importlib.util
from torchvision.transforms import functional as F
from PIL import Image
import os
import json
import numpy as np
from tqdm import tqdm
import glob
from datetime import datetime
from torchvision.models.detection import FasterRCNN
from torchvision.models.detection.rpn import AnchorGenerator
from torchvision.ops import MultiScaleRoIAlign  # 添加这行

def get_model(model_path, num_classes=2):
    """根据模型路径创建对应的模型架构"""
    if "checkpoint_epoch_31" in model_path:
        # 使用ColonyDetector架构
        import sys
        # 添加src目录到Python路径
        src_dir = os.path.join('d:/-Users-/Documents/GitHub/CNN-MicroAI-Colony', 
                             'faster_rcnn_resnet50', 'src')
        if src_dir not in sys.path:
            sys.path.insert(0, src_dir)
        from models.colony_detector import ColonyDetector
        model = ColonyDetector(num_classes=num_classes, pretrained=False)
    else:
        # 使用标准FasterRCNN架构
        backbone = torchvision.models.resnet50(weights=None)
        backbone = torch.nn.Sequential(*(list(backbone.children())[:-2]))
        backbone.out_channels = 2048
        
        anchor_generator = AnchorGenerator(
            sizes=((32, 64, 128, 256, 512),),
            aspect_ratios=((0.5, 1.0, 1.5),)
        )
        
        roi_pooler = MultiScaleRoIAlign(
            featmap_names=['0'],
            output_size=7,
            sampling_ratio=2
        )
        
        model = FasterRCNN(
            backbone,
            num_classes=num_classes,
            rpn_anchor_generator=anchor_generator,
            box_roi_pool=roi_pooler,
            rpn_batch_size_per_image=256,
            box_batch_size_per_image=512,
        )
    
    return model

class ModelEvaluator:
    def __init__(self, valid_data_path, valid_anno_path, device='cpu'):
        # 狂暴模式设置
        torch.set_num_threads(os.cpu_count())  # 使用所有CPU核心
        torch.backends.mkl.enabled = True  # 启用MKL优化
        self.device = device
        self.valid_data_path = valid_data_path
        
        # 加载验证集标注
        with open(valid_anno_path, 'r') as f:
            self.annotations = json.load(f)
            
        # 构建图像索引
        self.image_ids = [img['id'] for img in self.annotations['images']]
    
    def prepare_image(self, image_path):
        """准备单张图像"""
        img = Image.open(image_path).convert("RGB")
        img = F.to_tensor(img)
        img = F.normalize(img, mean=[0.485, 0.456, 0.406], 
                         std=[0.229, 0.224, 0.225])
        return img
    
    def evaluate_model(self, model_path, num_samples=10, seed=None):
        """评估单个模型"""
        if seed is not None:
            random.seed(seed)
            
        # 创建新模型实例
        model = get_model(model_path)
        
        # 加载检查点
        try:
            # 强制使用CPU加载模型
            checkpoint = torch.load(model_path, map_location=torch.device('cpu'))
            model.load_state_dict(checkpoint['model_state_dict'])
            model.eval()
            model.eval()
            
            train_loss = checkpoint['stats'].get('Train Loss', {}).get('current', float('inf'))
        except Exception as e:
            print(f"Error loading model {model_path}: {str(e)}")
            return None
        
        # 随机采样图像
        sample_ids = random.sample(self.image_ids, min(num_samples, len(self.image_ids)))
        
        results = {
            'detection_scores': [],
            'inference_times': [],
            'num_detections': [],
            'confidence_scores': []
        }
        
        with torch.no_grad():
            for img_id in tqdm(sample_ids, desc=f"Evaluating {os.path.basename(model_path)}"):
                img_info = next(img for img in self.annotations['images'] if img['id'] == img_id)
                img_path = os.path.join(self.valid_data_path, img_info['file_name'])
                
                # 准备输入
                img = self.prepare_image(img_path)
                img = img.to(self.device)
                
                # CPU计时推理
                start_time = time.time()
                predictions = model([img])
                inference_time = (time.time() - start_time) * 1000  # 转换为毫秒
                
                # 收集结果
                pred = predictions[0]
                results['detection_scores'].append(pred['scores'].mean().item() if len(pred['scores']) > 0 else 0)
                results['inference_times'].append(inference_time)
                results['num_detections'].append(len(pred['boxes']))
                results['confidence_scores'].append(pred['scores'].max().item() if len(pred['scores']) > 0 else 0)
        
        # 计算统计信息
        stats = {
            'avg_detection_score': np.mean(results['detection_scores']),
            'avg_inference_time': np.mean(results['inference_times']),
            'avg_num_detections': np.mean(results['num_detections']),
            'avg_confidence': np.mean(results['confidence_scores']),
            'std_detection_score': np.std(results['detection_scores']),
            'std_inference_time': np.std(results['inference_times'])
        }
        
        return {
            'stats': stats,
            'train_loss': train_loss
        }

import argparse

def evaluate_specified_models(model_paths, test_dir, num_samples=10):
    """评估指定的多个模型"""
    # 创建临时标注文件结构(test_dir下需要有图片文件)
    annotations = {
        'images': [],
        'annotations': []
    }
    
    # 添加测试图片路径
    img_files = [f for f in os.listdir(test_dir) 
                if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    for i, img_file in enumerate(img_files):
        annotations['images'].append({
            'id': i,
            'file_name': img_file
        })
    
    # 保存临时标注文件
    temp_anno = os.path.join(test_dir, 'temp_annotations.json')
    with open(temp_anno, 'w') as f:
        json.dump(annotations, f)
    
    # 评估每个模型
    evaluator = ModelEvaluator(test_dir, temp_anno)
    
    results = {}
    for model_path in model_paths:
        model_name = os.path.basename(model_path)
        try:
            result = evaluator.evaluate_model(
                model_path,
                num_samples=min(num_samples, len(img_files))
            )
            if result:
                results[model_name] = {
                    'average_inference_time_ms': result['stats']['avg_inference_time'],
                    'average_confidence': result['stats']['avg_confidence'],
                    'average_detections': result['stats']['avg_num_detections']
                }
        except Exception as e:
            print(f"Error evaluating {model_name}: {str(e)}")
    
    # 清理临时文件
    os.remove(temp_anno)
    
    return results

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Evaluate Faster-RCNN models')
    parser.add_argument('--models', type=str, required=True,
                      help='Comma-separated paths to model checkpoints')
    parser.add_argument('--test_dir', type=str, required=True,
                      help='Directory containing test images')
    parser.add_argument('--num_samples', type=int, default=5,
                      help='Number of test samples to evaluate')
    
    args = parser.parse_args()
    
    # 解析模型路径
    model_paths = [p.strip() for p in args.models.split(',')]
    results = evaluate_specified_models(
        model_paths,
        args.test_dir,
        args.num_samples
    )
    
    # 打印结果表格
    print("\nModel Evaluation Results:")
    print("{:<40} {:<20} {:<20} {:<20}".format(
        "Model", "Avg Time(ms)", "Avg Confidence", "Avg Detections"))
    for model, res in results.items():
        print("{:<40} {:<20.2f} {:<20.2f} {:<20.2f}".format(
            model, 
            res['average_inference_time_ms'],
            res['average_confidence'],
            res['average_detections']))
