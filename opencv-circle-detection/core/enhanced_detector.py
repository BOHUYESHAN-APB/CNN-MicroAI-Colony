import cv2
import numpy as np
from typing import List, Optional, Tuple, Dict
from enum import Enum
from .models import Colony, PetriDish, SubstanceTypeEnum
from .processor import ImageProcessor, ImageQuality
from utils.logger import get_logger

logger = get_logger(__name__)

class DetectionMode(Enum):
    SINGLE_SUBSTANCE = 1
    MULTIPLE_SUBSTANCES = 2
    UNKNOWN = 0

class SubstanceType(Enum):
    FILTER_PAPER = 1
    HOLE = 2
    UNKNOWN = 0

class EnhancedCircleDetector:
    """增强的圆形检测器类，改进抑菌物质和抑菌圈检测精度"""

    def __init__(self, plate_diameter_mm: float = 90.0,
                 filter_paper_diameter_mm: float = 6.0,
                 hole_diameter_mm: float = 6.0):
        self.plate_diameter_mm = plate_diameter_mm
        self.filter_paper_diameter_mm = filter_paper_diameter_mm
        self.hole_diameter_mm = hole_diameter_mm
        self.processor = ImageProcessor()
        self.px_per_mm = None
        self.detection_mode = DetectionMode.UNKNOWN
        self.substance_type = SubstanceType.UNKNOWN
        self.detected_substances: List[Colony] = []

    def detect_petri_dishes(self, image: np.ndarray) -> List[PetriDish]:
        """检测培养皿并进行尺寸标定"""
        logger.info("开始检测培养皿")
        self.px_per_mm = None
        
        # 预处理
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        # 增强预处理：添加高斯模糊和对比度增强
        blurred = cv2.GaussianBlur(gray, (9, 9), 2)
        enhanced = self.processor.enhance_contrast(blurred)
        processed = self.processor.preprocess(enhanced)
        
        # 多尺度检测参数
        detection_params = [
            {
                'dp': 1,
                'minDist': max(400, image.shape[0]//3),
                'param1': 50,
                'param2': 30,  # 降低阈值以提高检测灵敏度
                'minRadius': int(image.shape[0]/4),
                'maxRadius': int(image.shape[0]/1.5)
            },
            {
                'dp': 1.2,
                'minDist': max(300, image.shape[0]//4),
                'param1': 60,
                'param2': 35,
                'minRadius': int(image.shape[0]/3.5),
                'maxRadius': int(image.shape[0]/1.8)
            }
        ]
        
        all_circles = []
        for params in detection_params:
            circles = cv2.HoughCircles(
                processed,
                cv2.HOUGH_GRADIENT,
                **params
            )
            if circles is not None:
                all_circles.extend(circles[0,:])
        
        # 去重和验证
        plates = []
        if all_circles:
            # 合并相近的检测结果
            merged_circles = self._merge_similar_circles(all_circles, min_distance=50)
            
            for x, y, r in merged_circles:
                if self._validate_dish_circle(processed, (int(x), int(y)), int(r)):
                    plates.append(PetriDish(
                        center=(int(x), int(y)),
                        radius=int(r),
                        diameter_mm=self.plate_diameter_mm
                    ))
                    # 更新像素比例
                    self.px_per_mm = r * 2 / self.plate_diameter_mm
                    logger.info(f"标定比例: {self.px_per_mm:.2f}px/mm")
        
        logger.info(f"检测到 {len(plates)} 个培养皿")
        return plates

    def _merge_similar_circles(self, circles: List, min_distance: float = 50) -> List:
        """合并相近的圆检测结果"""
        if not circles:
            return []
        
        merged = []
        used = set()
        
        for i, (x1, y1, r1) in enumerate(circles):
            if i in used:
                continue
                
            # 找到所有相近的圆
            similar_circles = [(x1, y1, r1)]
            for j, (x2, y2, r2) in enumerate(circles):
                if j <= i or j in used:
                    continue
                    
                distance = np.sqrt((x1 - x2)**2 + (y1 - y2)**2)
                if distance < min_distance:
                    similar_circles.append((x2, y2, r2))
                    used.add(j)
            
            # 计算平均值
            avg_x = np.mean([x for x, y, r in similar_circles])
            avg_y = np.mean([y for x, y, r in similar_circles])
            avg_r = np.mean([r for x, y, r in similar_circles])
            
            merged.append((avg_x, avg_y, avg_r))
            used.add(i)
        
        return merged

    def enhanced_detect_substances_by_type(self, image: np.ndarray, dish: PetriDish, 
                                         substance_type: SubstanceType) -> List[Colony]:
        """增强的抑菌物质检测算法"""
        if self.px_per_mm is None:
            raise ValueError("请先进行培养皿检测和尺寸标定")

        logger.info(f"开始增强检测 {substance_type.name}")

        # 创建培养皿掩码
        dish_mask = np.zeros(image.shape[:2], dtype=np.uint8)
        cv2.circle(dish_mask, dish.center, int(dish.radius * 0.95), 255, -1)  # 稍微缩小搜索区域
        
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        masked_dish_gray = cv2.bitwise_and(gray, gray, mask=dish_mask)
        
        # 计算预期尺寸
        diameter_mm = self.filter_paper_diameter_mm if substance_type == SubstanceType.FILTER_PAPER else self.hole_diameter_mm
        expected_radius_px = int(diameter_mm * self.px_per_mm / 2)
        
        # 多参数检测策略
        detection_results = []
        
        if substance_type == SubstanceType.FILTER_PAPER:
            detection_results.extend(self._detect_filter_papers_enhanced(masked_dish_gray, dish, expected_radius_px))
        elif substance_type == SubstanceType.HOLE:
            detection_results.extend(self._detect_holes_enhanced(masked_dish_gray, dish, expected_radius_px))
        
        # 去重和验证
        final_results = self._filter_and_validate_detections(detection_results, dish, substance_type)
        
        logger.info(f"增强检测到 {len(final_results)} 个 {substance_type.name}")
        return final_results

    def _detect_filter_papers_enhanced(self, masked_gray: np.ndarray, dish: PetriDish, 
                                     expected_radius: int) -> List[Colony]:
        """增强的滤纸片检测"""
        detections = []
        
        # 多种预处理策略
        preprocessing_methods = [
            lambda img: self.processor.preprocess(img),
            lambda img: self.processor.enhance_contrast(img),
            lambda img: cv2.GaussianBlur(self.processor.preprocess(img), (5, 5), 1),
        ]
        
        # 多组参数配置
        param_sets = [
            {
                'dp': 1.0,
                'param1': 50,
                'param2': 20,  # 更低的阈值
                'radius_factor': (0.7, 1.3)
            },
            {
                'dp': 1.2,
                'param1': 60,
                'param2': 25,
                'radius_factor': (0.8, 1.2)
            },
            {
                'dp': 1.5,
                'param1': 40,
                'param2': 15,  # 非常低的阈值，提高检测灵敏度
                'radius_factor': (0.75, 1.25)
            }
        ]
        
        for preprocess_func in preprocessing_methods:
            processed_img = preprocess_func(masked_gray)
            
            for params in param_sets:
                min_radius = max(3, int(expected_radius * params['radius_factor'][0]))
                max_radius = int(expected_radius * params['radius_factor'][1])
                min_dist = max(int(expected_radius * 1.5), 15)
                
                circles = cv2.HoughCircles(
                    processed_img,
                    cv2.HOUGH_GRADIENT,
                    dp=params['dp'],
                    minDist=min_dist,
                    param1=params['param1'],
                    param2=params['param2'],
                    minRadius=min_radius,
                    maxRadius=max_radius
                )
                
                if circles is not None:
                    for x, y, r in circles[0,:]:
                        # 亮度验证（滤纸片通常比背景亮）
                        if self._validate_roi_brightness_enhanced(
                            masked_gray, (int(x), int(y)), int(r), 
                            check_bright=True, adaptive_threshold=True
                        ):
                            detections.append(Colony(
                                center=(int(x), int(y)),
                                radius=int(r),
                                contour=self._create_circle_contour((int(x), int(y)), int(r)),
                                substance_type=SubstanceTypeEnum.FILTER_PAPER
                            ))
        
        return detections

    def _detect_holes_enhanced(self, masked_gray: np.ndarray, dish: PetriDish, 
                             expected_radius: int) -> List[Colony]:
        """增强的孔洞检测"""
        detections = []
        
        # 反转图像用于孔洞检测
        inverted_gray = cv2.bitwise_not(masked_gray)
        
        # 多种预处理策略
        preprocessing_methods = [
            lambda img: self.processor.preprocess(img),
            lambda img: cv2.GaussianBlur(img, (3, 3), 1),
            lambda img: cv2.morphologyEx(img, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))),
        ]
        
        # 针对孔洞的参数配置
        param_sets = [
            {
                'dp': 1.0,
                'param1': 30,  # 更低的Canny阈值
                'param2': 10,  # 更低的累积阈值
                'radius_factor': (0.6, 1.4)
            },
            {
                'dp': 1.2,
                'param1': 40,
                'param2': 12,
                'radius_factor': (0.7, 1.3)
            },
            {
                'dp': 1.5,
                'param1': 25,
                'param2': 8,   # 非常低的阈值
                'radius_factor': (0.65, 1.35)
            }
        ]
        
        for preprocess_func in preprocessing_methods:
            processed_img = preprocess_func(inverted_gray)
            
            for params in param_sets:
                min_radius = max(3, int(expected_radius * params['radius_factor'][0]))
                max_radius = int(expected_radius * params['radius_factor'][1])
                min_dist = max(int(expected_radius * 1.2), 10)
                
                circles = cv2.HoughCircles(
                    processed_img,
                    cv2.HOUGH_GRADIENT,
                    dp=params['dp'],
                    minDist=min_dist,
                    param1=params['param1'],
                    param2=params['param2'],
                    minRadius=min_radius,
                    maxRadius=max_radius
                )
                
                if circles is not None:
                    for x, y, r in circles[0,:]:
                        # 暗度验证（孔洞在原图中应该较暗）
                        if self._validate_roi_brightness_enhanced(
                            masked_gray, (int(x), int(y)), int(r), 
                            check_bright=False, adaptive_threshold=True
                        ):
                            detections.append(Colony(
                                center=(int(x), int(y)),
                                radius=int(r),
                                contour=self._create_circle_contour((int(x), int(y)), int(r)),
                                substance_type=SubstanceTypeEnum.HOLE
                            ))
        
        return detections

    def _validate_roi_brightness_enhanced(self, image_gray: np.ndarray, center: Tuple[int, int], 
                                        radius: int, check_bright: bool = True, 
                                        adaptive_threshold: bool = False) -> bool:
        """增强的ROI亮度验证"""
        x, y = center
        
        # 创建ROI掩码
        mask = np.zeros(image_gray.shape[:2], dtype=np.uint8)
        cv2.circle(mask, (x, y), max(1, int(radius * 0.8)), 255, -1)
        roi_pixels = image_gray[mask == 255]
        
        if roi_pixels.size < 5:
            return False
        
        mean_brightness = np.mean(roi_pixels)
        std_dev = np.std(roi_pixels)
        
        if adaptive_threshold:
            # 自适应阈值：基于局部图像统计
            local_roi_size = max(radius * 3, 50)
            x1 = max(0, x - local_roi_size)
            y1 = max(0, y - local_roi_size)
            x2 = min(image_gray.shape[1], x + local_roi_size)
            y2 = min(image_gray.shape[0], y + local_roi_size)
            
            local_region = image_gray[y1:y2, x1:x2]
            local_mean = np.mean(local_region)
            local_std = np.std(local_region)
            
            if check_bright:
                threshold = local_mean + 0.3 * local_std
                brightness_valid = mean_brightness > threshold
            else:
                threshold = local_mean - 0.3 * local_std
                brightness_valid = mean_brightness < threshold
        else:
            # 固定阈值
            threshold = 120 if check_bright else 90
            brightness_valid = (mean_brightness > threshold) if check_bright else (mean_brightness < threshold)
        
        # 均匀性检查
        max_std_threshold = 35.0 if not check_bright else 25.0
        uniformity_valid = std_dev < max_std_threshold
        
        return brightness_valid and uniformity_valid

    def _filter_and_validate_detections(self, detections: List[Colony], dish: PetriDish, 
                                       substance_type: SubstanceType) -> List[Colony]:
        """过滤和验证检测结果"""
        if not detections:
            return []
        
        # 1. 去除培养皿外的检测
        valid_detections = []
        for detection in detections:
            x, y = detection.center
            distance_to_center = np.sqrt((x - dish.center[0])**2 + (y - dish.center[1])**2)
            if distance_to_center + detection.radius <= dish.radius * 0.95:
                valid_detections.append(detection)
        
        # 2. 基于距离的非极大值抑制
        if len(valid_detections) > 1:
            valid_detections = self._non_maximum_suppression(valid_detections)
        
        # 3. 基于质量评分排序和筛选
        scored_detections = []
        for detection in valid_detections:
            score = self._calculate_detection_quality_score(detection, dish)
            detection.detection_score = score
            scored_detections.append(detection)
        
        # 按得分排序，保留前N个最佳检测
        scored_detections.sort(key=lambda x: x.detection_score, reverse=True)
        max_detections = 5  # 最多保留5个检测结果
        
        return scored_detections[:max_detections]

    def _non_maximum_suppression(self, detections: List[Colony], 
                                overlap_threshold: float = 0.3) -> List[Colony]:
        """非极大值抑制"""
        if len(detections) <= 1:
            return detections
        
        # 按检测得分排序
        detections.sort(key=lambda x: getattr(x, 'detection_score', 0), reverse=True)
        
        suppressed = []
        used = set()
        
        for i, det1 in enumerate(detections):
            if i in used:
                continue
                
            suppressed.append(det1)
            
            for j, det2 in enumerate(detections[i+1:], i+1):
                if j in used:
                    continue
                    
                # 计算重叠度
                distance = np.sqrt((det1.center[0] - det2.center[0])**2 + 
                                 (det1.center[1] - det2.center[1])**2)
                min_distance = (det1.radius + det2.radius) * overlap_threshold
                
                if distance < min_distance:
                    used.add(j)
        
        return suppressed

    def _calculate_detection_quality_score(self, detection: Colony, dish: PetriDish) -> float:
        """计算检测质量得分"""
        # 基于多个因素计算得分
        score = 0.0
        
        # 1. 距离培养皿中心的得分（越靠近中心得分越高，但不是绝对要求）
        distance_to_center = np.sqrt((detection.center[0] - dish.center[0])**2 + 
                                   (detection.center[1] - dish.center[1])**2)
        max_distance = dish.radius * 0.8
        distance_score = max(0, 1 - distance_to_center / max_distance) * 0.3
        
        # 2. 尺寸合理性得分
        expected_radius = int(self.filter_paper_diameter_mm * self.px_per_mm / 2) if self.px_per_mm else 20
        size_diff = abs(detection.radius - expected_radius) / expected_radius
        size_score = max(0, 1 - size_diff) * 0.4
        
        # 3. 圆形度得分（基于轮廓）
        if detection.contour is not None:
            area = cv2.contourArea(detection.contour)
            perimeter = cv2.arcLength(detection.contour, True)
            if perimeter > 0:
                circularity = 4 * np.pi * area / (perimeter * perimeter)
                circularity_score = min(circularity, 1.0) * 0.3
            else:
                circularity_score = 0.0
        else:
            circularity_score = 0.5  # 默认得分
        
        score = distance_score + size_score + circularity_score
        return score

    def _validate_dish_circle(self, image: np.ndarray, center: Tuple[int, int], radius: int) -> bool:
        """验证培养皿圆形的有效性"""
        x, y = center
        h, w = image.shape[:2]
        
        # 基本边界检查
        if x - radius < 0 or x + radius >= w or y - radius < 0 or y + radius >= h:
            return False
        
        # 检查圆周上的像素强度变化（培养皿边缘应该有明显对比度）
        angles = np.linspace(0, 2*np.pi, 32)
        edge_intensities = []
        
        for angle in angles:
            edge_x = int(x + radius * np.cos(angle))
            edge_y = int(y + radius * np.sin(angle))
            if 0 <= edge_x < w and 0 <= edge_y < h:
                edge_intensities.append(image[edge_y, edge_x])
        
        if len(edge_intensities) < 16:
            return False
        
        # 检查边缘强度的变化
        edge_std = np.std(edge_intensities)
        return edge_std > 15  # 要求边缘有一定的强度变化

    def _create_circle_contour(self, center: Tuple[int, int], radius: int) -> np.ndarray:
        """创建圆形轮廓"""
        angles = np.linspace(0, 2*np.pi, 32)
        points = []
        for angle in angles:
            x = int(center[0] + radius * np.cos(angle))
            y = int(center[1] + radius * np.sin(angle))
            points.append([x, y])
        return np.array(points, dtype=np.int32)

    def analyze_dish_contents(self, image: np.ndarray, dish: PetriDish) -> Tuple[DetectionMode, SubstanceType, List[Colony]]:
        """分析培养皿内容"""
        logger.info(f"开始分析培养皿 {dish.center} 内的物质...")
        if self.px_per_mm is None:
            logger.error("px_per_mm 未标定，无法分析培养皿内容。")
            return DetectionMode.UNKNOWN, SubstanceType.UNKNOWN, []

        papers = self.enhanced_detect_substances_by_type(image, dish, SubstanceType.FILTER_PAPER)
        holes = self.enhanced_detect_substances_by_type(image, dish, SubstanceType.HOLE)

        detected_substances = []
        final_substance_type = SubstanceType.UNKNOWN
        detection_mode = DetectionMode.UNKNOWN

        if len(papers) > 0 and len(holes) == 0:
            detected_substances = papers
            final_substance_type = SubstanceType.FILTER_PAPER
            logger.info(f"主要检测到滤纸片: {len(papers)} 个")
        elif len(holes) > 0 and len(papers) == 0:
            detected_substances = holes
            final_substance_type = SubstanceType.HOLE
            logger.info(f"主要检测到孔洞: {len(holes)} 个")
        elif len(papers) > 0 and len(holes) > 0:
            logger.warning(f"同时检测到 {len(papers)} 个滤纸片和 {len(holes)} 个孔洞。优先考虑得分较高者。")
            # 比较最高得分
            best_paper_score = max([p.detection_score for p in papers]) if papers else 0
            best_hole_score = max([h.detection_score for h in holes]) if holes else 0
            
            if best_paper_score >= best_hole_score:
                detected_substances = papers
                final_substance_type = SubstanceType.FILTER_PAPER
            else:
                detected_substances = holes
                final_substance_type = SubstanceType.HOLE
        else:
            logger.warning("未能明确检测到滤纸片或孔洞。")

        if len(detected_substances) == 1:
            detection_mode = DetectionMode.SINGLE_SUBSTANCE
        elif len(detected_substances) > 1:
            detection_mode = DetectionMode.MULTIPLE_SUBSTANCES
        else:
            logger.info("未检测到明确的抑菌物质，可能为单一抑菌圈在中心。")
            detection_mode = DetectionMode.SINGLE_SUBSTANCE
            final_substance_type = SubstanceType.UNKNOWN

        self.detection_mode = detection_mode
        self.substance_type = final_substance_type
        self.detected_substances = detected_substances

        logger.info(f"分析完成: 模式={detection_mode.name}, 类型={final_substance_type.name}, 数量={len(detected_substances)}")
        return detection_mode, final_substance_type, detected_substances