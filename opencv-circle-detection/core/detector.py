import cv2
import numpy as np
from typing import List, Optional, Tuple, Dict
from .models import Colony, PetriDish
from .processor import ImageProcessor, ImageQuality
from utils.logger import get_logger

logger = get_logger(__name__)

class CircleDetector:
    """圆形检测器类，用于检测培养皿、滤纸片和抑菌圈"""
    
    def __init__(self, plate_diameter_mm: float = 90.0, filter_paper_diameter_mm: float = 6.0):
        self.plate_diameter_mm = plate_diameter_mm
        self.filter_paper_diameter_mm = filter_paper_diameter_mm
        self.processor = ImageProcessor()
        self.px_per_mm = None  # 像素/毫米比例
        
    def detect_petri_dishes(self, image: np.ndarray) -> List[PetriDish]:
        """检测培养皿并进行尺寸标定"""
        logger.info("开始检测培养皿")
        
        # 预处理
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        # 高斯模糊
        blurred = cv2.GaussianBlur(gray, (9, 9), 2)
        processed = self.processor.preprocess(blurred)
        
        params = {
            'dp': 1,
            'minDist': 400,
            'param1': 50,
            'param2': 35,
            'minRadius': int(image.shape[0]/3),
            'maxRadius': int(image.shape[0]/1.8)
        }
        
        # 培养皿检测
        circles = cv2.HoughCircles(
            processed,
            cv2.HOUGH_GRADIENT,
            **params
        )
        
        plates = []
        if circles is not None:
            circles = np.uint16(np.around(circles))
            for x, y, r in circles[0,:]:
                # 验证圆的有效性
                if self._validate_dish_circle(processed, (x, y), r):
                    plates.append(PetriDish(
                        center=(int(x), int(y)),
                        radius=int(r),
                        colonies=[],  # 初始为空列表
                        diameter_mm=self.plate_diameter_mm
                    ))
                    # 更新像素比例
                    self.px_per_mm = r * 2 / self.plate_diameter_mm
                    logger.info(f"标定比例: {self.px_per_mm:.2f}px/mm")
        
        logger.info(f"检测到 1 个培养皿")
        return plates

    def detect_filter_papers(self, image: np.ndarray, dish: PetriDish) -> List[Colony]:
        """检测圆形滤纸片"""
        if self.px_per_mm is None:
            raise ValueError("请先进行培养皿检测和尺寸标定")
            
        logger.info("开始检测滤纸片")
        
        # 创建培养皿区域掩码
        mask = np.zeros(image.shape[:2], dtype=np.uint8)
        cv2.circle(mask, dish.center, dish.radius, 255, -1)
        
        # 预处理
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        masked = cv2.bitwise_and(gray, gray, mask=mask)
        
        # 计算滤纸片的预期像素半径
        expected_radius = int(self.filter_paper_diameter_mm * self.px_per_mm / 2)
        min_radius = int(expected_radius * 0.8)
        max_radius = int(expected_radius * 1.2)
        
        # 霍夫圆检测
        circles = cv2.HoughCircles(
            masked,
            cv2.HOUGH_GRADIENT,
            dp=1,
            minDist=expected_radius*2,
            param1=50,
            param2=25,
            minRadius=min_radius,
            maxRadius=max_radius
        )
        
        papers = []
        if circles is not None:
            circles = np.uint16(np.around(circles))
            for x, y, r in circles[0,:]:
                # 验证滤纸片的有效性
                if self._validate_paper_circle(masked, (x, y), r):
                    papers.append(Colony(
                        center=(int(x), int(y)),
                        radius=int(r),
                        contour=self._create_circle_contour((x, y), r)
                    ))
                    
        logger.info(f"检测到 {len(papers)} 个滤纸片")
        return papers

    def detect_inhibition_zones(self, image: np.ndarray, papers: List[Colony]) -> List[Dict]:
        """检测每个滤纸片周围的抑菌圈"""
        logger.info("开始检测抑菌圈")
        
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        results = []
        
        for paper in papers:
            # 创建ROI区域
            x, y = paper.center
            search_radius = paper.radius * 5
            roi = self._get_roi(gray, x, y, search_radius)
            
            if roi is None:
                continue
                
            # 预处理
            enhanced = cv2.equalizeHist(roi)
            
            # 检测主抑菌圈
            primary_zone = self._detect_primary_zone(enhanced, paper)
            
            results.append({
                'paper': paper,
                'primary_zone': primary_zone
            })
            
        return results

    def _detect_primary_zone(self, image: np.ndarray, paper: Colony) -> Optional[Dict]:
        """检测主抑菌圈"""
        # 自适应阈值
        binary = cv2.adaptiveThreshold(
            image, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            51, 5
        )
        
        # 形态学处理
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5,5))
        binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        
        # 查找轮廓
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        best_zone = None
        max_score = 0
        
        for contour in contours:
            area = cv2.contourArea(contour)
            perimeter = cv2.arcLength(contour, True)
            circularity = 4 * np.pi * area / (perimeter * perimeter) if perimeter > 0 else 0
            
            if circularity > 0.7 and area > np.pi * paper.radius * paper.radius * 0.8:
                (x, y), radius = cv2.minEnclosingCircle(contour)
                score = circularity * (area / (np.pi * radius * radius))
                
                if score > max_score:
                    max_score = score
                    best_zone = {
                        'center': (int(x), int(y)),
                        'radius': int(radius),
                        'diameter_mm': (radius * 2) / self.px_per_mm
                    }
                    
        return best_zone

    def _get_roi(self, image: np.ndarray, x: int, y: int, radius: int) -> Optional[np.ndarray]:
        """获取感兴趣区域"""
        h, w = image.shape[:2]
        x1 = max(0, x - radius)
        y1 = max(0, y - radius)
        x2 = min(w, x + radius)
        y2 = min(h, y + radius)
        
        if x2 <= x1 or y2 <= y1:
            return None
            
        return image[y1:y2, x1:x2]

    def _validate_dish_circle(self, image: np.ndarray, center: Tuple[int, int], 
                            radius: int) -> bool:
        """验证培养皿圆的有效性"""
        mask = np.zeros_like(image)
        cv2.circle(mask, center, radius, 255, 2)
        edge_pixels = cv2.bitwise_and(image, mask)
        mean_value = np.mean(edge_pixels[edge_pixels > 0])
        return mean_value > 50

    def _validate_paper_circle(self, image: np.ndarray, center: Tuple[int, int], 
                             radius: int) -> bool:
        """验证滤纸片圆的有效性"""
        mask = np.zeros_like(image)
        cv2.circle(mask, center, radius, 255, -1)
        roi = cv2.bitwise_and(image, mask)
        mean_value = np.mean(roi[roi > 0])
        return mean_value > 150

    def _create_circle_contour(self, center: Tuple[int, int], 
                             radius: int) -> np.ndarray:
        """创建圆形轮廓点集"""
        angles = np.linspace(0, 2*np.pi, 100)
        pts = np.array([
            [int(center[0] + radius*np.cos(theta)),
             int(center[1] + radius*np.sin(theta))]
            for theta in angles
        ], dtype=np.int32)
        return pts.reshape((-1, 1, 2))