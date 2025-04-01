"""
模型加载模块 - 负责加载和管理不同版本的Faster R-CNN模型
"""
import torch
import torchvision
from torchvision.models.detection import FasterRCNN
from torchvision.models.detection.rpn import AnchorGenerator
from torchvision.ops import MultiScaleRoIAlign
import os
from .image_preprocessor import ImagePreprocessor

def load_model(model_type='balanced'):
    """加载指定类型的模型
    
    Args:
        model_type: 模型类型 ('lightweight', 'balanced', 'accurate')
    
    Returns:
        加载好的模型
    """
    from app import app
    
    # 检查模型路径是否存在
    model_path = app.config['MODEL_PATHS'].get(model_type)
    if not model_path or not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file not found: {model_path}")
    
    # 重建与训练时相同的自定义模型结构
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
        num_classes=2,
        rpn_anchor_generator=anchor_generator,
        box_roi_pool=roi_pooler,
        rpn_batch_size_per_image=256,
        box_batch_size_per_image=512,
    )
    
    # 加载检查点
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Loading model from {model_path} on device {device}")
    
    try:
        checkpoint = torch.load(model_path, map_location=device)
        
        # 处理不同格式的检查点
        if 'model_state_dict' in checkpoint:
            state_dict = checkpoint['model_state_dict']
        else:
            state_dict = checkpoint
        
        # 打印模型结构和权重键名用于调试
        print("Model structure keys:", model.state_dict().keys())
        print("Checkpoint keys:", state_dict.keys())
        
        # 尝试加载权重
        model.load_state_dict(state_dict, strict=False)
        model.eval()
        model.to(device)
        model.device = device
        
        print("Model loaded successfully")
        return model
    except Exception as e:
        print(f"Error loading model: {str(e)}")
        raise
    
    return model

class ColonyAnalyzer:
    """菌落分析器封装类"""
    def __init__(self, model):
        self.model = model
        self.preprocessor = ImagePreprocessor()
        
    def analyze(self, image_path, preprocess_methods=None, preprocess_params=None):
        """分析图片并返回菌落信息
        
        Args:
            image_path: 图片路径
            preprocess_methods: 预处理方法列表
            preprocess_params: 预处理参数字典
            
        Returns:
            包含菌落信息的字典
        """
        import cv2
        import numpy as np
        from PIL import Image
        import torchvision.transforms.functional as F
        
        try:
            # 1. 图片预处理
            img = Image.open(image_path).convert("RGB")
            if preprocess_methods:
                img_array = np.array(img)
                processed_array = self.preprocessor.process(
                    img_array, 
                    methods=preprocess_methods,
                    params=preprocess_params
                )
                img = Image.fromarray(processed_array)
            
            # 2. 转换为模型输入格式
            img_tensor = F.to_tensor(img)
            img_tensor = F.normalize(img_tensor, 
                                   mean=[0.485, 0.456, 0.406], 
                                   std=[0.229, 0.224, 0.225])
            
            # 3. 模型推理
            with torch.no_grad():
                predictions = self.model([img_tensor.to(self.model.device)])
            
            # 4. 处理结果
            boxes = predictions[0]['boxes'].cpu().numpy()
            scores = predictions[0]['scores'].cpu().numpy()
            
            # 过滤低置信度检测结果(阈值0.5)
            keep = scores > 0.5
            boxes = boxes[keep]
            scores = scores[keep]
            
            # 计算菌落大小(面积)
            sizes = [(box[2]-box[0])*(box[3]-box[1]) for box in boxes]
            
            # 确保所有NumPy数据转换为Python原生类型
            return {
                'status': 'success',
                'count': int(len(boxes)),
                'sizes': [float(size) for size in sizes],
                'boxes': [box.tolist() for box in boxes],
                'scores': [float(score) for score in scores]
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e)
            }
