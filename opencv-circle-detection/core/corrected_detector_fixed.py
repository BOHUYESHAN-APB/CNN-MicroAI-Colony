import cv2
import numpy as np
from typing import List, Optional, Tuple, Dict
from enum import Enum
try:
    from .models import Colony, PetriDish, SubstanceTypeEnum
except ImportError:
    # 如果无法导入，提供基本的替代类
    class SubstanceTypeEnum:
        HOLE = "HOLE"
        FILTER_PAPER = "FILTER_PAPER"
    
    class Colony:
        def __init__(self, center, radius, contour=None, substance_type=None, detection_score=0.5):
            self.center = center
            self.radius = radius
            self.contour = contour
            self.substance_type = substance_type
            self.detection_score = detection_score
    
    class PetriDish:
        def __init__(self, center, radius, diameter_mm=90.0):
            self.center = center
            self.radius = radius
            self.diameter_mm = diameter_mm
from .processor import ImageProcessor
from utils.logger import get_logger

logger = get_logger(__name__)

class CorrectedDetector:
    """基于用户反馈修正的检测器 - 修复版本"""

    def __init__(self, plate_diameter_mm: float = 90.0,
                 filter_paper_diameter_mm: float = 6.0,
                 hole_diameter_mm: float = 6.0):
        self.plate_diameter_mm = plate_diameter_mm
        self.filter_paper_diameter_mm = filter_paper_diameter_mm
        self.hole_diameter_mm = hole_diameter_mm
        self.processor = ImageProcessor()
        self.px_per_mm = None

    def detect_petri_dishes_robust(self, image: np.ndarray) -> List[PetriDish]:
        """更稳健的培养皿检测 - 修复版本"""
        logger.info("开始稳健培养皿检测")
        
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # 简化的检测策略，避免过度复杂
        preprocessed_images = []
        
        # 1. 标准预处理
        standard = self.processor.preprocess(gray)
        preprocessed_images.append(('standard', standard))
        
        # 2. 强对比度增强
        clahe_strong = cv2.createCLAHE(clipLimit=4.0, tileGridSize=(8, 8))
        enhanced_strong = clahe_strong.apply(gray)
        preprocessed_images.append(('enhanced_strong', enhanced_strong))
        
        all_circles = []
        
        # 简化的参数集合
        param_sets = [
            {
                'dp': 1.0,
                'minDist': max(200, image.shape[0]//4),
                'param1': 50,
                'param2': 30,
                'minRadius': int(image.shape[0]/5),
                'maxRadius': int(image.shape[0]/1.8)
            },
            {
                'dp': 1.2,
                'minDist': max(150, image.shape[0]//5),
                'param1': 40,
                'param2': 25,
                'minRadius': int(image.shape[0]/4),
                'maxRadius': int(image.shape[0]/1.6)
            }
        ]
        
        for name, proc_img in preprocessed_images:
            for i, params in enumerate(param_sets):
                circles = cv2.HoughCircles(
                    proc_img,
                    cv2.HOUGH_GRADIENT,
                    **params
                )
                
                if circles is not None:
                    logger.info(f"{name} 预处理 + 参数组{i+1}: 检测到 {len(circles[0])} 个圆")
                    for x, y, r in circles[0,:]:
                        # 计算质量分数
                        score = self._calculate_dish_quality_score(gray, (int(x), int(y)), int(r))
                        all_circles.append((x, y, r, f"{name}_param{i+1}", score))
        
        if not all_circles:
            logger.warning("所有方法都未检测到培养皿")
            return []
        
        # 更简单的圆合并策略
        merged_circles = self._simple_circle_merge(all_circles)
        
        plates = []
        for x, y, r, source, score in merged_circles:
            if self._validate_dish_circle_strict(gray, (int(x), int(y)), int(r)):
                plates.append(PetriDish(
                    center=(int(x), int(y)),
                    radius=int(r),
                    diameter_mm=self.plate_diameter_mm
                ))
                self.px_per_mm = r * 2 / self.plate_diameter_mm
                logger.info(f"验证通过的培养皿: 中心({int(x)},{int(y)}), 半径{int(r)}px, 得分{score:.2f}")
                break  # 只取第一个最好的
        
        logger.info(f"最终检测到 {len(plates)} 个有效培养皿")
        return plates

    def _simple_circle_merge(self, circles: List[Tuple]) -> List[Tuple]:
        """简化的圆合并策略"""
        if not circles:
            return []
        
        # 按质量分数排序
        circles.sort(key=lambda c: c[4], reverse=True)
        
        merged = []
        used = set()
        
        for i, (x1, y1, r1, source1, score1) in enumerate(circles):
            if i in used:
                continue
            
            # 寻找相近的圆
            similar_circles = [(x1, y1, r1, source1, score1)]
            
            for j, (x2, y2, r2, source2, score2) in enumerate(circles[i+1:], i+1):
                if j in used:
                    continue
                
                distance = np.sqrt((x1 - x2)**2 + (y1 - y2)**2)
                
                # 如果圆很相近，则合并
                if distance < max(r1, r2) * 0.5:
                    similar_circles.append((x2, y2, r2, source2, score2))
                    used.add(j)
            
            # 加权平均计算合并后的圆
            if len(similar_circles) > 1:
                weights = [c[4] for c in similar_circles]
                total_weight = sum(weights)
                
                if total_weight > 0 and not np.isnan(total_weight):
                    avg_x = sum(c[0] * c[4] for c in similar_circles) / total_weight
                    avg_y = sum(c[1] * c[4] for c in similar_circles) / total_weight
                    avg_r = sum(c[2] * c[4] for c in similar_circles) / total_weight
                    avg_score = total_weight / len(similar_circles)
                else:
                    # 如果权重有问题，使用简单平均
                    avg_x = sum(c[0] for c in similar_circles) / len(similar_circles)
                    avg_y = sum(c[1] for c in similar_circles) / len(similar_circles)
                    avg_r = sum(c[2] for c in similar_circles) / len(similar_circles)
                    avg_score = sum(c[4] for c in similar_circles) / len(similar_circles)
                
                # 检查结果是否有效
                if not (np.isnan(avg_x) or np.isnan(avg_y) or np.isnan(avg_r)):
                    sources = [c[3] for c in similar_circles]
                    merged_source = f"merged({len(sources)})"
                    merged.append((avg_x, avg_y, avg_r, merged_source, avg_score))
            else:
                merged.append((x1, y1, r1, source1, score1))
            
            used.add(i)
            
            # 限制合并数量，避免过多结果
            if len(merged) >= 3:
                break
        
        return merged

    def _calculate_dish_quality_score(self, image: np.ndarray, center: Tuple[int, int], radius: int) -> float:
        """计算培养皿检测的质量分数"""
        x, y = center
        h, w = image.shape[:2]
        
        score = 0.0
        
        # 1. 边界完整性检查
        if x - radius >= 0 and x + radius < w and y - radius >= 0 and y + radius < h:
            score += 0.4
        else:
            return 0.0  # 如果超出边界，直接返回0分
        
        # 2. 尺寸合理性检查
        expected_radius_range = (min(h, w) // 6, min(h, w) // 2)
        if expected_radius_range[0] <= radius <= expected_radius_range[1]:
            score += 0.3
        
        # 3. 简化的边缘检查
        try:
            angles = np.linspace(0, 2*np.pi, 16)
            edge_gradients = []
            
            for angle in angles:
                inner_x = int(x + (radius - 2) * np.cos(angle))
                inner_y = int(y + (radius - 2) * np.sin(angle))
                outer_x = int(x + (radius + 2) * np.cos(angle))
                outer_y = int(y + (radius + 2) * np.sin(angle))
                
                if (0 <= inner_x < w and 0 <= inner_y < h and 
                    0 <= outer_x < w and 0 <= outer_y < h):
                    gradient = abs(int(image[inner_y, inner_x]) - int(image[outer_y, outer_x]))
                    edge_gradients.append(gradient)
            
            if edge_gradients:
                avg_gradient = np.mean(edge_gradients)
                gradient_score = min(avg_gradient / 30.0, 1.0)
                score += gradient_score * 0.3
        except:
            # 如果计算出错，给默认分数
            score += 0.1
        
        return score

    def _validate_dish_circle_strict(self, image: np.ndarray, center: Tuple[int, int], radius: int) -> bool:
        """严格验证培养皿圆形"""
        x, y = center
        h, w = image.shape[:2]
        
        # 基本边界检查
        if x - radius < 10 or x + radius >= w - 10 or y - radius < 10 or y + radius >= h - 10:
            return False
        
        # 尺寸合理性检查
        min_radius = min(h, w) // 8
        max_radius = min(h, w) // 2
        if not (min_radius <= radius <= max_radius):
            return False
        
        return True

    def detect_transparent_holes_corrected(self, image: np.ndarray, dish: PetriDish) -> List[Colony]:
        """修正的透明挖孔检测"""
        logger.info("开始修正的透明挖孔检测")
        
        if self.px_per_mm is None:
            logger.error("未进行尺寸标定")
            return []
        
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # 创建培养皿掩码
        dish_mask = np.zeros(gray.shape[:2], dtype=np.uint8)
        cv2.circle(dish_mask, dish.center, int(dish.radius * 0.9), 255, -1)
        
        masked_gray = cv2.bitwise_and(gray, gray, mask=dish_mask)
        
        holes = []
        
        # 策略1: 基于暗区域检测
        holes.extend(self._detect_holes_by_dark_regions(masked_gray, dish))
        
        # 策略2: 基于边缘检测
        holes.extend(self._detect_holes_by_edges(masked_gray, dish))
        
        # 过滤和验证
        validated_holes = self._filter_holes(holes, dish)
        
        logger.info(f"透明挖孔检测完成: {len(validated_holes)} 个")
        return validated_holes

    def _detect_holes_by_dark_regions(self, image: np.ndarray, dish: PetriDish) -> List[Colony]:
        """基于暗区域检测孔洞"""
        holes = []
        
        # 计算图像统计
        mean_val = np.mean(image[image > 0])
        std_val = np.std(image[image > 0])
        
        # 寻找比平均值暗的区域
        threshold = mean_val - 0.5 * std_val
        _, binary = cv2.threshold(image, threshold, 255, cv2.THRESH_BINARY_INV)
        
        # 形态学操作
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
        
        # 查找轮廓
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        expected_radius = self.hole_diameter_mm * self.px_per_mm / 2
        
        for contour in contours:
            area = cv2.contourArea(contour)
            expected_area = np.pi * (expected_radius ** 2)
            
            # 面积检查
            if area < expected_area * 0.1 or area > expected_area * 10:
                continue
            
            # 获取外接圆
            (x, y), radius = cv2.minEnclosingCircle(contour)
            center = (int(x), int(y))
            radius = int(radius)
            
            # 位置检查
            distance_to_center = np.sqrt((center[0] - dish.center[0])**2 + 
                                       (center[1] - dish.center[1])**2)
            if distance_to_center + radius > dish.radius * 0.8:
                continue
            
            holes.append(Colony(
                center=center,
                radius=radius,
                contour=contour,
                substance_type=SubstanceTypeEnum.HOLE,
                detection_score=0.5
            ))
        
        return holes

    def _detect_holes_by_edges(self, image: np.ndarray, dish: PetriDish) -> List[Colony]:
        """基于边缘检测孔洞"""
        holes = []
        
        # Canny边缘检测
        edges = cv2.Canny(image, 20, 60)
        
        # 预期孔洞半径
        expected_radius = int(self.hole_diameter_mm * self.px_per_mm / 2)
        
        # 霍夫圆检测
        circles = cv2.HoughCircles(
            edges,
            cv2.HOUGH_GRADIENT,
            dp=1.0,
            minDist=max(20, expected_radius),
            param1=30,
            param2=15,
            minRadius=max(3, int(expected_radius * 0.3)),
            maxRadius=int(expected_radius * 3)
        )
        
        if circles is not None:
            for x, y, r in circles[0,:]:
                center = (int(x), int(y))
                radius = int(r)
                
                # 验证是否在培养皿内
                distance_to_center = np.sqrt((center[0] - dish.center[0])**2 + 
                                           (center[1] - dish.center[1])**2)
                if distance_to_center + radius > dish.radius * 0.8:
                    continue
                
                holes.append(Colony(
                    center=center,
                    radius=radius,
                    contour=self._create_circle_contour(center, radius),
                    substance_type=SubstanceTypeEnum.HOLE,
                    detection_score=0.6
                ))
        
        return holes

    def _filter_holes(self, holes: List[Colony], dish: PetriDish) -> List[Colony]:
        """过滤孔洞检测结果"""
        if not holes:
            return []
        
        # 去重
        filtered = []
        for hole in holes:
            is_duplicate = False
            for existing in filtered:
                distance = np.sqrt((hole.center[0] - existing.center[0])**2 + 
                                 (hole.center[1] - existing.center[1])**2)
                if distance < max(hole.radius, existing.radius) * 1.2:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                filtered.append(hole)
        
        # 按检测得分排序，取前4个（因为预期有4个孔）
        filtered.sort(key=lambda h: h.detection_score, reverse=True)
        return filtered[:6]  # 最多6个，允许一些容错

    def detect_filter_papers_corrected(self, image: np.ndarray, dish: PetriDish) -> List[Colony]:
        """修正的滤纸片检测"""
        logger.info("开始修正的滤纸片检测")
        
        if self.px_per_mm is None:
            logger.error("未进行尺寸标定")
            return []
        
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # 创建培养皿掩码
        dish_mask = np.zeros(gray.shape[:2], dtype=np.uint8)
        cv2.circle(dish_mask, dish.center, int(dish.radius * 0.9), 255, -1)
        
        masked_gray = cv2.bitwise_and(gray, gray, mask=dish_mask)
        
        papers = []
        
        # 策略1: 基于高亮度检测
        papers.extend(self._detect_papers_by_brightness(masked_gray, dish))
        
        # 策略2: 基于霍夫圆检测
        papers.extend(self._detect_papers_by_circles(masked_gray, dish))
        
        # 过滤和验证
        validated_papers = self._filter_papers(papers, dish, masked_gray)
        
        logger.info(f"滤纸片检测完成: {len(validated_papers)} 个")
        return validated_papers

    def _detect_papers_by_brightness(self, image: np.ndarray, dish: PetriDish) -> List[Colony]:
        """基于亮度检测滤纸片"""
        papers = []
        
        # 计算图像统计
        mean_val = np.mean(image[image > 0])
        std_val = np.std(image[image > 0])
        
        # 高亮度阈值
        threshold = mean_val + 1.0 * std_val
        
        # 二值化
        _, binary = cv2.threshold(image, threshold, 255, cv2.THRESH_BINARY)
        
        # 形态学操作
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
        
        # 查找轮廓
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        expected_radius = self.filter_paper_diameter_mm * self.px_per_mm / 2
        
        for contour in contours:
            area = cv2.contourArea(contour)
            expected_area = np.pi * (expected_radius ** 2)
            
            # 面积检查
            if area < expected_area * 0.2 or area > expected_area * 5:
                continue
            
            # 获取外接圆
            (x, y), radius = cv2.minEnclosingCircle(contour)
            center = (int(x), int(y))
            radius = int(radius)
            
            papers.append(Colony(
                center=center,
                radius=radius,
                contour=contour,
                substance_type=SubstanceTypeEnum.FILTER_PAPER,
                detection_score=0.7
            ))
        
        return papers

    def _detect_papers_by_circles(self, image: np.ndarray, dish: PetriDish) -> List[Colony]:
        """基于霍夫圆检测滤纸片"""
        papers = []
        
        # 预期滤纸片半径
        expected_radius = int(self.filter_paper_diameter_mm * self.px_per_mm / 2)
        
        # 霍夫圆检测
        circles = cv2.HoughCircles(
            image,
            cv2.HOUGH_GRADIENT,
            dp=1.0,
            minDist=max(20, expected_radius),
            param1=50,
            param2=20,
            minRadius=max(5, int(expected_radius * 0.5)),
            maxRadius=int(expected_radius * 2)
        )
        
        if circles is not None:
            for x, y, r in circles[0,:]:
                center = (int(x), int(y))
                radius = int(r)
                
                papers.append(Colony(
                    center=center,
                    radius=radius,
                    contour=self._create_circle_contour(center, radius),
                    substance_type=SubstanceTypeEnum.FILTER_PAPER,
                    detection_score=0.6
                ))
        
        return papers

    def _filter_papers(self, papers: List[Colony], dish: PetriDish, image: np.ndarray) -> List[Colony]:
        """过滤滤纸片检测结果"""
        if not papers:
            return []
        
        # 验证每个滤纸片的亮度特征
        validated = []
        for paper in papers:
            if self._validate_paper_brightness(paper, image):
                validated.append(paper)
        
        # 去重
        filtered = []
        for paper in validated:
            is_duplicate = False
            for existing in filtered:
                distance = np.sqrt((paper.center[0] - existing.center[0])**2 + 
                                 (paper.center[1] - existing.center[1])**2)
                if distance < max(paper.radius, existing.radius) * 1.2:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                filtered.append(paper)
        
        # 按检测得分排序
        filtered.sort(key=lambda p: p.detection_score, reverse=True)
        return filtered[:5]  # 最多5个

    def _validate_paper_brightness(self, paper: Colony, image: np.ndarray) -> bool:
        """验证滤纸片亮度特征"""
        x, y = paper.center
        r = paper.radius
        
        # 创建滤纸片区域掩码
        mask = np.zeros(image.shape[:2], dtype=np.uint8)
        cv2.circle(mask, (x, y), r, 255, -1)
        
        paper_pixels = image[mask == 255]
        if paper_pixels.size < 5:
            return False
        
        # 获取周围区域
        ring_mask = np.zeros(image.shape[:2], dtype=np.uint8)
        cv2.circle(ring_mask, (x, y), int(r * 1.8), 255, -1)
        cv2.circle(ring_mask, (x, y), r, 0, -1)
        
        ring_pixels = image[ring_mask == 255]
        if ring_pixels.size < 10:
            return False
        
        paper_mean = np.mean(paper_pixels)
        ring_mean = np.mean(ring_pixels)
        
        # 滤纸片应该比周围亮
        brightness_diff = paper_mean - ring_mean
        return brightness_diff > 10

    def _create_circle_contour(self, center: Tuple[int, int], radius: int) -> np.ndarray:
        """创建圆形轮廓"""
        angles = np.linspace(0, 2*np.pi, 32)
        points = []
        for angle in angles:
            x = int(center[0] + radius * np.cos(angle))
            y = int(center[1] + radius * np.sin(angle))
            points.append([x, y])
        return np.array(points, dtype=np.int32)