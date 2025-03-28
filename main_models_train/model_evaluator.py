import torch
import torchvision  # 添加这行
import random
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

def get_model(num_classes=2):
    """重新创建模型架构"""
    backbone = torchvision.models.resnet50(weights="DEFAULT")
    backbone = torch.nn.Sequential(*(list(backbone.children())[:-2]))
    backbone.out_channels = 2048
    
    anchor_generator = AnchorGenerator(
        sizes=((32, 64, 128, 256, 512),),
        aspect_ratios=((0.5, 1.0, 1.5),)
    )
    
    roi_pooler = MultiScaleRoIAlign(  # 修改这里
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
    def __init__(self, valid_data_path, valid_anno_path, device='cuda'):
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
        model = get_model()
        
        # 加载检查点
        try:
            checkpoint = torch.load(model_path)
            model.load_state_dict(checkpoint['model_state_dict'])
            model.to(self.device)
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
                
                # 计时推理
                start_time = torch.cuda.Event(enable_timing=True)
                end_time = torch.cuda.Event(enable_timing=True)
                
                start_time.record()
                predictions = model([img])
                end_time.record()
                
                torch.cuda.synchronize()
                inference_time = start_time.elapsed_time(end_time)
                
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

def analyze_checkpoints(checkpoint_dir, valid_data_path, valid_anno_path, num_samples=10):
    """分析所有检查点"""
    evaluator = ModelEvaluator(valid_data_path, valid_anno_path)
    checkpoints = glob.glob(os.path.join(checkpoint_dir, 'faster_rcnn_colony*.pth'))
    
    results = []
    for checkpoint in sorted(checkpoints):
        if 'interrupted' in checkpoint:  # 跳过中断的检查点
            continue
            
        try:
            result = evaluator.evaluate_model(checkpoint, num_samples=num_samples)
            if result is not None:
                epoch = int(checkpoint.split('epoch')[-1].split('.')[0])
                result['epoch'] = epoch
                result['checkpoint'] = os.path.basename(checkpoint)
                results.append(result)
                
        except Exception as e:
            print(f"Error evaluating {checkpoint}: {str(e)}")
    
    return results