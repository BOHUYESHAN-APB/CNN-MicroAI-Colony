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
from datetime import datetime
from pathlib import Path

from .utils.path_manager import get_checkpoints_dir

logger = logging.getLogger(__name__)

class ColonyDetector:
    """Colony detection and analysis"""
    
    def __init__(self, config=None): # Added config
        # Config
        self.config = config  # Store config
        
        # Basic parameters
        self._min_size = 5  # Minimum colony size
        self._max_size = 100 # Maximum colony size
        self._confidence = 0.5  # Detection confidence threshold
        self._use_gpu = False  # Whether to use GPU
        self._model = None
        self._device = None
        self.scale_x = 1.0
        self.scale_y = 1.0
        
        # Initialize model
        self.load_model()

    def _create_info_panel(self, image: np.ndarray, colonies: List[Dict], density: float, 
                          area_coverage: float, confidence_thresh: float, process_time: float, 
                          image_name: str, petri_size: int = 90) -> np.ndarray:
        """在原图右侧添加信息面板并标注菌落"""
        h, w = image.shape[:2]
        info_width = 400  # 扩大信息区域宽度
        
        # 在原图上标注菌落
        annotated_image = image.copy()
        for colony in colonies:
            x, y = colony['x'], colony['y']
            r = colony['radius']
            conf = colony['confidence']
            
            # 根据置信度设置颜色 (绿色到红色)
            color = (
                int(255 * (1 - conf)),  # B
                int(255 * conf),        # G
                0                       # R
            )
            
            # 画圆圈标注菌落
            cv2.circle(annotated_image, (x, y), r, color, 2)
            
        # 创建带有信息区域的新画布
        canvas = np.ones((h, w + info_width, 3), dtype=np.uint8) * 255
        canvas[:, :w] = annotated_image  # 复制带标注的图
        
        # 添加文本信息
        text_color = (0, 0, 0)  # 黑色文字
        font = cv2.FONT_HERSHEY_SIMPLEX
        start_x = w + 20
        start_y = 50
        line_gap = 35
        
        # 获取当前时间
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 标题和文件信息
        cv2.putText(canvas, "分析结果", (start_x, start_y), 
                    font, 1.0, (0, 0, 255), 2)
        start_y += line_gap
        
        cv2.putText(canvas, f"文件: {image_name}", 
                    (start_x, start_y), font, 0.6, text_color, 1)
        start_y += line_gap
        
        cv2.putText(canvas, f"分析时间: {current_time}", 
                    (start_x, start_y), font, 0.6, text_color, 1)
        start_y += line_gap * 1.5

        # 分析结果
        results = [
            ("菌落数量", f"{len(colonies)} 个"),
            ("培养皿大小", f"{petri_size} mm"),
            ("菌落密度", f"{density:.2f} 个/mm²"),
            ("覆盖面积", f"{area_coverage:.2%}"),
            ("置信度阈值", f"{confidence_thresh:.2f}"),
            ("分析用时", f"{process_time:.2f} 秒")
        ]

        for label, value in results:
            cv2.putText(canvas, f"{label}: {value}", 
                        (start_x, start_y), font, 0.7, text_color, 2)
            start_y += line_gap

        # 添加置信度图例
        start_y += line_gap
        cv2.putText(canvas, "置信度图例:", 
                    (start_x, start_y), font, 0.7, text_color, 2)
        start_y += line_gap

        legend_width = 200
        legend_height = 20
        for i in range(legend_width):
            confidence = i / legend_width
            color = (
                int(255 * (1 - confidence)),
                int(255 * confidence),
                0
            )
            cv2.line(canvas, 
                     (start_x + i, start_y),
                     (start_x + i, start_y + legend_height),
                     color,
                     1)

        cv2.putText(canvas, "低", 
                    (start_x, start_y + legend_height + 20),
                    font, 0.6, text_color, 1)
        cv2.putText(canvas, "高", 
                    (start_x + legend_width - 20, start_y + legend_height + 20),
                    font, 0.6, text_color, 1)
        
        return canvas

    def load_model(self):
        """Load the colony detection model"""
        self._load_detection_model()

    def _load_detection_model(self):
        """Load the colony detection model based on configuration"""
        config = self.config.config  # 获取 ConfigManager 实例
        model_type = config.get("model.type", "faster_rcnn_resnet50")  # 从配置中读取模型类型，默认为 faster_rcnn_resnet50
        checkpoint_path = ""
        model_class = None

        if model_type == "faster_rcnn_resnet50":
            checkpoint_path = config.get("model.faster_rcnn_resnet50.checkpoint_path", "faster_rcnn_resnet50/checkpoints/checkpoint_epoch_31.pth")
            from app.models.colony_detector import ColonyDetectionModel
            model_class = ColonyDetectionModel
        elif model_type == "yolov11":
            checkpoint_path = config.get("model.yolov11.checkpoint_path", "yolo11/checkpoints/best.pth")
            from yolo11.src.models.yolo11 import YOLO11Detector
            model_class = YOLO11Detector
        else:
            raise ValueError(f"Unknown model type: {model_type}")

        if not os.path.exists(checkpoint_path):
            raise FileNotFoundError(f"Model checkpoint file not found: {checkpoint_path}")
        try:
            checkpoint = torch.load(checkpoint_path, map_location=torch.device('cpu'))
            logger.info(f"Checkpoint keys: {checkpoint.keys()}")
            self._device = torch.device("cuda" if torch.cuda.is_available() and self._use_gpu else "cpu")
            if model_type == "faster_rcnn_resnet50":
                num_classes = 2  # Use 2 classes for the pre-trained Faster R-CNN model
            else:
                num_classes = config.get("model.num_classes", 1)
            self._model = model_class(num_classes=num_classes).to(self._device)

            if model_type == "faster_rcnn_resnet50":
                model_state_dict = checkpoint['model_state_dict']
            elif model_type == "yolov11":
                model_state_dict = checkpoint['state_dict']
            else:
                raise ValueError(f"Unknown model type: {model_type}")

            self._model.load_state_dict(model_state_dict, strict=False)
            self._model.to(self._device)
            self._model.eval()
            logger.info(f"Model loaded from: {checkpoint_path}, using device: {self._device}, type: {model_type}")
        except Exception as e:
            logger.error(f"Error loading checkpoint from {checkpoint_path}: {e}")
            self._model = None
            raise

    def estimate_colony_density(self, image: np.ndarray) -> Dict[str, Any]:
        """预估菌落密度并返回优化参数 (Estimate colony density and return optimized parameters)"""
        # 转换为灰度图并进行初步处理
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)

        # 计算图像清晰度 (Laplacian variance)
        laplacian = cv2.Laplacian(blurred, cv2.CV_64F)
        clarity = np.var(laplacian)
        logger.info(f"图像清晰度 (Laplacian variance): {clarity:.2f}")

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
            'clahe_clip': 2.0, # 降低 CLAHE clip limit 
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

    def analyze_image(self, image_path: str, **kwargs) -> Dict[str, Any]:
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

            # 创建带信息面板的结果图像
            petri_size = kwargs.get('petri_size', 90)  # 获取培养皿大小，默认90mm
            annotated_image = self._create_info_panel(
                image=image,
                colonies=colonies,
                density=density,
                area_coverage=area_coverage,
                confidence_thresh=self._confidence,
                process_time=process_time,
                image_name=Path(image_path).name,
                petri_size=petri_size
            )

            # 保存结果图像
            results_dir = os.path.join("app", "results")
            os.makedirs(results_dir, exist_ok=True)  # 确保目录存在
            result_path = os.path.join(results_dir, f"{Path(image_path).stem}_result.png")
            cv2.imencode('.png', annotated_image)[1].tofile(result_path)

            # 准备UI显示的摘要信息
            summary = f"菌落数量: {len(colonies)}\n" \
                     f"置信度阈值: {self._confidence}\n" \
                     f"处理时间: {process_time:.2f}秒"

            return {
                "colonies": colonies,         # 菌落列表 (Colony list)
                "count": len(colonies),       # 菌落数量 (Colony count)
                "density": density,           # 密度 (Density)
                "area": area_coverage,        # 覆盖率 (Coverage)
                "time": process_time,         # 处理时间 (Processing time)
                "parameters": params,         # 使用的参数 (Used parameters)
                "result_image": result_path,  # 结果图像路径
                "summary": summary           # UI显示的摘要信息
            }

        except Exception as e:
            logger.error(f"分析失败: {e}")
            raise
