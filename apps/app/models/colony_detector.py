"""
Colony detection model implementation
菌落检测模型实现
"""
import os
import cv2
import torch
import numpy as np
from torchvision.models.detection import fasterrcnn_resnet50_fpn
from torchvision.transforms import functional as F
import logging

logger = logging.getLogger(__name__)

class ColonyDetector:
    """Colony detection model wrapper"""
    
    def __init__(self, model_type='fasterrcnn'):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model = None
        self.model_type = model_type
        # 可配置参数
        self.confidence_threshold = 0.2
        self.min_size = 600
        self.max_size = 1000
        self.rpn_pre_nms_top_n = 2000
        self.rpn_post_nms_top_n = 1000
        self.nms_thresh = 0.2
        self.max_detections = 500
        self.aspect_ratio_range = (0.7, 1.3)
        self.min_area_ratio = 0.0001
        self.max_area_ratio = 0.01
        self.overlap_threshold = 0.3
        
        # 模型路径配置
        self.model_paths = {
            'fasterrcnn': 'faster_rcnn_resnet50/checkpoints/checkpoint_epoch_31.pth',
            'yolov11': 'yolov11/checkpoints/best.pt'
        }
        self.initialized = False
        
    def initialize(self):
        """Initialize model and load weights"""
        try:
            logger.info(f"Initializing model on device: {self.device}")
            
            # 创建基础模型（不加载预训练权重）
            self.model = fasterrcnn_resnet50_fpn(
                pretrained=False,
                weights=None,
                min_size=600,  # 增加最小尺寸以提高小目标检测
                max_size=1000,
                box_score_thresh=0.2,  # 降低分数阈值
                rpn_pre_nms_top_n_test=2000,  # 增加RPN候选框数量
                rpn_post_nms_top_n_test=1000,
                box_nms_thresh=0.2,  # 降低NMS阈值以减少重叠抑制
                box_detections_per_img=500  # 增加每张图片的最大检测数
            )
            
            # 修改分类器以支持二分类
            in_features = self.model.roi_heads.box_predictor.cls_score.in_features
            self.model.roi_heads.box_predictor.cls_score = torch.nn.Linear(in_features, 2)
            self.model.roi_heads.box_predictor.bbox_pred = torch.nn.Linear(in_features, 4 * 2)
            
            # 根据模型类型加载对应权重
            model_path = self.model_paths.get(self.model_type)
            if not model_path:
                logger.error(f"Unsupported model type: {self.model_type}")
                return False
                
            if os.path.exists(model_path):
                # 加载检查点
                checkpoint = torch.load(model_path, map_location=self.device)
                
                # 处理权重文件中的键名，移除"model."前缀
                state_dict = checkpoint['model_state_dict']
                new_state_dict = {}
                for key, value in state_dict.items():
                    if key.startswith('model.'):
                        new_key = key[6:]  # 移除"model."前缀
                    else:
                        new_key = key
                    new_state_dict[new_key] = value
                
                # 加载修改后的权重并设置为评估模式
                try:
                    self.model.to(self.device)
                    self.model.load_state_dict(new_state_dict)
                    self.model.eval()  # 确保在加载权重后设置为评估模式
                    logger.info(f"Successfully loaded {self.model_type} checkpoint from {model_path}")
                    self.initialized = True  # 只在成功加载后设置为已初始化
                    logger.info("Model initialized successfully with modified head")
                    return True
                except Exception as e:
                    logger.error(f"Error loading state dict: {e}")
                    return False
            else:
                logger.error(f"Checkpoint file not found at {self.model_path}")
                return False
            
        except Exception as e:
            logger.error(f"Error initializing model: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
            
    def preprocess_image(self, image):
        """Preprocess image for model input"""
        # BGR转RGB
        if len(image.shape) == 2:
            image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
        elif image.shape[2] == 3:
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
        # 保存原始尺寸
        original_size = image.shape[:2]
        
        # 图像预处理
        image = image.astype(np.float32) / 255.0
        
        # 应用图像增强
        image = cv2.GaussianBlur(image, (3, 3), 0)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        image = cv2.cvtColor(image, cv2.COLOR_RGB2LAB)
        image[:,:,0] = clahe.apply(np.uint8(image[:,:,0] * 255)) / 255.0
        image = cv2.cvtColor(image, cv2.COLOR_LAB2RGB)
        
        # 对比度增强
        image = np.clip(image * 1.2, 0, 1)
        
        # 转为tensor并标准化
        image = F.to_tensor(image)
        image = F.normalize(image, mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        
        return image, original_size
        
    def detect_colonies(self, image):
        """Detect colonies in image"""
        if not self.initialized:
            if not self.initialize():
                return None
                
        try:
            # 预处理图像
            input_tensor, original_size = self.preprocess_image(image)
            input_tensor = input_tensor.unsqueeze(0).to(self.device)
            
            # 运行推理
            with torch.no_grad():
                prediction = self.model(input_tensor)[0]
                
            # 提取结果
            boxes = prediction['boxes'].cpu().numpy()
            scores = prediction['scores'].cpu().numpy()
            labels = prediction['labels'].cpu().numpy()
            
            # 应用后处理
            filtered_indices = []
            for i, (box, score) in enumerate(zip(boxes, scores)):
                if score < self.confidence_threshold:
                    continue
                    
                # 基于形状的过滤
                width = box[2] - box[0]
                height = box[3] - box[1]
                aspect_ratio = width / height
                if not (0.7 < aspect_ratio < 1.3):  # 更严格的圆形条件
                    continue
                    
                # 基于大小的过滤
                area = width * height
                min_area = (original_size[0] * original_size[1]) * 0.0001  # 最小面积
                max_area = (original_size[0] * original_size[1]) * 0.01   # 最大面积
                if not (min_area < area < max_area):
                    continue
                    
                # 检查重叠
                has_overlap = False
                for j in filtered_indices:
                    other_box = boxes[j]
                    # 计算IoU
                    intersection = self._calculate_intersection(box, other_box)
                    if intersection > 0.3:  # 允许30%重叠
                        has_overlap = True
                        break
                if has_overlap:
                    continue
                    
                filtered_indices.append(i)
            
            # 过滤结果
            boxes = boxes[filtered_indices]
            scores = scores[filtered_indices]
            labels = labels[filtered_indices]
            
            # 转换为检测列表
            detections = []
            for box, score, label in zip(boxes, scores, labels):
                x1, y1, x2, y2 = box
                center_x = (x1 + x2) / 2
                center_y = (y1 + y2) / 2
                width = x2 - x1
                height = y2 - y1
                diameter = (width + height) / 2
                
                detection = {
                    'center': (int(center_x), int(center_y)),
                    'diameter': int(diameter),
                    'confidence': float(score),
                    'box': box.astype(int).tolist(),
                    'label': int(label)
                }
                detections.append(detection)
                
            return detections
            
        except Exception as e:
            logger.error(f"Error during detection: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None
            
    def _calculate_intersection(self, box1, box2):
        """计算两个边界框的IoU"""
        x1 = max(box1[0], box2[0])
        y1 = max(box1[1], box2[1])
        x2 = min(box1[2], box2[2])
        y2 = min(box1[3], box2[3])
        
        if x2 <= x1 or y2 <= y1:
            return 0.0
            
        intersection = (x2 - x1) * (y2 - y1)
        area1 = (box1[2] - box1[0]) * (box1[3] - box1[1])
        area2 = (box2[2] - box2[0]) * (box2[3] - box2[1])
        
        return intersection / min(area1, area2)
            
    def get_statistics(self, detections, image_shape):
        """Calculate detection statistics"""
        if not detections:
            return {
                'total_count': 0,
                'high_confidence': 0,
                'medium_confidence': 0,
                'low_confidence': 0,
                'average_confidence': 0.0,
                'average_diameter': 0.0,
                'density': 0.0
            }
            
        stats = {
            'total_count': len(detections),
            'high_confidence': len([d for d in detections if d['confidence'] >= 0.8]),
            'medium_confidence': len([d for d in detections if 0.6 <= d['confidence'] < 0.8]),
            'low_confidence': len([d for d in detections if d['confidence'] < 0.6]),
            'average_confidence': np.mean([d['confidence'] for d in detections]),
            'average_diameter': np.mean([d['diameter'] for d in detections]),
            'density': len(detections) / (image_shape[0] * image_shape[1] / 1000000)  # colonies/mm²
        }
        
        return stats
