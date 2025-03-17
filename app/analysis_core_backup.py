"""
Colony Detection Core
菌落检测核心
"""
import os # Adding import os again
import cv2
import torch
import numpy as np
import logging
from typing import Dict, List, Any, Optional
from time import time
from pathlib import Path

from .utils.path_manager import get_checkpoints_dir

logger = logging.getLogger(__name__)

class ColonyDetector:
    """Colony detection and analysis"""
    
    def __init__(self):
        # 基本参数设置 Basic parameters
        self._min_size = 5  # 最小菌落尺寸 (Minimum colony size)
        self._max_size = 100  # 最大菌落尺寸 (Maximum colony size)
        self._confidence = 0.5  # 检测置信度阈值 (Detection confidence threshold)
        self._use_gpu = False  # 是否使用GPU (Whether to use GPU)
        self._model = None
        self._device = None
        self.scale_x = 1.0
        self.scale_y = 1.0
        
        # 初始化模型 (Initialize model)
        self.load_model()

    def load_model(self):
        """Load the colony detection model"""
        checkpoint_path = "faster_rcnn_resnet50/checkpoints/checkpoint_epoch_31.pth" # Path to checkpoint file, provided by user
        if not os.path.exists(checkpoint_path):
            raise FileNotFoundError(f"Model checkpoint file not found: {checkpoint_path}")
        try:    
            checkpoint = torch.load(checkpoint_path, map_location=torch.device('cpu')) # Load checkpoint to CPU
            logger.info(f"Checkpoint keys: {checkpoint.keys()}") # Print checkpoint keys for inspection
            # Initialize device before model
            self._device = torch.device("cuda" if torch.cuda.is_available() and self._use_gpu else "cpu") # Use GPU if available and requested
            
            # Import and initialize the actual model from faster_rcnn_resnet50
            from app.models.colony_detector import ColonyDetectionModel  # Import the actual model class
            self._model = ColonyDetectionModel().to(self._device)  # Create model instance and move to device
            
            # Load the state dict with strict=False to ignore unexpected keys
            model_state_dict = checkpoint['model_state_dict']  # Get model state dict from checkpoint
            self._model.load_state_dict(model_state_dict, strict=False)  # Load state dict with strict=False
            self._model.to(self._device) # Move model to device
            self._model.eval() # Set model to evaluation mode
            logger.info(f"Model loaded from: {checkpoint_path}, using device: {self._device}")
        except Exception as e:
            logger.error(f"Error loading checkpoint from {checkpoint_path}: {e}")
            self._model = None # Ensure model is None in case of loading failure
            raise

    def estimate_colony_density(self, image: np.ndarray) -> Dict[str, Any]:
        """预估菌落密度并返回优化参数 (Estimate colony density and return optimized parameters)"""
        # 转换为灰度图并进行初步处理
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # 快速检测潜在菌落
        _, binary = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # 计算密度指标
        image_area = image.shape[0] * image.shape[1]
        colony_count = len(contours)
        density = colony_count / (image_area / 1000000)

        # 根据密度动态调整参数
        params = {
            'use_clahe': density > 5,  # 高密度时启用CLAHE
            'clahe_clip': min(4.0 + (density / 10), 6.0),  # 根据密度调整对比度限制
            'clahe_grid': (
                min(int(12 + density), 20),  # 根据密度调整网格大小
                min(int(12 + density), 20)
            ),
            'blur_kernel': (
                max(3, min(7, int(7 - density/10))) if max(3, min(7, int(7 - density/10))) % 2 != 0 else max(3, min(7, int(7 - density/10))) + 1,  # 密度越高，模糊程度越小, ensure odd
                max(3, min(7, int(7 - density/10))) if max(3, min(7, int(7 - density/10))) % 2 != 0 else max(3, min(7, int(7 - density/10))) + 1 # ensure odd
            ),
            'canny_min': max(30, min(50, int(50 - density))),
            'canny_max': max(100, min(150, int(150 - density))),
            'watershed_thresh': max(0.3, min(0.6, 0.6 - (density/20))),  # 密度越高，阈值越低
            'min_size': max(3, min(5, int(5 - density/10))),  # 密度越高，最小尺寸越小
            'max_size': max(50, min(100, int(100 - density*2))),  # 密度越高，最大尺寸越小
            'overlap_threshold': max(0.6, min(0.8, 0.8 - (density/20)))  # 密度越高，允许更多重叠
        }
        
        logger.info(f"预估密度: {density:.2f} colonies/mm², 参数已优化")
        return params

    def _check_special_image_type(self, image: np.ndarray, image_name: str) -> Dict[str, Any]:
        """检测图像类型并返回优化参数 (Detect image type and return optimized parameters)"""
        # 获取基础参数
        params = {
            'use_clahe': False,
            'clahe_clip': 3.0,
            'clahe_grid': (12, 12),
            'blur_kernel': (7, 7),
            'canny_min': 50,
            'canny_max': 150,
            'watershed_thresh': 0.5, # 将基础阈值从 0.6 调整为 0.5
            'min_size': self._min_size,
            'max_size': self._max_size,
            'overlap_threshold': 0.8,
            'adaptive_thresh_method': 'gaussian' # 默认使用高斯自适应阈值
        }
        
        # 特殊图像类型处理
        if "202104131002" in image_name:
            params.update({
                'use_clahe': True,
                'clahe_clip': 4.0,
                'clahe_grid': (16, 16),
                'blur_kernel': (5, 5),
                'canny_min': 40,
                'canny_max': 120,
                'watershed_thresh': 0.5,
                'min_size': 4,
                'max_size': 80,
                'overlap_threshold': 0.7
            })
            
        # 动态优化参数
        density_params = self.estimate_colony_density(image)
        
        # 合并参数，使用密度估计的参数覆盖基础参数
        params.update(density_params)
        
        return params

    def preprocess_image(self, image: np.ndarray, image_path: str = "") -> torch.Tensor:
        """图像预处理 (Image preprocessing)"""
        start_time = time()
        image_name = Path(image_path).name if image_path else ""
        
        # 获取优化参数
        params = self._check_special_image_type(image, image_name)
        
        # 调整检测参数
        self._min_size = params['min_size']
        self._max_size = params['max_size']
        
        # 图像缩放
        resized_image = cv2.resize(image, (512, 512))
        self.scale_x = image.shape[1] / resized_image.shape[1]
        self.scale_y = image.shape[0] / resized_image.shape[0]

        # 灰度转换和预处理
        gray = cv2.cvtColor(resized_image, cv2.COLOR_BGR2GRAY)

        if params['use_clahe']:
            clahe = cv2.createCLAHE(
                clipLimit=params['clahe_clip'],
                tileGridSize=params['clahe_grid']
            )
            gray = clahe.apply(gray)

        # 创建并应用掩码
        dish_mask = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV, 15, 3
        )
        
        # 选择自适应阈值方法
        adaptive_thresh_method = params['adaptive_thresh_method']
        if adaptive_thresh_method == 'gaussian':
            dish_mask = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY_INV, 15, 3
            )
        elif adaptive_thresh_method == 'mean':
            dish_mask = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C,
                cv2.THRESH_BINARY_INV, 15, 3
            )
        else: # 默认使用高斯方法
            dish_mask = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY_INV, 15, 3
            )
            
        dish_mask = cv2.dilate(dish_mask, None, iterations=2)
        masked_gray = cv2.bitwise_and(gray, gray, mask=dish_mask)

        # 图像增强
        blurred_gray = cv2.GaussianBlur(
            masked_gray,
            params['blur_kernel'], 0
        )

        edges = cv2.Canny(
            blurred_gray,
            params['canny_min'], # 密度自适应参数仍然使用 params
            params['canny_max']  # 密度自适应参数仍然使用 params
        )

        # 形态学处理
        kernel = np.ones((3,3), np.uint8)
        eroded = cv2.erode(edges, kernel, iterations=3)
        dilated = cv2.dilate(eroded, kernel, iterations=1)

        # 分水岭分割
        dist_transform = cv2.distanceTransform(dilated, cv2.DIST_L2, 5)
        _, sure_fg = cv2.threshold(
            dist_transform,
            params['watershed_thresh'] * dist_transform.max(),
            255, 0
        )
        sure_fg = np.uint8(sure_fg)

        # 标记处理
        sure_bg = cv2.dilate(dilated, None, iterations=3)
        unknown = cv2.subtract(sure_bg, sure_fg)
        _, markers = cv2.connectedComponents(sure_fg)
        markers = markers + 1
        markers[unknown == 255] = 0

        markers = cv2.resize(
            markers,
            (resized_image.shape[1], resized_image.shape[0]),
            interpolation=cv2.INTER_NEAREST
        )

        # 应用分水岭
        markers = cv2.watershed(
            cv2.cvtColor(resized_image.copy(), cv2.COLOR_BGR2RGB),
            markers
        )

        # 边界处理
        mask = np.uint8(markers == -1)
        opened_mask = cv2.morphologyEx(
            mask,
            cv2.MORPH_OPEN,
            kernel,
            iterations=1
        )

        # 可视化处理
        image = cv2.resize(image, (resized_image.shape[1], resized_image.shape[0]))
        image[opened_mask == 255] = [0, 0, 255]

        # 准备模型输入
        processed_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        processed_image = processed_image.astype(np.float32) / 255.0
        tensor_image = torch.from_numpy(processed_image).permute(2, 0, 1)

        processing_time = time() - start_time
        logger.info(f"图像预处理完成，耗时: {processing_time:.2f}秒")

        return tensor_image.to(self._device)

    def postprocess_detections(self, detections: List[Dict], orig_size: tuple, overlap_threshold: float = 0.8) -> List[Dict]:
        """处理检测结果 (Process detection results)"""
        colonies = []
        
        if not detections or not detections[0]["boxes"].shape[0]:
            return colonies

        boxes = detections[0]["boxes"].cpu().numpy()
        scores = detections[0]["scores"].cpu().numpy()
        labels = detections[0]["labels"].cpu().numpy()

        # 计算缩放因子
        height, width = orig_size
        scale_x = width / 512
        scale_y = height / 512

        # 按置信度排序
        indices = np.argsort(scores)[::-1]
        boxes = boxes[indices]
        scores = scores[indices]
        labels = labels[indices]

        for box, score, label in zip(boxes, scores, labels):
            if label == 1 and score >= self._confidence:
                x1, y1, x2, y2 = box

                # 计算坐标和大小
                x = int(((x1 + x2) / 2) * scale_x)
                y = int(((y1 + y2) / 2) * scale_y)
                w = int((x2 - x1) * scale_x)
                h = int((y2 - y1) * scale_y)
                radius = int((w + h) / 4)

                if self._min_size <= radius * 2 <= self._max_size:
                    # 检查重叠
                    overlapping = False
                    for colony in colonies:
                        dist = np.sqrt((colony['x'] - x)**2 + (colony['y'] - y)**2)
                        if dist < (colony['radius'] + radius) * overlap_threshold:
                            overlapping = True
                            break
                    
                    if not overlapping:
                        colonies.append({
                            "x": x,
                            "y": y,
                            "radius": radius,
                            "confidence": float(score)
                        })

        return colonies

    def analyze(self, image_path: str, **kwargs) -> Dict[str, Any]:
        """分析图像中的菌落 (Analyze colonies in image)"""
        start_time = time()

        # 获取参数 (Get parameters)
        self._confidence = kwargs.get('confidence', 0.5)  # 置信度阈值 (Confidence threshold)
        self._min_size = kwargs.get('min_size', 5)       # 最小尺寸 (Minimum size)
        self._max_size = kwargs.get('max_size', 100)     # 最大尺寸 (Maximum size)
        self._use_gpu = kwargs.get('use_gpu', False)     # 使用GPU (Use GPU)

        try:
            if self._model is None:
                self.load_model()

            # 读取图像 (Read image)
            image_path = Path(image_path).resolve()
            if not image_path.exists():
                raise FileNotFoundError(f"找不到图像: {image_path}")

            try:
                with open(image_path, 'rb') as f:
                    img_data = np.frombuffer(f.read(), np.uint8)
                image = cv2.imdecode(img_data, cv2.IMREAD_COLOR)
                if image is None:
                    raise ValueError(f"无法解码图像: {image_path}")
            except Exception as e:
                raise ValueError(f"读取图像失败: {image_path} - {str(e)}")

            # 获取图像尺寸和优化参数
            orig_size = image.shape[:2]
            tensor_image = self.preprocess_image(image, str(image_path))
            input_data = {'image': tensor_image, 'image_path': str(image_path)}

            # 调整阈值参数
            nms_threshold = kwargs.get('nms_threshold', 0.3)  # NMS阈值
            score_threshold = kwargs.get('score_threshold', 0.1)  # 分数阈值

            # 根据密度估计动态调整阈值
            params = self._check_special_image_type(image, str(image_path))
            nms_threshold = min(nms_threshold, 0.3 if params['use_clahe'] else 0.4)
            score_threshold = min(score_threshold, 0.1 if params['use_clahe'] else 0.15)

            # 模型推理
            self._model.eval()
            with torch.no_grad():
                detections = self._model(
                    input_data,
                    nms_threshold=nms_threshold,
                    score_threshold=score_threshold
                )
                logger.info(f"推理完成，NMS阈值={nms_threshold:.2f}, 分数阈值={score_threshold:.2f}")

            # 后处理检测结果
            colonies = self.postprocess_detections(
                detections, 
                orig_size,
                overlap_threshold=params['overlap_threshold']
            )

            # 计算指标
            total_area = sum([np.pi * c["radius"] ** 2 for c in colonies])
            image_area = orig_size[0] * orig_size[1]
            density = len(colonies) / (image_area / 1000000)  # 每平方毫米密度
            area_coverage = total_area / image_area

            # 记录处理时间
            process_time = time() - start_time
            logger.info(f"总处理时间: {process_time:.2f}秒")

            return {
                "colonies": colonies,         # 菌落列表 (Colony list)
                "count": len(colonies),       # 菌落数量 (Colony count)
                "density": density,           # 密度 (Density)
                "area": area_coverage,        # 覆盖率 (Coverage)
                "time": process_time,         # 处理时间 (Processing time)
                "parameters": params          # 使用的参数 (Used parameters)
            }

        except Exception as e:
            logger.error(f"分析失败: {e}")
            raise
