import cv2
import numpy as np
from typing import List, Optional, Tuple, Dict
from enum import Enum
from .models import Colony, PetriDish, SubstanceTypeEnum
from .processor import ImageProcessor
from utils.logger import get_logger

logger = get_logger(__name__)

class FinalOptimizedDetector:
    """最终优化版检测器 - 基于用户反馈精确调优"""

    def __init__(self, plate_diameter_mm: float = 90.0,
                 filter_paper_diameter_mm: float = 6.0,
                 hole_diameter_mm: float = 6.0):
        self.plate_diameter_mm = plate_diameter_mm
        self.filter_paper_diameter_mm = filter_paper_diameter_mm
        self.hole_diameter_mm = hole_diameter_mm
        self.processor = ImageProcessor()
        self.px_per_mm = None

    def detect_petri_dishes_optimized(self, image: np.ndarray) -> List[PetriDish]:
        """优化的培养皿检测 - 确保稳定检测"""
        logger.info("开始优化培养皿检测")
        
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        h, w = gray.shape
        
        # 多层次检测策略
        dishes = []
        
        # 策略1: 标准霍夫圆检测
        processed1 = self.processor.preprocess(gray)
        circles1 = cv2.HoughCircles(
            processed1,
            cv2.HOUGH_GRADIENT,
            dp=1.0,
            minDist=max(200, min(h,w)//3),
            param1=50,
            param2=30,
            minRadius=min(h,w)//6,
            maxRadius=min(h,w)//2
        )
        
        # 策略2: 增强对比度检测（针对低对比度图像）
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        processed2 = self.processor.preprocess(enhanced)
        circles2 = cv2.HoughCircles(
            processed2,
            cv2.HOUGH_GRADIENT,
            dp=1.2,
            minDist=max(150, min(h,w)//4),
            param1=40,
            param2=25,
            minRadius=min(h,w)//8,
            maxRadius=min(h,w)//2
        )
        
        # 合并所有检测结果
        all_circles = []
        if circles1 is not None:
            all_circles.extend(circles1[0,:])
        if circles2 is not None:
            all_circles.extend(circles2[0,:])
        
        if all_circles:
            # 选择最佳的培养皿（最大且质量最好的）
            best_circle = self._select_best_dish(all_circles, gray)
            if best_circle:
                x, y, r = best_circle
                dishes.append(PetriDish(
                    center=(int(x), int(y)),
                    radius=int(r),
                    diameter_mm=self.plate_diameter_mm
                ))
                self.px_per_mm = r * 2 / self.plate_diameter_mm
                logger.info(f"检测到培养皿: 中心({int(x)},{int(y)}), 半径{int(r)}px, 标定{self.px_per_mm:.2f}px/mm")
        
        return dishes

    def _select_best_dish(self, circles: List, image: np.ndarray) -> Optional[Tuple]:
        """从候选圆中选择最佳的培养皿"""
        scored_circles = []
        
        for x, y, r in circles:
            # 质量评分
            score = self._calculate_dish_score(image, (int(x), int(y)), int(r))
            scored_circles.append((x, y, r, score))
        
        if not scored_circles:
            return None
        
        # 选择得分最高且尺寸最大的
        scored_circles.sort(key=lambda c: (c[3], c[2]), reverse=True)
        return scored_circles[0][:3]

    def _calculate_dish_score(self, image: np.ndarray, center: Tuple[int, int], radius: int) -> float:
        """计算培养皿质量得分"""
        x, y = center
        h, w = image.shape
        
        # 边界检查
        if x-radius < 0 or x+radius >= w or y-radius < 0 or y+radius >= h:
            return 0.0
        
        score = 0.0
        
        # 1. 尺寸合理性 (40%)
        ideal_radius = min(h, w) // 3
        size_diff = abs(radius - ideal_radius) / ideal_radius
        size_score = max(0, 1 - size_diff)
        score += size_score * 0.4
        
        # 2. 边缘强度 (40%)
        edge_score = self._calculate_edge_strength(image, center, radius)
        score += edge_score * 0.4
        
        # 3. 圆形度 (20%)
        circularity_score = self._calculate_circularity(image, center, radius)
        score += circularity_score * 0.2
        
        return score

    def _calculate_edge_strength(self, image: np.ndarray, center: Tuple[int, int], radius: int) -> float:
        """计算边缘强度"""
        x, y = center
        angles = np.linspace(0, 2*np.pi, 32)
        gradients = []
        
        for angle in angles:
            # 内外采样点
            inner_r = max(1, radius - 3)
            outer_r = radius + 3
            
            inner_x = int(x + inner_r * np.cos(angle))
            inner_y = int(y + inner_r * np.sin(angle))
            outer_x = int(x + outer_r * np.cos(angle))
            outer_y = int(y + outer_r * np.sin(angle))
            
            if (0 <= inner_x < image.shape[1] and 0 <= inner_y < image.shape[0] and
                0 <= outer_x < image.shape[1] and 0 <= outer_y < image.shape[0]):
                gradient = abs(int(image[inner_y, inner_x]) - int(image[outer_y, outer_x]))
                gradients.append(gradient)
        
        if gradients:
            avg_gradient = np.mean(gradients)
            return min(avg_gradient / 30.0, 1.0)
        return 0.0

    def _calculate_circularity(self, image: np.ndarray, center: Tuple[int, int], radius: int) -> float:
        """计算圆形度"""
        x, y = center
        angles = np.linspace(0, 2*np.pi, 16)
        
        # 检查圆周上点的强度一致性
        intensities = []
        for angle in angles:
            px = int(x + radius * np.cos(angle))
            py = int(y + radius * np.sin(angle))
            if 0 <= px < image.shape[1] and 0 <= py < image.shape[0]:
                intensities.append(image[py, px])
        
        if len(intensities) > 8:
            std_dev = np.std(intensities)
            return max(0, 1 - std_dev / 50.0)
        return 0.0

    def detect_transparent_holes_final(self, image: np.ndarray, dish: PetriDish) -> List[Colony]:
        """最终优化的透明挖孔检测 - 目标：准确检测4个挖孔，排除气泡"""
        logger.info("开始最终优化透明挖孔检测")
        
        if self.px_per_mm is None:
            return []
        
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # 限制搜索区域到培养皿内部
        dish_mask = np.zeros(gray.shape[:2], dtype=np.uint8)
        cv2.circle(dish_mask, dish.center, int(dish.radius * 0.9), 255, -1)
        masked_gray = cv2.bitwise_and(gray, gray, mask=dish_mask)
        
        holes = []
        
        # 预期挖孔尺寸
        expected_radius = int(self.hole_diameter_mm * self.px_per_mm / 2)
        
        # 策略1: 基于暗区域的形态学检测
        holes.extend(self._detect_holes_morphology(masked_gray, dish, expected_radius))
        
        # 策略2: 基于轮廓的检测
        holes.extend(self._detect_holes_contours(masked_gray, dish, expected_radius))
        
        # 策略3: 基于霍夫圆的检测
        holes.extend(self._detect_holes_hough(masked_gray, dish, expected_radius))
        
        # 智能过滤：去除气泡，保留真实挖孔
        validated_holes = self._filter_holes_vs_bubbles(holes, masked_gray, dish)
        
        # 确保检测数量合理（目标4个）
        final_holes = self._select_best_holes(validated_holes, target_count=4)
        
        logger.info(f"透明挖孔最终检测: {len(final_holes)} 个")
        return final_holes

    def _detect_holes_morphology(self, image: np.ndarray, dish: PetriDish, expected_radius: int) -> List[Colony]:
        """基于形态学的挖孔检测"""
        holes = []
        
        # 计算自适应阈值
        mean_val = np.mean(image[image > 0])
        std_val = np.std(image[image > 0])
        
        # 检测暗区域
        dark_threshold = mean_val - 0.8 * std_val
        _, binary = cv2.threshold(image, dark_threshold, 255, cv2.THRESH_BINARY_INV)
        
        # 形态学操作 - 专门针对圆形孔洞
        kernel_size = max(3, expected_radius // 4)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
        
        # 开运算去除小噪声
        binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel, iterations=1)
        # 闭运算连接断开的部分
        binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel, iterations=2)
        
        # 查找轮廓
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            area = cv2.contourArea(contour)
            expected_area = np.pi * (expected_radius ** 2)
            
            # 面积筛选
            if area < expected_area * 0.15 or area > expected_area * 8:
                continue
            
            # 轮廓拟合圆
            (x, y), radius = cv2.minEnclosingCircle(contour)
            center = (int(x), int(y))
            radius = int(radius)
            
            # 位置验证
            if self._is_valid_hole_position(center, radius, dish):
                holes.append(Colony(
                    center=center,
                    radius=radius,
                    contour=contour,
                    substance_type=SubstanceTypeEnum.HOLE,
                    detection_score=0.6
                ))
        
        return holes

    def _detect_holes_contours(self, image: np.ndarray, dish: PetriDish, expected_radius: int) -> List[Colony]:
        """基于轮廓的挖孔检测"""
        holes = []
        
        # 边缘检测
        edges = cv2.Canny(image, 20, 60)
        
        # 膨胀边缘以连接断开的轮廓
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        edges = cv2.dilate(edges, kernel, iterations=1)
        
        # 查找轮廓
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            area = cv2.contourArea(contour)
            perimeter = cv2.arcLength(contour, True)
            
            if area < 20 or perimeter == 0:
                continue
            
            # 圆形度检查
            circularity = 4 * np.pi * area / (perimeter * perimeter)
            if circularity < 0.3:
                continue
            
            # 尺寸检查
            (x, y), radius = cv2.minEnclosingCircle(contour)
            if radius < expected_radius * 0.3 or radius > expected_radius * 3:
                continue
            
            center = (int(x), int(y))
            radius = int(radius)
            
            if self._is_valid_hole_position(center, radius, dish):
                holes.append(Colony(
                    center=center,
                    radius=radius,
                    contour=contour,
                    substance_type=SubstanceTypeEnum.HOLE,
                    detection_score=circularity * 0.8
                ))
        
        return holes

    def _detect_holes_hough(self, image: np.ndarray, dish: PetriDish, expected_radius: int) -> List[Colony]:
        """基于霍夫圆的挖孔检测"""
        holes = []
        
        # 多组霍夫参数，专门针对小圆
        param_sets = [
            {'param1': 30, 'param2': 12, 'minRadius': max(3, expected_radius//2), 'maxRadius': expected_radius*2},
            {'param1': 25, 'param2': 10, 'minRadius': max(2, expected_radius//3), 'maxRadius': expected_radius*3},
            {'param1': 35, 'param2': 15, 'minRadius': max(4, int(expected_radius*0.6)), 'maxRadius': int(expected_radius*1.5)}
        ]
        
        for params in param_sets:
            circles = cv2.HoughCircles(
                image,
                cv2.HOUGH_GRADIENT,
                dp=1.0,
                minDist=max(10, expected_radius//2),
                **params
            )
            
            if circles is not None:
                for x, y, r in circles[0,:]:
                    center = (int(x), int(y))
                    radius = int(r)
                    
                    if self._is_valid_hole_position(center, radius, dish):
                        holes.append(Colony(
                            center=center,
                            radius=radius,
                            contour=self._create_circle_contour(center, radius),
                            substance_type=SubstanceTypeEnum.HOLE,
                            detection_score=0.7
                        ))
        
        return holes

    def _is_valid_hole_position(self, center: Tuple[int, int], radius: int, dish: PetriDish) -> bool:
        """验证挖孔位置的有效性"""
        x, y = center
        
        # 必须在培养皿内
        distance_to_center = np.sqrt((x - dish.center[0])**2 + (y - dish.center[1])**2)
        if distance_to_center + radius > dish.radius * 0.85:
            return False
        
        # 尺寸合理性
        expected_radius = int(self.hole_diameter_mm * self.px_per_mm / 2)
        if radius < expected_radius * 0.2 or radius > expected_radius * 5:
            return False
        
        return True

    def _filter_holes_vs_bubbles(self, holes: List[Colony], image: np.ndarray, dish: PetriDish) -> List[Colony]:
        """区分真实挖孔和气泡干扰"""
        validated = []
        
        for hole in holes:
            # 气泡特征检测
            bubble_score = self._calculate_bubble_score(hole, image)
            hole_score = self._calculate_hole_score(hole, image)
            
            # 如果更像挖孔而不是气泡，则保留
            if hole_score > bubble_score:
                hole.detection_score = hole_score
                validated.append(hole)
        
        return validated

    def _calculate_bubble_score(self, colony: Colony, image: np.ndarray) -> float:
        """计算气泡特征得分（越高越像气泡）"""
        x, y = colony.center
        r = colony.radius
        
        # 创建检测区域
        mask = np.zeros(image.shape[:2], dtype=np.uint8)
        cv2.circle(mask, (x, y), r, 255, -1)
        roi_pixels = image[mask == 255]
        
        if roi_pixels.size < 5:
            return 1.0  # 无法分析，认为是气泡
        
        bubble_score = 0.0
        
        # 1. 气泡通常有很高的亮度变化（不均匀）
        std_dev = np.std(roi_pixels)
        if std_dev > 30:
            bubble_score += 0.4
        
        # 2. 气泡边缘通常有高对比度环
        edge_contrast = self._calculate_edge_contrast(image, (x, y), r)
        if edge_contrast > 40:
            bubble_score += 0.3
        
        # 3. 气泡通常是亮点而不是暗点
        mean_brightness = np.mean(roi_pixels)
        image_mean = np.mean(image[image > 0])
        if mean_brightness > image_mean + 20:
            bubble_score += 0.3
        
        return bubble_score

    def _calculate_hole_score(self, colony: Colony, image: np.ndarray) -> float:
        """计算挖孔特征得分（越高越像挖孔）"""
        x, y = colony.center
        r = colony.radius
        
        mask = np.zeros(image.shape[:2], dtype=np.uint8)
        cv2.circle(mask, (x, y), r, 255, -1)
        roi_pixels = image[mask == 255]
        
        if roi_pixels.size < 5:
            return 0.0
        
        hole_score = 0.0
        
        # 1. 挖孔内部应该相对均匀
        std_dev = np.std(roi_pixels)
        if std_dev < 20:
            hole_score += 0.4
        
        # 2. 挖孔应该比周围稍暗或相似
        mean_brightness = np.mean(roi_pixels)
        ring_brightness = self._get_ring_brightness(image, (x, y), r)
        brightness_diff = ring_brightness - mean_brightness
        if -10 <= brightness_diff <= 30:  # 允许挖孔稍暗或相似
            hole_score += 0.3
        
        # 3. 尺寸匹配性
        expected_radius = int(self.hole_diameter_mm * self.px_per_mm / 2)
        size_diff = abs(r - expected_radius) / expected_radius
        if size_diff < 0.5:
            hole_score += 0.3
        
        return hole_score

    def _calculate_edge_contrast(self, image: np.ndarray, center: Tuple[int, int], radius: int) -> float:
        """计算边缘对比度"""
        x, y = center
        angles = np.linspace(0, 2*np.pi, 16)
        contrasts = []
        
        for angle in angles:
            inner_x = int(x + (radius-2) * np.cos(angle))
            inner_y = int(y + (radius-2) * np.sin(angle))
            outer_x = int(x + (radius+2) * np.cos(angle))
            outer_y = int(y + (radius+2) * np.sin(angle))
            
            if (0 <= inner_x < image.shape[1] and 0 <= inner_y < image.shape[0] and
                0 <= outer_x < image.shape[1] and 0 <= outer_y < image.shape[0]):
                contrast = abs(int(image[inner_y, inner_x]) - int(image[outer_y, outer_x]))
                contrasts.append(contrast)
        
        return np.mean(contrasts) if contrasts else 0.0

    def _get_ring_brightness(self, image: np.ndarray, center: Tuple[int, int], radius: int) -> float:
        """获取环形区域的平均亮度"""
        x, y = center
        ring_mask = np.zeros(image.shape[:2], dtype=np.uint8)
        cv2.circle(ring_mask, (x, y), radius + 8, 255, -1)
        cv2.circle(ring_mask, (x, y), radius, 0, -1)
        
        ring_pixels = image[ring_mask == 255]
        return np.mean(ring_pixels) if ring_pixels.size > 0 else 0.0

    def _select_best_holes(self, holes: List[Colony], target_count: int = 4) -> List[Colony]:
        """选择最佳的挖孔结果"""
        if not holes:
            return []
        
        # 去重：合并相近的检测
        merged_holes = self._merge_nearby_detections(holes)
        
        # 按得分排序
        merged_holes.sort(key=lambda h: h.detection_score, reverse=True)
        
        # 选择前target_count个最佳结果
        return merged_holes[:target_count]

    def _merge_nearby_detections(self, holes: List[Colony]) -> List[Colony]:
        """合并相近的检测结果"""
        if not holes:
            return []
        
        merged = []
        used = set()
        
        for i, hole in enumerate(holes):
            if i in used:
                continue
            
            # 查找相近的检测
            nearby = [hole]
            for j, other in enumerate(holes[i+1:], i+1):
                if j in used:
                    continue
                
                distance = np.sqrt((hole.center[0] - other.center[0])**2 + 
                                 (hole.center[1] - other.center[1])**2)
                
                if distance < max(hole.radius, other.radius) * 1.2:
                    nearby.append(other)
                    used.add(j)
            
            # 选择最佳的作为代表
            best = max(nearby, key=lambda h: h.detection_score)
            merged.append(best)
            used.add(i)
        
        return merged

    def detect_filter_papers_final(self, image: np.ndarray, dish: PetriDish) -> List[Colony]:
        """最终优化的滤纸片检测 - 目标：准确检测3个滤纸片"""
        logger.info("开始最终优化滤纸片检测")
        
        if self.px_per_mm is None:
            return []
        
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # 限制搜索区域
        dish_mask = np.zeros(gray.shape[:2], dtype=np.uint8)
        cv2.circle(dish_mask, dish.center, int(dish.radius * 0.9), 255, -1)
        masked_gray = cv2.bitwise_and(gray, gray, mask=dish_mask)
        
        papers = []
        
        # 预期滤纸片尺寸
        expected_radius = int(self.filter_paper_diameter_mm * self.px_per_mm / 2)
        
        # 策略1: 基于亮度的精确检测
        papers.extend(self._detect_papers_brightness_precise(masked_gray, dish, expected_radius))
        
        # 策略2: 基于霍夫圆的精确检测
        papers.extend(self._detect_papers_hough_precise(masked_gray, dish, expected_radius))
        
        # 策略3: 基于轮廓的检测
        papers.extend(self._detect_papers_contours_precise(masked_gray, dish, expected_radius))
        
        # 精确验证和过滤
        validated_papers = self._validate_papers_strict(papers, masked_gray, dish)
        
        # 选择最佳结果（目标3个）
        final_papers = self._select_best_papers(validated_papers, target_count=3)
        
        logger.info(f"滤纸片最终检测: {len(final_papers)} 个")
        return final_papers

    def _detect_papers_brightness_precise(self, image: np.ndarray, dish: PetriDish, expected_radius: int) -> List[Colony]:
        """基于亮度的精确滤纸片检测"""
        papers = []
        
        # 计算动态阈值
        image_stats = image[image > 0]
        mean_val = np.mean(image_stats)
        std_val = np.std(image_stats)
        
        # 滤纸片应该明显比背景亮
        bright_threshold = mean_val + 1.2 * std_val
        
        # 二值化
        _, binary = cv2.threshold(image, bright_threshold, 255, cv2.THRESH_BINARY)
        
        # 形态学操作 - 保持滤纸片的圆形特征
        kernel_size = max(3, expected_radius // 6)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
        
        # 去除小噪声
        binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel, iterations=1)
        # 填充内部孔洞
        binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel, iterations=2)
        
        # 查找轮廓
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            area = cv2.contourArea(contour)
            expected_area = np.pi * (expected_radius ** 2)
            
            # 面积筛选 - 更严格
            if area < expected_area * 0.3 or area > expected_area * 4:
                continue
            
            # 圆形度检查
            perimeter = cv2.arcLength(contour, True)
            if perimeter == 0:
                continue
            
            circularity = 4 * np.pi * area / (perimeter * perimeter)
            if circularity < 0.5:  # 要求较高的圆形度
                continue
            
            # 拟合圆
            (x, y), radius = cv2.minEnclosingCircle(contour)
            center = (int(x), int(y))
            radius = int(radius)
            
            # 位置和尺寸验证
            if self._is_valid_paper_position(center, radius, dish, expected_radius):
                papers.append(Colony(
                    center=center,
                    radius=radius,
                    contour=contour,
                    substance_type=SubstanceTypeEnum.FILTER_PAPER,
                    detection_score=circularity * 0.8 + 0.2
                ))
        
        return papers

    def _detect_papers_hough_precise(self, image: np.ndarray, dish: PetriDish, expected_radius: int) -> List[Colony]:
        """基于霍夫圆的精确滤纸片检测"""
        papers = []
        
        # 针对滤纸片的多组精确参数
        param_sets = [
            {
                'param1': 50, 'param2': 20, 
                'minRadius': max(5, int(expected_radius * 0.5)), 
                'maxRadius': int(expected_radius * 2.0)
            },
            {
                'param1': 40, 'param2': 18, 
                'minRadius': max(4, int(expected_radius * 0.6)), 
                'maxRadius': int(expected_radius * 1.8)
            },
            {
                'param1': 60, 'param2': 25, 
                'minRadius': max(6, int(expected_radius * 0.7)), 
                'maxRadius': int(expected_radius * 1.5)
            }
        ]
        
        for params in param_sets:
            circles = cv2.HoughCircles(
                image,
                cv2.HOUGH_GRADIENT,
                dp=1.0,
                minDist=max(15, expected_radius),
                **params
            )
            
            if circles is not None:
                for x, y, r in circles[0,:]:
                    center = (int(x), int(y))
                    radius = int(r)
                    
                    if self._is_valid_paper_position(center, radius, dish, expected_radius):
                        papers.append(Colony(
                            center=center,
                            radius=radius,
                            contour=self._create_circle_contour(center, radius),
                            substance_type=SubstanceTypeEnum.FILTER_PAPER,
                            detection_score=0.7
                        ))
        
        return papers

    def _detect_papers_contours_precise(self, image: np.ndarray, dish: PetriDish, expected_radius: int) -> List[Colony]:
        """基于轮廓的精确滤纸片检测"""
        papers = []
        
        # 使用自适应阈值突出亮区域
        adaptive = cv2.adaptiveThreshold(
            image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 15, -5
        )
        
        # 查找轮廓
        contours, _ = cv2.findContours(adaptive, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            area = cv2.contourArea(contour)
            expected_area = np.pi * (expected_radius ** 2)
            
            # 严格的面积筛选
            if area < expected_area * 0.4 or area > expected_area * 3:
                continue
            
            # 轮廓质量检查
            perimeter = cv2.arcLength(contour, True)
            if perimeter == 0:
                continue
            
            circularity = 4 * np.pi * area / (perimeter * perimeter)
            if circularity < 0.6:  # 高圆形度要求
                continue
            
            (x, y), radius = cv2.minEnclosingCircle(contour)
            center = (int(x), int(y))
            radius = int(radius)
            
            if self._is_valid_paper_position(center, radius, dish, expected_radius):
                papers.append(Colony(
                    center=center,
                    radius=radius,
                    contour=contour,
                    substance_type=SubstanceTypeEnum.FILTER_PAPER,
                    detection_score=circularity * 0.9
                ))
        
        return papers

    def _is_valid_paper_position(self, center: Tuple[int, int], radius: int, 
                                dish: PetriDish, expected_radius: int) -> bool:
        """验证滤纸片位置的有效性"""
        x, y = center
        
        # 必须在培养皿内
        distance_to_center = np.sqrt((x - dish.center[0])**2 + (y - dish.center[1])**2)
        if distance_to_center + radius > dish.radius * 0.85:
            return False
        
        # 尺寸合理性 - 更严格
        if radius < expected_radius * 0.4 or radius > expected_radius * 2.5:
            return False
        
        return True

    def _validate_papers_strict(self, papers: List[Colony], image: np.ndarray, dish: PetriDish) -> List[Colony]:
        """严格验证滤纸片特征"""
        validated = []
        
        for paper in papers:
            # 亮度验证 - 滤纸片必须明显比周围亮
            if self._validate_paper_brightness_strict(paper, image):
                validated.append(paper)
        
        return validated

    def _validate_paper_brightness_strict(self, paper: Colony, image: np.ndarray) -> bool:
        """严格验证滤纸片亮度特征"""
        x, y = paper.center
        r = paper.radius
        
        # 滤纸片区域
        paper_mask = np.zeros(image.shape[:2], dtype=np.uint8)
        cv2.circle(paper_mask, (x, y), r, 255, -1)
        paper_pixels = image[paper_mask == 255]
        
        if paper_pixels.size < 5:
            return False
        
        # 周围环形区域
        ring_mask = np.zeros(image.shape[:2], dtype=np.uint8)
        cv2.circle(ring_mask, (x, y), int(r * 2.5), 255, -1)
        cv2.circle(ring_mask, (x, y), r, 0, -1)
        ring_pixels = image[ring_mask == 255]
        
        if ring_pixels.size < 10:
            return False
        
        paper_mean = np.mean(paper_pixels)
        ring_mean = np.mean(ring_pixels)
        
        # 滤纸片必须比周围亮至少20个灰度级
        brightness_diff = paper_mean - ring_mean
        if brightness_diff < 20:
            return False
        
        # 滤纸片内部应该相对均匀
        paper_std = np.std(paper_pixels)
        if paper_std > 15:
            return False
        
        return True

    def _select_best_papers(self, papers: List[Colony], target_count: int = 3) -> List[Colony]:
        """选择最佳的滤纸片结果"""
        if not papers:
            return []
        
        # 去重
        merged_papers = self._merge_nearby_detections(papers)
        
        # 按检测得分排序
        merged_papers.sort(key=lambda p: p.detection_score, reverse=True)
        
        # 选择前target_count个最佳结果
        return merged_papers[:target_count]

    def _create_circle_contour(self, center: Tuple[int, int], radius: int) -> np.ndarray:
        """创建圆形轮廓"""
        angles = np.linspace(0, 2*np.pi, 32)
        points = []
        for angle in angles:
            x = int(center[0] + radius * np.cos(angle))
            y = int(center[1] + radius * np.sin(angle))
            points.append([x, y])
        return np.array(points, dtype=np.int32)