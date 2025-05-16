import cv2
import numpy as np
from typing import List, Optional, Tuple
from .models import Colony, PetriDish

class CircleDetector:
    """圆形检测器类，用于检测培养皿和菌落"""
    
    def __init__(self, plate_diameter_mm=90):
        self.plate_diameter_mm = plate_diameter_mm
    
    def detect_petri_dishes(self, image: np.ndarray) -> List[PetriDish]:
        """检测培养皿"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (9, 9), 2)
        
        # 修改霍夫圆检测参数
        plates = cv2.HoughCircles(blurred, cv2.HOUGH_GRADIENT, dp=1, minDist=400,
                                param1=50, param2=35,
                                minRadius=int(image.shape[0]/3),
                                maxRadius=int(image.shape[0]/1.8))
        
        if plates is None:
            raise Exception("未检测到培养皿")
        
        plates = np.uint16(np.around(plates[0, :]))
        petri_dishes = []
        
        for plate in plates:
            x, y, r = plate
            petri_dishes.append(PetriDish(
                center=(x, y),
                radius=r,
                colonies=[],
                diameter_mm=self.plate_diameter_mm
            ))
            
        return petri_dishes

    def detect_colonies_in_dish(self, image: np.ndarray, dish: PetriDish) -> List[Colony]:
        """在培养皿内检测菌落"""
        mask = np.zeros_like(cv2.cvtColor(image, cv2.COLOR_BGR2GRAY))
        cv2.circle(mask, dish.center, dish.radius, 255, -1)

        colonies_methods = []
        
        try:
            hsv_colonies = self._detect_colonies_hsv(image, mask, dish)
            if hsv_colonies:
                colonies_methods.append(hsv_colonies)
        except Exception as e:
            print(f"HSV方法失败: {str(e)}")
            
        try:
            adaptive_colonies = self._detect_colonies_adaptive(image, mask, dish)
            if adaptive_colonies:
                colonies_methods.append(adaptive_colonies)
        except Exception as e:
            print(f"自适应方法失败: {str(e)}")
            
        try:
            gradient_colonies = self._detect_colonies_gradient(image, mask, dish)
            if gradient_colonies:
                colonies_methods.append(gradient_colonies)
        except Exception as e:
            print(f"梯度方法失败: {str(e)}")
        
        if not colonies_methods:
            return []
            
        # 评估每种方法的结果
        best_colonies = []
        best_score = -1
        
        for colonies in colonies_methods:
            num_score = max(0, 1.0 - abs(len(colonies) - 3) / 3)
            
            shape_scores = []
            for colony in colonies:
                area = cv2.contourArea(colony.contour)
                perimeter = cv2.arcLength(colony.contour, True)
                circularity = 4 * np.pi * area / (perimeter * perimeter) if perimeter > 0 else 0
                shape_scores.append(circularity)
            
            shape_score = np.mean(shape_scores) if shape_scores else 0
            
            position_score = 1.0
            if len(colonies) > 1:
                angles = []
                for colony in colonies:
                    dx = np.int64(colony.center[0]) - np.int64(dish.center[0])
                    dy = np.int64(colony.center[1]) - np.int64(dish.center[1])
                    angle = np.degrees(np.arctan2(float(dy), float(dx))) % 360
                    angles.append(angle)
                angles.sort()
                expected_angle = 360.0 / len(colonies)
                angle_diffs = []
                for i in range(len(angles)):
                    next_i = (i + 1) % len(angles)
                    diff = (angles[next_i] - angles[i]) % 360
                    angle_diffs.append(abs(diff - expected_angle))
                position_score = max(0, 1.0 - np.mean(angle_diffs) / 180.0)
            
            total_score = num_score * 0.4 + shape_score * 0.3 + position_score * 0.3
            
            if total_score > best_score:
                best_score = total_score
                best_colonies = colonies

        return best_colonies

    def _detect_colonies_hsv(self, image: np.ndarray, mask: np.ndarray, dish: PetriDish) -> List[Colony]:
        """使用HSV色彩空间的方法检测菌落"""
        masked = cv2.bitwise_and(image, image, mask=mask)
        hsv = cv2.cvtColor(masked, cv2.COLOR_BGR2HSV)
        
        value = hsv[:,:,2]
        denoised = cv2.medianBlur(value, 5)
        
        clahe1 = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        clahe2 = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(16,16))
        enhanced = clahe1.apply(denoised)
        enhanced = clahe2.apply(enhanced)
        
        mean, stddev = cv2.meanStdDev(enhanced, mask=mask)
        local_std = cv2.GaussianBlur(enhanced, (15, 15), 2.0)
        grad_mask = local_std > (mean[0] + stddev[0] * 0.5)
        grad_mask = grad_mask.astype(np.uint8) * 255
        
        _, binary1 = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        binary2 = cv2.adaptiveThreshold(enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                     cv2.THRESH_BINARY_INV, 51, 10)
        binary3 = grad_mask
        
        binary = cv2.bitwise_or(binary1, binary2)
        binary = cv2.bitwise_or(binary, binary3)
        
        kernel1 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3,3))
        kernel2 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5,5))
        
        morphed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel2)
        morphed = cv2.morphologyEx(morphed, cv2.MORPH_OPEN, kernel1)

        return self._find_colonies(morphed, dish)

    def _detect_colonies_adaptive(self, image: np.ndarray, mask: np.ndarray, dish: PetriDish) -> List[Colony]:
        """使用改进的自适应阈值方法检测菌落"""
        masked = cv2.bitwise_and(image, image, mask=mask)
        gray = cv2.cvtColor(masked, cv2.COLOR_BGR2GRAY)
        
        denoised = cv2.medianBlur(gray, 5)
        clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8,8))
        enhanced = clahe.apply(denoised)
        
        sobelx = cv2.Sobel(enhanced, cv2.CV_64F, 1, 0, ksize=3)
        sobely = cv2.Sobel(enhanced, cv2.CV_64F, 0, 1, ksize=3)
        gradient = np.sqrt(sobelx**2 + sobely**2)
        gradient = cv2.normalize(gradient, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
        
        block_sizes = [25, 51, 75]
        binaries = []
        
        for block_size in block_sizes:
            binary = cv2.adaptiveThreshold(enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                       cv2.THRESH_BINARY_INV, block_size, 5)
            binaries.append(binary)
        
        _, gradient_binary = cv2.threshold(gradient, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        binaries.append(gradient_binary)
        
        binary = np.zeros_like(binaries[0])
        for b in binaries:
            binary = cv2.bitwise_or(binary, b)
        
        kernel1 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5,5))
        kernel2 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3,3))
        
        morphed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel1)
        morphed = cv2.morphologyEx(morphed, cv2.MORPH_OPEN, kernel2)

        return self._find_colonies(morphed, dish)

    def _detect_colonies_gradient(self, image: np.ndarray, mask: np.ndarray, dish: PetriDish) -> List[Colony]:
        """使用改进的梯度方法检测菌落"""
        masked = cv2.bitwise_and(image, image, mask=mask)
        gray = cv2.cvtColor(masked, cv2.COLOR_BGR2GRAY)
        
        denoised = cv2.GaussianBlur(gray, (5, 5), 0)
        
        gradients = []
        ksize_list = [3, 5, 7]
        
        for ksize in ksize_list:
            sobelx = cv2.Sobel(denoised, cv2.CV_64F, 1, 0, ksize=ksize)
            sobely = cv2.Sobel(denoised, cv2.CV_64F, 0, 1, ksize=ksize)
            mag = np.sqrt(sobelx**2 + sobely**2)
            mag = cv2.normalize(mag, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
            gradients.append(mag)
        
        gradient = np.zeros_like(gradients[0])
        for grad in gradients:
            gradient = cv2.max(gradient, grad)
        
        mean, stddev = cv2.meanStdDev(denoised, mask=mask)
        local_std = cv2.GaussianBlur(denoised, (15, 15), 2.0)
        grad_mask = local_std > (mean[0] + stddev[0] * 0.5)
        grad_mask = grad_mask.astype(np.uint8) * 255
        
        _, binary1 = cv2.threshold(gradient, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        binary2 = grad_mask
        binary = cv2.bitwise_or(binary1, binary2)
        
        kernel1 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3,3))
        kernel2 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5,5))
        
        morphed = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel1)
        morphed = cv2.morphologyEx(morphed, cv2.MORPH_CLOSE, kernel2)

        return self._find_colonies(morphed, dish)

    def _find_colonies(self, binary: np.ndarray, dish: PetriDish) -> List[Colony]:
        """从二值图像中提取菌落"""
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        colonies = []
        
        for contour in contours:
            area = cv2.contourArea(contour)
            perimeter = cv2.arcLength(contour, True)
            circularity = 4 * np.pi * area / (perimeter * perimeter) if perimeter > 0 else 0
            
            (x, y), radius = cv2.minEnclosingCircle(contour)
            center = (int(x), int(y))
            radius = int(radius)
            
            compactness = area / (np.pi * radius * radius) if radius > 0 else 0
            aspect_ratio = 1.0
            if len(contour) >= 5:
                (_, _), (width, height), _ = cv2.fitEllipse(contour)
                aspect_ratio = min(width, height) / max(width, height) if max(width, height) > 0 else 0
            
            min_radius = dish.radius * 0.03
            max_radius = dish.radius * 0.15
            
            if (radius < min_radius or
                radius > max_radius or
                circularity < 0.7 or
                compactness < 0.8 or
                aspect_ratio < 0.8):
                continue
                
            center_x = np.int64(center[0])
            center_y = np.int64(center[1])
            dish_x = np.int64(dish.center[0])
            dish_y = np.int64(dish.center[1])
            
            dx = center_x - dish_x
            dy = center_y - dish_y
            dist_to_center = np.sqrt(float(dx * dx + dy * dy))
            if dist_to_center > dish.radius * 0.9:
                continue
            
            colony = Colony(center=center, radius=radius, contour=contour)
            colonies.append(colony)
            
            if len(colonies) >= 3:
                break
        
        return colonies

    def _find_best_zone_contour(self, binary: np.ndarray, colony: Colony,
                             max_radius: int, min_radius: int) -> Optional[Tuple[int, int, int]]:
        """查找最佳抑菌圈轮廓"""
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        best_circle = None
        max_score = -float('inf')
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < np.pi * min_radius * min_radius:
                continue
                
            perimeter = cv2.arcLength(contour, True)
            circularity = 4 * np.pi * area / (perimeter * perimeter) if perimeter > 0 else 0
            
            (x, y), radius = cv2.minEnclosingCircle(contour)
            
            center_score = self._calculate_center_score((int(x), int(y)), colony.center, max_radius)
            shape_score = circularity
            size_score = 1.0 if radius > min_radius else 0.0
            
            total_score = (center_score * 0.4 + shape_score * 0.4 + size_score * 0.2)
            
            if total_score > max_score:
                max_score = total_score
                best_circle = (int(x), int(y), int(radius))
        
        return best_circle if max_score > 0.5 else None

    def _calculate_center_score(self, point1: Tuple[int, int], point2: Tuple[int, int],
                            max_dist: float) -> float:
        """计算两点之间的距离得分"""
        dx = np.int64(point1[0]) - np.int64(point2[0])
        dy = np.int64(point1[1]) - np.int64(point2[1])
        dist = np.sqrt(float(dx * dx + dy * dy))
        return max(0, 1.0 - dist / max_dist)

    def detect_inhibition_zone(self, value_channel: np.ndarray, colony: Colony, dish: PetriDish) -> None:
        """检测主抑菌圈和次级抑菌圈"""
        FILTER_PAPER_DIAMETER_MM = 6.0
        mm_per_pixel = dish.diameter_mm / (2 * dish.radius)
        filter_paper_radius_px = int(FILTER_PAPER_DIAMETER_MM / (2 * mm_per_pixel))
        
        mask = np.zeros_like(value_channel)
        max_search_radius = min(int(colony.radius * 5), int(dish.radius * 0.8))
        cv2.circle(mask, colony.center, max_search_radius, 255, -1)
        
        masked = cv2.bitwise_and(value_channel, value_channel, mask=mask)
        blurred = cv2.GaussianBlur(masked, (5, 5), 1)
        
        # 改进的多级阈值设置
        thresholds = {
            'primary': {
                'low': 35,  # 降低主抑菌圈的低阈值以捕获更多区域
                'high': 180,
                'min_area_ratio': 0.8  # 相对于滤纸片面积的最小比例
            },
            'secondary': {
                'low': 65,  # 调整次级抑菌圈阈值
                'high': 160,
                'min_area_ratio': 0.6
            }
        }
        
        results = {}
        for zone_type, thresh in thresholds.items():
            zone_mask = np.zeros_like(blurred)
            cv2.circle(zone_mask, colony.center, max_search_radius, 255, -1)
            
            _, high_mask = cv2.threshold(blurred, thresh['high'], 255, cv2.THRESH_BINARY)
            _, low_mask = cv2.threshold(blurred, thresh['low'], 255, cv2.THRESH_BINARY_INV)
            binary = cv2.bitwise_and(high_mask, low_mask)
            binary = cv2.bitwise_and(binary, zone_mask)
            
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5,5))
            morphed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
            morphed = cv2.morphologyEx(morphed, cv2.MORPH_OPEN, kernel)
            
            results[zone_type] = self._find_best_zone_contour(
                morphed, colony, max_search_radius, filter_paper_radius_px)
        
        colony.primary_inhibition_zone = results['primary']
        colony.secondary_inhibition_zone = results['secondary']
        
        if results['primary'] and results['secondary']:
            self._analyze_zone_overlap(value_channel, colony, results)

    def _analyze_zone_overlap(self, value_channel: np.ndarray, colony: Colony,
                           results: dict) -> None:
        """高级抑菌圈重叠区域分析"""
        if not (colony.primary_inhibition_zone and colony.secondary_inhibition_zone):
            return
        
        h, w = value_channel.shape[:2]
        primary_mask = np.zeros((h, w), dtype=np.uint8)
        secondary_mask = np.zeros((h, w), dtype=np.uint8)
        
        # 绘制抑菌圈区域
        primary = colony.primary_inhibition_zone
        secondary = colony.secondary_inhibition_zone
        
        cv2.circle(primary_mask, (primary[0], primary[1]), primary[2], 255, -1)
        cv2.circle(secondary_mask, (secondary[0], secondary[1]), secondary[2], 255, -1)
        
        # 计算重叠区域
        overlap = cv2.bitwise_and(primary_mask, secondary_mask)
        
        # 应用形态学操作优化重叠区域
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3,3))
        overlap = cv2.morphologyEx(overlap, cv2.MORPH_OPEN, kernel)
        
        # 寻找重叠区域的轮廓
        contours, _ = cv2.findContours(overlap, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        overlap_zones = []
        min_area = 50  # 最小有效面积
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < min_area:
                continue
                
            # 计算轮廓特征
            perimeter = cv2.arcLength(contour, True)
            circularity = 4 * np.pi * area / (perimeter * perimeter) if perimeter > 0 else 0
            
            # 获取最小外接圆
            (x, y), radius = cv2.minEnclosingCircle(contour)
            center = (int(x), int(y))
            
            # 验证重叠区域的有效性
            if circularity > 0.5:  # 要求一定的圆形度
                overlap_zones.append((center[0], center[1], int(radius)))
        
        colony.overlap_zones = overlap_zones

    def draw_results(self, image: np.ndarray, dishes: List[PetriDish]) -> np.ndarray:
        """在图像上绘制检测结果"""
        result = image.copy()
        
        for dish in dishes:
            # 绘制培养皿
            cv2.circle(result, dish.center, dish.radius, (0, 255, 0), 2)
            
            for colony in dish.colonies:
                # 绘制菌落
                cv2.circle(result, colony.center, colony.radius, (0, 0, 255), 2)
                cv2.drawContours(result, [colony.contour], -1, (255, 0, 0), 1)
                
                # 绘制主抑菌圈
                if colony.primary_inhibition_zone:
                    x, y, r = colony.primary_inhibition_zone
                    cv2.circle(result, (x, y), r, (255, 255, 0), 2)
                
                # 绘制次级抑菌圈
                if colony.secondary_inhibition_zone:
                    x, y, r = colony.secondary_inhibition_zone
                    cv2.circle(result, (x, y), r, (0, 255, 255), 2)
                
                # 绘制重叠区域
                if colony.overlap_zones:
                    for x, y, r in colony.overlap_zones:
                        cv2.circle(result, (x, y), r, (255, 0, 255), 2)
        
        return result

    def _generate_analysis_report(self, dish: PetriDish) -> str:
        """生成详细的分析报告"""
        mm_per_pixel = dish.diameter_mm / (2 * dish.radius)
        report = []
        
        report.append(f"培养皿分析报告")
        report.append(f"培养皿直径: {dish.diameter_mm:.1f}mm")
        report.append(f"检测到菌落数量: {len(dish.colonies)}\n")
        
        for i, colony in enumerate(dish.colonies, 1):
            report.append(f"菌落 {i}:")
            colony_diameter = 2 * colony.radius * mm_per_pixel
            report.append(f"- 滤纸片直径: {colony_diameter:.1f}mm")
            
            # 主抑菌圈信息
            if colony.primary_inhibition_zone:
                x, y, r = colony.primary_inhibition_zone
                diameter = 2 * r * mm_per_pixel
                width = (diameter - 6.0) / 2  # 6.0mm是标准滤纸片直径
                report.append(f"- 主抑菌圈:")
                report.append(f"  直径: {diameter:.1f}mm")
                report.append(f"  抑菌环宽度: {width:.1f}mm")
            
            # 次级抑菌圈信息
            if colony.secondary_inhibition_zone:
                x, y, r = colony.secondary_inhibition_zone
                diameter = 2 * r * mm_per_pixel
                width = (diameter - 6.0) / 2
                report.append(f"- 次级抑菌圈(半透明):")
                report.append(f"  直径: {diameter:.1f}mm")
                report.append(f"  抑菌环宽度: {width:.1f}mm")
            
            # 重叠区域信息
            if colony.overlap_zones:
                total_area = sum(np.pi * r * r * (mm_per_pixel ** 2)
                               for _, _, r in colony.overlap_zones)
                report.append(f"- 重叠区域:")
                report.append(f"  面积: {total_area:.1f}mm²")
                report.append(f"  区域数量: {len(colony.overlap_zones)}")
            
            report.append("")  # 空行分隔
        
        return "\n".join(report)

    def process_image(self, image_path: str) -> Tuple[np.ndarray, str]:
        """处理图像的主函数"""
        image = cv2.imread(image_path)
        if image is None:
            raise Exception(f"无法读取图像: {image_path}")
        
        dishes = self.detect_petri_dishes(image)
        
        for dish in dishes:
            colonies = self.detect_colonies_in_dish(image, dish)
            dish.colonies = colonies
            
            # 检测每个菌落的抑菌圈
            for colony in colonies:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                self.detect_inhibition_zone(gray, colony, dish)
        
        # 生成分析报告
        report = ""
        for i, dish in enumerate(dishes, 1):
            report += f"\n===== 培养皿 {i} =====\n"
            report += self._generate_analysis_report(dish)
            
        return self.draw_results(image, dishes), report