import cv2
import numpy as np
from typing import List, Optional, Tuple, Dict
from enum import Enum
from .models import Colony, PetriDish, SubstanceTypeEnum
from .processor import ImageProcessor
from utils.logger import get_logger

logger = get_logger(__name__)

class DetectionChallenge(Enum):
    """检测挑战类型"""
    TRANSPARENT_HOLE_AND_ZONE = 1  # 透明挖孔+透明抑菌圈
    MULTI_GRADIENT_TRANSPARENCY = 2  # 多级梯度透明
    BUBBLE_INTERFERENCE = 3  # 气泡干扰
    COLORED_BACKGROUND_COLONIES = 4  # 有色背景菌落

class SpecializedInhibitionDetector:
    """针对特殊挑战的专门检测器"""

    def __init__(self, px_per_mm: float):
        self.px_per_mm = px_per_mm
        self.processor = ImageProcessor()

    def detect_with_challenge_awareness(self, image: np.ndarray, 
                                      challenge_type: DetectionChallenge,
                                      dish: PetriDish) -> Dict:
        """根据检测挑战类型选择合适的检测策略"""
        logger.info(f"开始针对 {challenge_type.name} 的专门检测")
        
        if challenge_type == DetectionChallenge.TRANSPARENT_HOLE_AND_ZONE:
            return self._detect_transparent_holes_and_zones(image, dish)
        elif challenge_type == DetectionChallenge.MULTI_GRADIENT_TRANSPARENCY:
            return self._detect_multi_gradient_zones(image, dish)
        elif challenge_type == DetectionChallenge.BUBBLE_INTERFERENCE:
            return self._detect_with_bubble_filtering(image, dish)
        elif challenge_type == DetectionChallenge.COLORED_BACKGROUND_COLONIES:
            return self._detect_with_colony_background(image, dish)
        else:
            logger.warning(f"未知的挑战类型: {challenge_type}")
            return {'substances': [], 'zones': []}

    def _detect_transparent_holes_and_zones(self, image: np.ndarray, dish: PetriDish) -> Dict:
        """检测透明挖孔和透明抑菌圈"""
        logger.info("使用透明目标检测策略")
        
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # 策略1: 基于局部对比度增强
        enhanced_image = self._enhance_transparent_features(gray, dish)
        
        # 策略2: 基于纹理分析检测透明边界
        texture_features = self._analyze_texture_boundaries(enhanced_image, dish)
        
        # 策略3: 基于统计差异检测微弱变化
        statistical_features = self._detect_statistical_anomalies(gray, dish)
        
        # 综合分析结果
        holes = self._find_transparent_holes(enhanced_image, texture_features, statistical_features, dish)
        zones = self._find_transparent_zones(enhanced_image, holes, dish)
        
        return {
            'substances': holes,
            'zones': zones,
            'confidence': self._calculate_transparent_detection_confidence(holes, zones)
        }

    def _enhance_transparent_features(self, gray_image: np.ndarray, dish: PetriDish) -> np.ndarray:
        """增强透明特征的可见性"""
        
        # 创建培养皿掩码
        dish_mask = np.zeros(gray_image.shape[:2], dtype=np.uint8)
        cv2.circle(dish_mask, dish.center, int(dish.radius * 0.95), 255, -1)
        
        # 方法1: 局部对比度增强 (CLAHE)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(16, 16))
        enhanced1 = clahe.apply(gray_image)
        
        # 方法2: 拉普拉斯锐化突出边缘
        laplacian = cv2.Laplacian(gray_image, cv2.CV_64F, ksize=3)
        laplacian_normalized = cv2.normalize(laplacian, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
        enhanced2 = cv2.addWeighted(gray_image, 0.7, laplacian_normalized, 0.3, 0)
        
        # 方法3: 双边滤波保持边缘同时平滑噪声
        bilateral = cv2.bilateralFilter(gray_image, 9, 75, 75)
        
        # 方法4: 顶帽变换突出亮的小结构
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))
        tophat = cv2.morphologyEx(gray_image, cv2.MORPH_TOPHAT, kernel)
        enhanced3 = cv2.add(gray_image, tophat)
        
        # 综合多种增强方法
        combined = cv2.addWeighted(
            cv2.addWeighted(enhanced1, 0.4, enhanced2, 0.3, 0),
            0.7, enhanced3, 0.3, 0
        )
        
        # 只在培养皿区域内应用增强
        result = gray_image.copy()
        result[dish_mask == 255] = combined[dish_mask == 255]
        
        return result

    def _analyze_texture_boundaries(self, image: np.ndarray, dish: PetriDish) -> np.ndarray:
        """分析纹理边界来检测透明物体"""
        
        # 使用LBP (Local Binary Pattern) 检测纹理变化
        def lbp(image, radius=1, n_points=8):
            """简化的LBP实现"""
            h, w = image.shape
            lbp_image = np.zeros((h, w), dtype=np.uint8)
            
            for i in range(radius, h - radius):
                for j in range(radius, w - radius):
                    center = image[i, j]
                    pattern = 0
                    
                    for p in range(n_points):
                        angle = 2 * np.pi * p / n_points
                        x = int(j + radius * np.cos(angle))
                        y = int(i + radius * np.sin(angle))
                        
                        if 0 <= x < w and 0 <= y < h:
                            if image[y, x] >= center:
                                pattern |= (1 << p)
                    
                    lbp_image[i, j] = pattern
            
            return lbp_image
        
        # 计算LBP纹理特征
        lbp_image = lbp(image, radius=2, n_points=8)
        
        # 计算纹理变化的梯度
        grad_x = cv2.Sobel(lbp_image, cv2.CV_64F, 1, 0, ksize=3)
        grad_y = cv2.Sobel(lbp_image, cv2.CV_64F, 0, 1, ksize=3)
        texture_gradient = np.sqrt(grad_x**2 + grad_y**2)
        
        # 归一化并转换为uint8
        texture_boundaries = cv2.normalize(texture_gradient, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
        
        return texture_boundaries

    def _detect_statistical_anomalies(self, image: np.ndarray, dish: PetriDish) -> np.ndarray:
        """检测统计异常来发现微弱的透明目标"""
        
        # 使用滑动窗口计算局部统计特征
        window_size = max(10, int(dish.radius * 0.1))
        kernel = np.ones((window_size, window_size), np.float32) / (window_size * window_size)
        
        # 计算局部均值
        local_mean = cv2.filter2D(image.astype(np.float32), -1, kernel)
        
        # 计算局部方差
        local_variance = cv2.filter2D((image.astype(np.float32) - local_mean)**2, -1, kernel)
        
        # 计算全局统计
        global_mean = np.mean(image)
        global_std = np.std(image)
        
        # 检测异常：局部统计与全局统计的差异
        mean_anomaly = np.abs(local_mean - global_mean)
        variance_anomaly = np.abs(local_variance - global_std**2)
        
        # 综合异常分数
        anomaly_score = cv2.addWeighted(
            cv2.normalize(mean_anomaly, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8),
            0.6,
            cv2.normalize(variance_anomaly, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8),
            0.4, 0
        )
        
        return anomaly_score

    def _find_transparent_holes(self, enhanced_image: np.ndarray, 
                               texture_features: np.ndarray,
                               statistical_features: np.ndarray,
                               dish: PetriDish) -> List[Colony]:
        """在增强图像中寻找透明挖孔"""
        holes = []
        
        # 综合多种特征
        combined_features = cv2.addWeighted(
            cv2.addWeighted(enhanced_image, 0.4, texture_features, 0.3, 0),
            0.7, statistical_features, 0.3, 0
        )
        
        # 使用多阈值分割
        thresholds = [
            cv2.threshold(combined_features, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[0],
            np.mean(combined_features) - np.std(combined_features),
            np.mean(combined_features) + 0.5 * np.std(combined_features)
        ]
        
        for threshold_val in thresholds:
            # 对于挖孔，我们寻找比背景暗的区域
            _, binary = cv2.threshold(combined_features, threshold_val, 255, cv2.THRESH_BINARY_INV)
            
            # 形态学操作清理噪声
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
            binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
            binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
            
            # 寻找轮廓
            contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                hole = self._analyze_hole_contour(contour, dish, enhanced_image)
                if hole:
                    holes.append(hole)
        
        # 去重并选择最佳候选
        filtered_holes = self._filter_duplicate_holes(holes)
        
        return filtered_holes

    def _analyze_hole_contour(self, contour: np.ndarray, dish: PetriDish, 
                             image: np.ndarray) -> Optional[Colony]:
        """分析轮廓是否为有效的透明挖孔"""
        
        area = cv2.contourArea(contour)
        perimeter = cv2.arcLength(contour, True)
        
        # 基本尺寸检查
        expected_hole_area = np.pi * (self.hole_diameter_mm * self.px_per_mm / 2)**2
        if area < expected_hole_area * 0.3 or area > expected_hole_area * 3:
            return None
        
        if perimeter == 0:
            return None
        
        # 圆形度检查
        circularity = 4 * np.pi * area / (perimeter * perimeter)
        if circularity < 0.4:  # 放宽要求，因为透明边界可能不够清晰
            return None
        
        # 获取外接圆
        (x, y), radius = cv2.minEnclosingCircle(contour)
        center = (int(x), int(y))
        radius = int(radius)
        
        # 检查是否在培养皿内
        distance_to_dish_center = np.sqrt((center[0] - dish.center[0])**2 + 
                                         (center[1] - dish.center[1])**2)
        if distance_to_dish_center + radius > dish.radius * 0.9:
            return None
        
        # 透明度验证：挖孔区域应该与周围有微弱但一致的差异
        transparency_score = self._validate_transparency(image, center, radius)
        if transparency_score < 0.3:
            return None
        
        return Colony(
            center=center,
            radius=radius,
            contour=contour,
            substance_type=SubstanceTypeEnum.HOLE,
            detection_score=transparency_score
        )

    def _validate_transparency(self, image: np.ndarray, center: Tuple[int, int], 
                              radius: int) -> float:
        """验证区域的透明特征"""
        
        # 创建内部和环形区域的掩码
        inner_mask = np.zeros(image.shape[:2], dtype=np.uint8)
        cv2.circle(inner_mask, center, radius, 255, -1)
        
        ring_mask = np.zeros(image.shape[:2], dtype=np.uint8)
        cv2.circle(ring_mask, center, int(radius * 1.5), 255, -1)
        cv2.circle(ring_mask, center, radius, 0, -1)
        
        inner_pixels = image[inner_mask == 255]
        ring_pixels = image[ring_mask == 255]
        
        if inner_pixels.size < 5 or ring_pixels.size < 5:
            return 0.0
        
        # 透明特征：
        # 1. 内部区域的标准差应该较小（均匀）
        inner_std = np.std(inner_pixels)
        uniformity_score = max(0, 1 - inner_std / 30.0)
        
        # 2. 内部和环形区域的亮度差异应该微弱但一致
        inner_mean = np.mean(inner_pixels)
        ring_mean = np.mean(ring_pixels)
        contrast = abs(inner_mean - ring_mean)
        
        # 透明目标的对比度应该在一个合理范围内
        contrast_score = max(0, 1 - abs(contrast - 10) / 20.0)
        
        # 3. 边缘的渐变特征
        gradient_score = self._analyze_edge_gradient(image, center, radius)
        
        transparency_score = (uniformity_score * 0.4 + 
                            contrast_score * 0.4 + 
                            gradient_score * 0.2)
        
        return transparency_score

    def _analyze_edge_gradient(self, image: np.ndarray, center: Tuple[int, int], 
                              radius: int) -> float:
        """分析边缘梯度特征"""
        
        # 在圆周上采样点，分析梯度变化
        angles = np.linspace(0, 2*np.pi, 16)
        gradients = []
        
        for angle in angles:
            # 从内部到外部采样
            points = []
            for r in range(max(1, radius-3), radius+4):
                x = int(center[0] + r * np.cos(angle))
                y = int(center[1] + r * np.sin(angle))
                
                if 0 <= x < image.shape[1] and 0 <= y < image.shape[0]:
                    points.append(image[y, x])
            
            if len(points) > 2:
                # 计算梯度
                grad = np.gradient(points)
                gradients.extend(grad)
        
        if not gradients:
            return 0.0
        
        # 透明边界的梯度应该相对平缓
        gradient_magnitude = np.mean(np.abs(gradients))
        gradient_score = max(0, 1 - gradient_magnitude / 15.0)
        
        return gradient_score

    def _filter_duplicate_holes(self, holes: List[Colony]) -> List[Colony]:
        """过滤重复的挖孔检测"""
        if len(holes) <= 1:
            return holes
        
        # 按检测得分排序
        holes.sort(key=lambda x: x.detection_score, reverse=True)
        
        filtered = []
        for hole in holes:
            is_duplicate = False
            for existing in filtered:
                distance = np.sqrt((hole.center[0] - existing.center[0])**2 + 
                                 (hole.center[1] - existing.center[1])**2)
                if distance < max(hole.radius, existing.radius):
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                filtered.append(hole)
        
        return filtered[:3]  # 最多保留3个最佳候选

    def _find_transparent_zones(self, enhanced_image: np.ndarray, 
                               holes: List[Colony], dish: PetriDish) -> List[Dict]:
        """寻找透明抑菌圈"""
        zones = []
        
        if not holes:
            # 如果没有找到明确的挖孔，尝试在培养皿中心搜索
            center_hole = Colony(
                center=dish.center,
                radius=int(6 * self.px_per_mm / 2),  # 假设6mm直径
                contour=None,
                substance_type=SubstanceTypeEnum.UNKNOWN
            )
            holes = [center_hole]
        
        for hole in holes:
            zone = self._detect_transparent_zone_around_hole(enhanced_image, hole, dish)
            if zone:
                zones.append(zone)
        
        return zones

    def _detect_transparent_zone_around_hole(self, image: np.ndarray, 
                                           hole: Colony, dish: PetriDish) -> Optional[Dict]:
        """检测挖孔周围的透明抑菌圈"""
        
        # 使用径向分析检测透明抑菌圈
        center_x, center_y = hole.center
        max_radius = min(dish.radius // 2, 
                        int(np.sqrt((center_x - dish.center[0])**2 + 
                                   (center_y - dish.center[1])**2)) + dish.radius // 3)
        
        # 分析多个方向的径向强度曲线
        angles = np.linspace(0, 2*np.pi, 24)
        radius_range = range(hole.radius + 5, max_radius, 3)
        
        radial_profiles = []
        for angle in angles:
            profile = []
            for r in radius_range:
                x = int(center_x + r * np.cos(angle))
                y = int(center_y + r * np.sin(angle))
                
                if 0 <= x < image.shape[1] and 0 <= y < image.shape[0]:
                    profile.append(image[y, x])
                else:
                    profile.append(0)
            
            if profile:
                radial_profiles.append(profile)
        
        if not radial_profiles:
            return None
        
        # 计算平均径向强度曲线
        avg_profile = np.mean(radial_profiles, axis=0)
        
        # 寻找透明抑菌圈的边界（微弱的强度变化）
        # 对于透明抑菌圈，我们寻找平缓的强度上升
        smoothed_profile = cv2.GaussianBlur(avg_profile.reshape(1, -1).astype(np.float32), 
                                          (1, 5), 1).flatten()
        
        gradient = np.gradient(smoothed_profile)
        
        # 寻找持续的正梯度区域（可能的抑菌圈边界）
        zone_candidates = []
        for i in range(len(gradient) - 5):
            if all(g > 0.1 for g in gradient[i:i+3]):  # 持续上升
                zone_radius = radius_range[i] if i < len(radius_range) else max_radius
                
                # 验证这个半径处的透明特征
                if self._validate_transparent_zone(image, hole.center, zone_radius, dish):
                    confidence = self._calculate_transparent_zone_confidence(
                        smoothed_profile, i, gradient
                    )
                    
                    diameter_mm = (zone_radius * 2) / self.px_per_mm if self.px_per_mm > 0 else 0
                    
                    zone_info = {
                        'center': hole.center,
                        'radius': zone_radius,
                        'diameter_mm': diameter_mm,
                        'area_px': np.pi * (zone_radius ** 2),
                        'confidence': confidence,
                        'method': 'transparent_radial'
                    }
                    zone_candidates.append(zone_info)
        
        # 选择最佳候选
        if zone_candidates:
            best_zone = max(zone_candidates, key=lambda x: x['confidence'])
            return best_zone
        
        return None

    def _validate_transparent_zone(self, image: np.ndarray, center: Tuple[int, int],
                                  radius: int, dish: PetriDish) -> bool:
        """验证透明抑菌圈的有效性"""
        
        # 基本尺寸和位置检查
        if radius < 15 or radius > dish.radius * 0.6:
            return False
        
        distance_to_dish_center = np.sqrt((center[0] - dish.center[0])**2 + 
                                         (center[1] - dish.center[1])**2)
        if distance_to_dish_center + radius > dish.radius * 0.95:
            return False
        
        # 透明抑菌圈的特征验证
        zone_mask = np.zeros(image.shape[:2], dtype=np.uint8)
        cv2.circle(zone_mask, center, radius, 255, 2)  # 只检查边界
        
        boundary_pixels = image[zone_mask == 255]
        if boundary_pixels.size < 10:
            return False
        
        # 透明抑菌圈边界应该有一定的均匀性
        boundary_std = np.std(boundary_pixels)
        return boundary_std < 25  # 边界变化不应该太大

    def _calculate_transparent_zone_confidence(self, profile: np.ndarray, 
                                             peak_idx: int, gradient: np.ndarray) -> float:
        """计算透明抑菌圈的置信度"""
        confidence = 0.0
        
        # 1. 梯度的平缓性（透明抑菌圈应该有平缓的边界）
        if peak_idx < len(gradient):
            gradient_smoothness = 1.0 / (1.0 + abs(gradient[peak_idx]))
            confidence += gradient_smoothness * 0.4
        
        # 2. 强度变化的一致性
        if peak_idx < len(profile) - 3:
            consistency = 1.0 - np.std(profile[peak_idx:peak_idx+3]) / 20.0
            confidence += max(0, consistency) * 0.4
        
        # 3. 径向对称性（通过多方向分析的一致性）
        symmetry_score = 0.8  # 简化实现，实际应该分析多方向的一致性
        confidence += symmetry_score * 0.2
        
        return min(confidence, 1.0)

    def _calculate_transparent_detection_confidence(self, holes: List[Colony], 
                                                   zones: List[Dict]) -> float:
        """计算整体透明检测的置信度"""
        if not holes and not zones:
            return 0.0
        
        hole_confidence = np.mean([h.detection_score for h in holes]) if holes else 0.0
        zone_confidence = np.mean([z.get('confidence', 0) for z in zones]) if zones else 0.0
        
        # 如果同时检测到挖孔和抑菌圈，置信度更高
        if holes and zones:
            return min((hole_confidence + zone_confidence) * 0.6, 1.0)
        else:
            return max(hole_confidence, zone_confidence) * 0.8

    # 其他方法的属性设置
    @property
    def hole_diameter_mm(self):
        return 6.0  # 默认挖孔直径

    def _detect_multi_gradient_zones(self, image: np.ndarray, dish: PetriDish) -> Dict:
        """检测多级梯度透明抑菌圈（滤纸片法）"""
        # 这里可以实现滤纸片法的专门检测逻辑
        logger.info("多级梯度检测功能待实现")
        return {'substances': [], 'zones': []}

    def _detect_with_bubble_filtering(self, image: np.ndarray, dish: PetriDish) -> Dict:
        """带气泡过滤的检测"""
        # 这里可以实现气泡识别和过滤逻辑
        logger.info("气泡过滤检测功能待实现")
        return {'substances': [], 'zones': []}

    def _detect_with_colony_background(self, image: np.ndarray, dish: PetriDish) -> Dict:
        """带有色菌落背景的检测"""
        # 这里可以实现有色背景处理逻辑
        logger.info("有色背景检测功能待实现")
        return {'substances': [], 'zones': []}