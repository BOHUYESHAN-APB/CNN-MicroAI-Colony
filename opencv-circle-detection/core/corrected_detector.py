import cv2
import numpy as np
from typing import List, Optional, Tuple, Dict
from enum import Enum
from .models import Colony, PetriDish, SubstanceTypeEnum
from .processor import ImageProcessor
from utils.logger import get_logger

logger = get_logger(__name__)

class CorrectedDetector:
    """基于用户反馈修正的检测器"""

    def __init__(self, plate_diameter_mm: float = 90.0,
                 filter_paper_diameter_mm: float = 6.0,
                 hole_diameter_mm: float = 6.0):
        self.plate_diameter_mm = plate_diameter_mm
        self.filter_paper_diameter_mm = filter_paper_diameter_mm
        self.hole_diameter_mm = hole_diameter_mm
        self.processor = ImageProcessor()
        self.px_per_mm = None

    def detect_petri_dishes_robust(self, image: np.ndarray) -> List[PetriDish]:
        """更稳健的培养皿检测"""
        logger.info("开始稳健培养皿检测")
        
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # 多种预处理策略，特别针对低对比度图像
        preprocessed_images = []
        
        # 1. 标准预处理
        standard = self.processor.preprocess(gray)
        preprocessed_images.append(('standard', standard))
        
        # 2. 强对比度增强
        clahe_strong = cv2.createCLAHE(clipLimit=4.0, tileGridSize=(8, 8))
        enhanced_strong = clahe_strong.apply(gray)
        preprocessed_images.append(('enhanced_strong', enhanced_strong))
        
        # 3. 边缘增强
        edges = cv2.Canny(gray, 30, 80)
        edge_enhanced = cv2.addWeighted(gray, 0.7, edges, 0.3, 0)
        preprocessed_images.append(('edge_enhanced', edge_enhanced))
        
        # 4. 形态学增强
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        morph_enhanced = cv2.morphologyEx(gray, cv2.MORPH_GRADIENT, kernel)
        morph_combined = cv2.addWeighted(gray, 0.8, morph_enhanced, 0.2, 0)
        preprocessed_images.append(('morph_enhanced', morph_combined))
        
        all_circles = []
        
        # 对每种预处理图像使用多组参数
        param_sets = [
            # 保守参数 - 针对清晰边界
            {
                'dp': 1.0,
                'minDist': max(200, image.shape[0]//4),
                'param1': 50,
                'param2': 40,
                'minRadius': int(image.shape[0]/5),
                'maxRadius': int(image.shape[0]/1.5)
            },
            # 中等参数 - 平衡检测
            {
                'dp': 1.2,
                'minDist': max(150, image.shape[0]//5),
                'param1': 40,
                'param2': 30,
                'minRadius': int(image.shape[0]/4),
                'maxRadius': int(image.shape[0]/1.8)
            },
            # 激进参数 - 针对低对比度
            {
                'dp': 1.5,
                'minDist': max(100, image.shape[0]//6),
                'param1': 30,
                'param2': 20,
                'minRadius': int(image.shape[0]/3.5),
                'maxRadius': int(image.shape[0]/1.6)
            },
            # 超激进参数 - 针对极低对比度
            {
                'dp': 2.0,
                'minDist': max(80, image.shape[0]//8),
                'param1': 20,
                'param2': 15,
                'minRadius': int(image.shape[0]/4),
                'maxRadius': int(image.shape[0]/1.4)
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
                        all_circles.append((x, y, r, f"{name}_param{i+1}"))
        
        if not all_circles:
            logger.warning("所有方法都未检测到培养皿")
            return []
        
        # 更智能的圆合并和验证
        merged_circles = self._intelligent_circle_merge(all_circles, gray)
        
        plates = []
        for x, y, r, source in merged_circles:
            if self._validate_dish_circle_strict(gray, (int(x), int(y)), int(r)):
                plates.append(PetriDish(
                    center=(int(x), int(y)),
                    radius=int(r),
                    diameter_mm=self.plate_diameter_mm
                ))
                self.px_per_mm = r * 2 / self.plate_diameter_mm
                logger.info(f"验证通过的培养皿: 中心({int(x)},{int(y)}), 半径{int(r)}px, 来源{source}")
        
        logger.info(f"最终检测到 {len(plates)} 个有效培养皿")
        return plates

    def _intelligent_circle_merge(self, circles: List[Tuple], image: np.ndarray) -> List[Tuple]:
        """智能圆合并，考虑检测质量"""
        if not circles:
            return []
        
        # 为每个圆计算质量分数
        scored_circles = []
        for x, y, r, source in circles:
            score = self._calculate_dish_quality_score(image, (int(x), int(y)), int(r))
            scored_circles.append((x, y, r, source, score))
        
        # 按质量排序
        scored_circles.sort(key=lambda c: c[4], reverse=True)
        
        # 智能合并相近的圆
        merged = []
        used = set()
        
        for i, (x1, y1, r1, source1, score1) in enumerate(scored_circles):
            if i in used:
                continue
            
            # 寻找相近的圆
            similar_circles = [(x1, y1, r1, source1, score1)]
            total_weight = score1
            
            for j, (x2, y2, r2, source2, score2) in enumerate(scored_circles[i+1:], i+1):
                if j in used:
                    continue
                
                distance = np.sqrt((x1 - x2)**2 + (y1 - y2)**2)
                radius_diff = abs(r1 - r2)
                
                # 如果圆很相近，则合并
                if distance < max(r1, r2) * 0.3 and radius_diff < max(r1, r2) * 0.2:
                    similar_circles.append((x2, y2, r2, source2, score2))
                    total_weight += score2
                    used.add(j)
            
            # 加权平均计算合并后的圆
            if len(similar_circles) > 1:
                weights = [c[4] for c in similar_circles]
                total_weight = sum(weights)
                
                avg_x = sum(c[0] * c[4] for c in similar_circles) / total_weight
                avg_y = sum(c[1] * c[4] for c in similar_circles) / total_weight
                avg_r = sum(c[2] * c[4] for c in similar_circles) / total_weight
                
                sources = [c[3] for c in similar_circles]
                merged_source = f"merged({','.join(sources)})"
                
                merged.append((avg_x, avg_y, avg_r, merged_source))
            else:
                merged.append((x1, y1, r1, source1))
            
            used.add(i)
        
        return merged

    def _calculate_dish_quality_score(self, image: np.ndarray, center: Tuple[int, int], radius: int) -> float:
        """计算培养皿检测的质量分数"""
        x, y = center
        h, w = image.shape[:2]
        
        score = 0.0
        
        # 1. 边界完整性检查
        if x - radius >= 0 and x + radius < w and y - radius >= 0 and y + radius < h:
            score += 0.3
        else:
            return 0.0  # 如果超出边界，直接返回0分
        
        # 2. 圆周强度变化检查（培养皿边缘应该有明显对比度）
        angles = np.linspace(0, 2*np.pi, 32)
        edge_gradients = []
        
        for angle in angles:
            # 在圆周附近采样内外两点
            inner_x = int(x + (radius - 3) * np.cos(angle))
            inner_y = int(y + (radius - 3) * np.sin(angle))
            outer_x = int(x + (radius + 3) * np.cos(angle))
            outer_y = int(y + (radius + 3) * np.sin(angle))
            
            if (0 <= inner_x < w and 0 <= inner_y < h and 
                0 <= outer_x < w and 0 <= outer_y < h):
                gradient = abs(int(image[inner_y, inner_x]) - int(image[outer_y, outer_x]))
                edge_gradients.append(gradient)
        
        if edge_gradients:
            avg_gradient = np.mean(edge_gradients)
            gradient_score = min(avg_gradient / 50.0, 1.0)  # 归一化到0-1
            score += gradient_score * 0.4
        
        # 3. 尺寸合理性检查
        expected_radius_range = (min(h, w) // 6, min(h, w) // 2)
        if expected_radius_range[0] <= radius <= expected_radius_range[1]:
            size_score = 1.0
        else:
            size_score = max(0, 1 - abs(radius - np.mean(expected_radius_range)) / expected_radius_range[1])
        score += size_score * 0.3
        
        return score

    def _validate_dish_circle_strict(self, image: np.ndarray, center: Tuple[int, int], radius: int) -> bool:
        """严格验证培养皿圆形"""
        x, y = center
        h, w = image.shape[:2]
        
        # 基本边界检查
        if x - radius < 0 or x + radius >= w or y - radius < 0 or y + radius >= h:
            return False
        
        # 尺寸合理性检查 - 更严格
        min_radius = min(h, w) // 8
        max_radius = min(h, w) // 2
        if not (min_radius <= radius <= max_radius):
            return False
        
        # 圆周强度一致性检查
        angles = np.linspace(0, 2*np.pi, 24)
        edge_intensities = []
        
        for angle in angles:
            edge_x = int(x + radius * np.cos(angle))
            edge_y = int(y + radius * np.sin(angle))
            if 0 <= edge_x < w and 0 <= edge_y < h:
                edge_intensities.append(image[edge_y, edge_x])
        
        if len(edge_intensities) < 20:
            return False
        
        # 边缘强度的标准差应该在合理范围内
        edge_std = np.std(edge_intensities)
        if edge_std < 5:  # 边缘太平滑，可能不是真实边界
            return False
        if edge_std > 60:  # 边缘变化太剧烈，可能是噪声
            return False
        
        return True

    def detect_transparent_holes_corrected(self, image: np.ndarray, dish: PetriDish) -> List[Colony]:
        """修正的透明挖孔检测 - 专门针对4个透明孔"""
        logger.info("开始修正的透明挖孔检测")
        
        if self.px_per_mm is None:
            logger.error("未进行尺寸标定")
            return []
        
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # 创建培养皿掩码
        dish_mask = np.zeros(gray.shape[:2], dtype=np.uint8)
        cv2.circle(dish_mask, dish.center, int(dish.radius * 0.9), 255, -1)
        
        masked_gray = cv2.bitwise_and(gray, gray, mask=dish_mask)
        
        # 专门的透明孔检测策略
        holes = []
        
        # 策略1: 基于局部最小值检测（透明孔通常比周围暗）
        holes.extend(self._detect_holes_by_local_minima(masked_gray, dish))
        
        # 策略2: 基于边缘检测的圆形查找
        holes.extend(self._detect_holes_by_edge_circles(masked_gray, dish))
        
        # 策略3: 基于模板匹配
        holes.extend(self._detect_holes_by_template_matching(masked_gray, dish))
        
        # 过滤和验证检测结果
        validated_holes = self._validate_and_filter_holes(holes, dish, masked_gray)
        
        logger.info(f"透明挖孔检测完成: {len(validated_holes)} 个")
        return validated_holes

    def _detect_holes_by_local_minima(self, image: np.ndarray, dish: PetriDish) -> List[Colony]:
        """基于局部最小值检测透明孔"""
        holes = []
        
        # 应用高斯模糊减少噪声
        blurred = cv2.GaussianBlur(image, (5, 5), 1)
        
        # 使用形态学操作检测暗区域
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))
        tophat = cv2.morphologyEx(blurred, cv2.MORPH_BLACKHAT, kernel)
        
        # 阈值分割找到暗区域
        _, binary = cv2.threshold(tophat, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # 形态学清理
        kernel_clean = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel_clean)
        binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel_clean)
        
        # 查找轮廓
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            area = cv2.contourArea(contour)
            perimeter = cv2.arcLength(contour, True)
            
            if perimeter == 0:
                continue
            
            # 计算预期孔洞面积
            expected_hole_radius = self.hole_diameter_mm * self.px_per_mm / 2
            expected_area = np.pi * (expected_hole_radius ** 2)
            
            # 面积检查 - 更宽松的范围
            if area < expected_area * 0.2 or area > expected_area * 5:
                continue
            
            # 圆形度检查
            circularity = 4 * np.pi * area / (perimeter * perimeter)
            if circularity < 0.3:  # 放宽圆形度要求
                continue
            
            # 获取外接圆
            (x, y), radius = cv2.minEnclosingCircle(contour)
            center = (int(x), int(y))
            radius = int(radius)
            
            # 检查是否在培养皿内
            distance_to_center = np.sqrt((center[0] - dish.center[0])**2 + 
                                       (center[1] - dish.center[1])**2)
            if distance_to_center + radius > dish.radius * 0.85:
                continue
            
            holes.append(Colony(
                center=center,
                radius=radius,
                contour=contour,
                substance_type=SubstanceTypeEnum.HOLE,
                detection_score=circularity
            ))
        
        return holes

    def _detect_holes_by_edge_circles(self, image: np.ndarray, dish: PetriDish) -> List[Colony]:
        """基于边缘检测的圆形查找"""
        holes = []
        
        # Canny边缘检测
        edges = cv2.Canny(image, 20, 60)
        
        # 预期孔洞半径
        expected_radius = int(self.hole_diameter_mm * self.px_per_mm / 2)
        
        # 霍夫圆检测 - 专门针对小圆
        circles = cv2.HoughCircles(
            edges,
            cv2.HOUGH_GRADIENT,
            dp=1.0,
            minDist=expected_radius,
            param1=30,
            param2=12,  # 降低累积阈值
            minRadius=max(3, int(expected_radius * 0.5)),
            maxRadius=int(expected_radius * 2)
        )
        
        if circles is not None:
            for x, y, r in circles[0,:]:
                center = (int(x), int(y))
                radius = int(r)
                
                # 验证是否在培养皿内
                distance_to_center = np.sqrt((center[0] - dish.center[0])**2 + 
                                           (center[1] - dish.center[1])**2)
                if distance_to_center + radius > dish.radius * 0.85:
                    continue
                
                holes.append(Colony(
                    center=center,
                    radius=radius,
                    contour=self._create_circle_contour(center, radius),
                    substance_type=SubstanceTypeEnum.HOLE,
                    detection_score=0.7
                ))
        
        return holes

    def _detect_holes_by_template_matching(self, image: np.ndarray, dish: PetriDish) -> List[Colony]:
        """基于模板匹配检测孔洞"""
        holes = []
        
        # 创建圆形模板
        template_radius = int(self.hole_diameter_mm * self.px_per_mm / 2)
        template_size = template_radius * 4
        
        template = np.ones((template_size, template_size), dtype=np.uint8) * 255
        cv2.circle(template, (template_size//2, template_size//2), template_radius, 0, -1)
        
        # 模板匹配
        result = cv2.matchTemplate(image, template, cv2.TM_CCOEFF_NORMED)
        
        # 寻找匹配位置
        threshold = 0.3  # 降低阈值以提高检测灵敏度
        locations = np.where(result >= threshold)
        
        for pt in zip(*locations[::-1]):
            center_x = pt[0] + template_size // 2
            center_y = pt[1] + template_size // 2
            center = (center_x, center_y)
            
            # 验证是否在培养皿内
            distance_to_center = np.sqrt((center[0] - dish.center[0])**2 + 
                                       (center[1] - dish.center[1])**2)
            if distance_to_center + template_radius > dish.radius * 0.85:
                continue
            
            holes.append(Colony(
                center=center,
                radius=template_radius,
                contour=self._create_circle_contour(center, template_radius),
                substance_type=SubstanceTypeEnum.HOLE,
                detection_score=result[pt[1], pt[0]]
            ))
        
        return holes

    def _validate_and_filter_holes(self, holes: List[Colony], dish: PetriDish, 
                                  image: np.ndarray) -> List[Colony]:
        """验证和过滤孔洞检测结果"""
        if not holes:
            return []
        
        # 去重：合并相近的检测
        filtered_holes = []
        used = set()
        
        holes.sort(key=lambda h: h.detection_score, reverse=True)
        
        for i, hole in enumerate(holes):
            if i in used:
                continue
            
            # 检查是否与已选择的孔重叠
            is_duplicate = False
            for selected_hole in filtered_holes:
                distance = np.sqrt((hole.center[0] - selected_hole.center[0])**2 + 
                                 (hole.center[1] - selected_hole.center[1])**2)
                if distance < max(hole.radius, selected_hole.radius) * 1.5:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                # 额外验证：检查孔洞区域的特征
                if self._validate_hole_characteristics(hole, image):
                    filtered_holes.append(hole)
                    used.add(i)
            
            # 限制最大检测数量（根据实际应该有4个）
            if len(filtered_holes) >= 6:  # 允许一些误检容错
                break
        
        # 如果检测数量与预期差异很大，尝试调整
        if len(filtered_holes) < 2:
            logger.warning(f"检测到的孔洞数量({len(filtered_holes)})过少，可能需要调整参数")
        elif len(filtered_holes) > 6:
            logger.warning(f"检测到的孔洞数量({len(filtered_holes)})过多，选择前6个最佳结果")
            filtered_holes = filtered_holes[:6]
        
        return filtered_holes

    def _validate_hole_characteristics(self, hole: Colony, image: np.ndarray) -> bool:
        """验证孔洞的特征"""
        x, y = hole.center
        r = hole.radius
        
        # 创建孔洞区域掩码
        mask = np.zeros(image.shape[:2], dtype=np.uint8)
        cv2.circle(mask, (x, y), r, 255, -1)
        
        hole_pixels = image[mask == 255]
        if hole_pixels.size < 5:
            return False
        
        # 获取周围区域作为对比
        ring_mask = np.zeros(image.shape[:2], dtype=np.uint8)
        cv2.circle(ring_mask, (x, y), int(r * 2), 255, -1)
        cv2.circle(ring_mask, (x, y), r, 0, -1)
        
        ring_pixels = image[ring_mask == 255]
        if ring_pixels.size < 10:
            return False
        
        # 透明孔应该比周围区域稍暗或相似
        hole_mean = np.mean(hole_pixels)
        ring_mean = np.mean(ring_pixels)
        
        # 允许孔洞比周围稍亮或稍暗（透明特征）
        brightness_diff = abs(hole_mean - ring_mean)
        if brightness_diff > 30:  # 如果差异太大，可能不是透明孔
            return False
        
        # 孔洞内部应该相对均匀
        hole_std = np.std(hole_pixels)
        if hole_std > 25:  # 内部变化太大
            return False
        
        return True

    def _create_circle_contour(self, center: Tuple[int, int], radius: int) -> np.ndarray:
        """创建圆形轮廓"""
        angles = np.linspace(0, 2*np.pi, 32)
        points = []
        for angle in angles:
            x = int(center[0] + radius * np.cos(angle))
            y = int(center[1] + radius * np.sin(angle))
            points.append([x, y])
        return np.array(points, dtype=np.int32)

    def detect_filter_papers_corrected(self, image: np.ndarray, dish: PetriDish) -> List[Colony]:
        """修正的滤纸片检测 - 基于亮度特征"""
        logger.info("开始修正的滤纸片检测")
        
        if self.px_per_mm is None:
            logger.error("未进行尺寸标定")
            return []
        
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # 创建培养皿掩码
        dish_mask = np.zeros(gray.shape[:2], dtype=np.uint8)
        cv2.circle(dish_mask, dish.center, int(dish.radius * 0.9), 255, -1)
        
        masked_gray = cv2.bitwise_and(gray, gray, mask=dish_mask)
        
        # 滤纸片检测：寻找明显的亮点
        papers = []
        
        # 策略1: 基于亮度阈值
        papers.extend(self._detect_papers_by_brightness(masked_gray, dish))
        
        # 策略2: 基于顶帽变换
        papers.extend(self._detect_papers_by_tophat(masked_gray, dish))
        
        # 策略3: 基于自适应阈值
        papers.extend(self._detect_papers_by_adaptive_threshold(masked_gray, dish))
        
        # 验证和过滤
        validated_papers = self._validate_and_filter_papers(papers, dish, masked_gray)
        
        logger.info(f"滤纸片检测完成: {len(validated_papers)} 个")
        return validated_papers

    def _detect_papers_by_brightness(self, image: np.ndarray, dish: PetriDish) -> List[Colony]:
        """基于亮度检测滤纸片"""
        papers = []
        
        # 计算图像的统计信息
        mean_brightness = np.mean(image[image > 0])  # 排除掩码外的0值
        std_brightness = np.std(image[image > 0])
        
        # 高亮度阈值 - 滤纸片比背景亮
        high_threshold = mean_brightness + 1.5 * std_brightness
        
        # 二值化
        _, binary = cv2.threshold(image, high_threshold, 255, cv2.THRESH_BINARY)
        
        # 形态学操作
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
        binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        
        # 查找轮廓
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            area = cv2.contourArea(contour)
            perimeter = cv2.arcLength(contour, True)
            
            if perimeter == 0:
                continue
            
            # 预期滤纸片面积
            expected_radius = self.filter_paper_diameter_mm * self.px_per_mm / 2
            expected_area = np.pi * (expected_radius ** 2)
            
            # 面积检查
            if area < expected_area * 0.3 or area > expected_area * 3:
                continue
            
            # 圆形度检查
            circularity = 4 * np.pi * area / (perimeter * perimeter)
            if circularity < 0.4:
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
                detection_score=circularity
            ))
        
        return papers

    def _detect_papers_by_tophat(self, image: np.ndarray, dish: PetriDish) -> List[Colony]:
        """基于顶帽变换检测滤纸片"""
        papers = []
        
        # 顶帽变换突出亮的小结构
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))
        tophat = cv2.morphologyEx(image, cv2.MORPH_TOPHAT, kernel)
        
        # 阈值处理
        _, binary = cv2.threshold(tophat, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # 查找轮廓并处理（类似亮度方法）
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < 20:  # 过滤太小的区域
                continue
                
            (x, y), radius = cv2.minEnclosingCircle(contour)
            center = (int(x), int(y))
            radius = int(radius)
            
            papers.append(Colony(
                center=center,
                radius=radius,
                contour=contour,
                substance_type=SubstanceTypeEnum.FILTER_PAPER,
                detection_score=0.6
            ))
        
        return papers

    def _detect_papers_by_adaptive_threshold(self, image: np.ndarray, dish: PetriDish) -> List[Colony]:
        """基于自适应阈值检测滤纸片"""
        papers = []
        
        # 自适应阈值
        adaptive = cv2.adaptiveThreshold(
            image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 15, -2
        )
        
        # 查找轮廓
        contours, _ = cv2.findContours(adaptive, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < 50:
                continue
                
            (x, y), radius = cv2.minEnclosingCircle(contour)
            center = (int(x), int(y))
            radius = int(radius)
            
            papers.append(Colony(
                center=center,
                radius=radius,
                contour=contour,
                substance_type=SubstanceTypeEnum.FILTER_PAPER,
                detection_score=0.5
            ))
        
        return papers

    def _validate_and_filter_papers(self, papers: List[Colony], dish: PetriDish, 
                                   image: np.ndarray) -> List[Colony]:
        """验证和过滤滤纸片检测结果"""
        if not papers:
            return []
        
        # 去重和验证
        filtered_papers = []
        used = set()
        
        papers.sort(key=lambda p: p.detection_score, reverse=True)
        
        for i, paper in enumerate(papers):
            if i in used:
                continue
            
            # 验证滤纸片特征
            if not self._validate_paper_characteristics(paper, image):
                continue
            
            # 检查是否与已选择的重叠
            is_duplicate = False
            for selected_paper in filtered_papers:
                distance = np.sqrt((paper.center[0] - selected_paper.center[0])**2 + 
                                 (paper.center[1] - selected_paper.center[1])**2)
                if distance < max(paper.radius, selected_paper.radius) * 1.5:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                filtered_papers.append(paper)
                used.add(i)
        
        return filtered_papers

    def _validate_paper_characteristics(self, paper: Colony, image: np.ndarray) -> bool:
        """验证滤纸片特征"""
        x, y = paper.center
        r = paper.radius
        
        # 创建滤纸片区域掩码
        mask = np.zeros(image.shape[:2], dtype=np.uint8)
        cv2.circle(mask, (x, y), r, 255, -1)
        
        paper_pixels = image[mask == 255]
        if paper_pixels.size < 5:
            return False
        
        # 滤纸片应该明显比周围亮
        ring_mask = np.zeros(image.shape[:2], dtype=np.uint8)
        cv2.circle(ring_mask, (x, y), int(r * 2), 255, -1)
        cv2.circle(ring_mask, (x, y), r, 0, -1)
        
        ring_pixels = image[ring_mask == 255]
        if ring_pixels.size < 10:
            return False
        
        paper_mean = np.mean(paper_pixels)
        ring_mean = np.mean(ring_pixels)
        
        # 滤纸片应该比周围亮至少15个灰度级
        brightness_diff = paper_mean - ring_mean
        if brightness_diff < 15:
            return False
        
        # 滤纸片内部应该相对均匀
        paper_std = np.std(paper_pixels)
        if paper_std > 20:
            return False
        
        return True