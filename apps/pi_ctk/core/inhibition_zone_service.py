"""抑菌圈检测服务 - 集成到树莓派CTk应用"""
import cv2
import numpy as np
from pathlib import Path
from typing import Optional, Tuple, List
from dataclasses import dataclass


@dataclass
class InhibitionZoneResult:
    """抑菌圈检测结果"""
    dish_center: Tuple[int, int]
    dish_radius: int
    substances: List[Tuple[int, int, int]]  # (x, y, radius)
    zones: List[Tuple[int, int, int]]  # (x, y, radius)
    mode: str  # 'filter_paper', 'hole', 'auto'
    annotated_image: np.ndarray


class InhibitionZoneService:
    """抑菌圈检测服务（简化版，无外部依赖）"""

    def __init__(self, plate_diameter_mm: float = 90.0):
        self.plate_diameter_mm = plate_diameter_mm
        self.px_per_mm = None

    def detect(self, image_bgr: np.ndarray, mode: str = 'auto') -> Optional[InhibitionZoneResult]:
        """
        检测抑菌圈
        mode: 'filter_paper' | 'hole' | 'auto'
        """
        gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (9, 9), 2)

        # 1. 检测培养皿
        dish = self._detect_dish(blurred, image_bgr.shape)
        if dish is None:
            return None

        dish_x, dish_y, dish_r = dish
        self.px_per_mm = dish_r / (self.plate_diameter_mm / 2)

        # 2. 检测抑菌物质
        substances = []
        detected_mode = mode

        if mode == 'auto':
            # 先尝试滤纸片
            substances = self._detect_filter_paper(blurred, dish)
            if len(substances) == 0:
                # 再尝试挖孔
                substances = self._detect_holes(blurred, dish)
                detected_mode = 'hole' if substances else 'filter_paper'
            else:
                detected_mode = 'filter_paper'
        elif mode == 'filter_paper':
            substances = self._detect_filter_paper(blurred, dish)
        elif mode == 'hole':
            substances = self._detect_holes(blurred, dish)

        # 3. 检测抑菌圈
        zones = []
        for sx, sy, sr in substances:
            zone = self._detect_zone(blurred, dish, (sx, sy, sr))
            if zone:
                zones.append(zone)

        # 4. 绘制标注
        annotated = self._draw_annotations(image_bgr.copy(), dish, substances, zones)

        return InhibitionZoneResult(
            dish_center=(dish_x, dish_y),
            dish_radius=dish_r,
            substances=substances,
            zones=zones,
            mode=detected_mode,
            annotated_image=annotated
        )

    def _detect_dish(self, gray: np.ndarray, shape: Tuple) -> Optional[Tuple[int, int, int]]:
        """检测培养皿"""
        circles = cv2.HoughCircles(
            gray,
            cv2.HOUGH_GRADIENT,
            dp=1,
            minDist=400,
            param1=50,
            param2=35,
            minRadius=int(shape[0] / 3),
            maxRadius=int(shape[0] / 1.8)
        )

        if circles is not None:
            circles = np.uint16(np.around(circles))
            x, y, r = circles[0, 0]
            return (int(x), int(y), int(r))
        return None

    def _detect_filter_paper(self, gray: np.ndarray, dish: Tuple[int, int, int]) -> List[Tuple[int, int, int]]:
        """检测滤纸片（亮色圆形）"""
        dx, dy, dr = dish
        mask = np.zeros_like(gray)
        cv2.circle(mask, (dx, dy), int(dr * 0.9), 255, -1)

        # 亮度阈值
        _, bright = cv2.threshold(gray, 120, 255, cv2.THRESH_BINARY)
        masked = cv2.bitwise_and(bright, mask)

        circles = cv2.HoughCircles(
            masked,
            cv2.HOUGH_GRADIENT,
            dp=1,
            minDist=50,
            param1=50,
            param2=20,
            minRadius=int(self.px_per_mm * 2),
            maxRadius=int(self.px_per_mm * 10)
        )

        substances = []
        if circles is not None:
            circles = np.uint16(np.around(circles))
            for x, y, r in circles[0, :]:
                substances.append((int(x), int(y), int(r)))

        return substances

    def _detect_holes(self, gray: np.ndarray, dish: Tuple[int, int, int]) -> List[Tuple[int, int, int]]:
        """检测挖孔（暗色圆形）"""
        dx, dy, dr = dish
        mask = np.zeros_like(gray)
        cv2.circle(mask, (dx, dy), int(dr * 0.9), 255, -1)

        # 反转图像
        inverted = cv2.bitwise_not(gray)
        _, dark = cv2.threshold(inverted, 120, 255, cv2.THRESH_BINARY)
        masked = cv2.bitwise_and(dark, mask)

        circles = cv2.HoughCircles(
            masked,
            cv2.HOUGH_GRADIENT,
            dp=1,
            minDist=50,
            param1=50,
            param2=20,
            minRadius=int(self.px_per_mm * 2),
            maxRadius=int(self.px_per_mm * 10)
        )

        substances = []
        if circles is not None:
            circles = np.uint16(np.around(circles))
            for x, y, r in circles[0, :]:
                substances.append((int(x), int(y), int(r)))

        return substances

    def _detect_zone(self, gray: np.ndarray, dish: Tuple[int, int, int],
                     substance: Tuple[int, int, int]) -> Optional[Tuple[int, int, int]]:
        """检测抑菌圈"""
        sx, sy, sr = substance
        dx, dy, dr = dish

        # 在物质周围搜索抑菌圈
        search_radius = int(sr * 3)
        roi_size = search_radius * 2

        x1 = max(0, sx - search_radius)
        y1 = max(0, sy - search_radius)
        x2 = min(gray.shape[1], sx + search_radius)
        y2 = min(gray.shape[0], sy + search_radius)

        roi = gray[y1:y2, x1:x2]
        if roi.size == 0:
            return None

        # 边缘检测
        edges = cv2.Canny(roi, 50, 150)

        circles = cv2.HoughCircles(
            edges,
            cv2.HOUGH_GRADIENT,
            dp=1,
            minDist=30,
            param1=50,
            param2=20,
            minRadius=int(sr * 1.2),
            maxRadius=int(sr * 3)
        )

        if circles is not None:
            circles = np.uint16(np.around(circles))
            # 选择最接近物质中心的圆
            for x, y, r in circles[0, :]:
                abs_x = x1 + x
                abs_y = y1 + y
                dist = np.sqrt((abs_x - sx)**2 + (abs_y - sy)**2)
                if dist < sr * 0.5:  # 圆心接近物质中心
                    return (int(abs_x), int(abs_y), int(r))

        return None

    def _draw_annotations(self, image: np.ndarray, dish: Tuple[int, int, int],
                         substances: List[Tuple[int, int, int]],
                         zones: List[Tuple[int, int, int]]) -> np.ndarray:
        """绘制标注"""
        # 培养皿（蓝色）
        dx, dy, dr = dish
        cv2.circle(image, (dx, dy), dr, (255, 0, 0), 2)

        # 抑菌物质（红色）
        for sx, sy, sr in substances:
            cv2.circle(image, (sx, sy), sr, (0, 0, 255), 2)
            diameter_mm = (sr * 2) / self.px_per_mm
            cv2.putText(image, f"{diameter_mm:.1f}mm", (sx - 30, sy - sr - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)

        # 抑菌圈（绿色半透明）
        overlay = image.copy()
        for zx, zy, zr in zones:
            cv2.circle(overlay, (zx, zy), zr, (0, 255, 0), 2)
            diameter_mm = (zr * 2) / self.px_per_mm
            cv2.putText(overlay, f"Zone: {diameter_mm:.1f}mm", (zx - 40, zy + zr + 20),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

        cv2.addWeighted(overlay, 0.7, image, 0.3, 0, image)

        return image
