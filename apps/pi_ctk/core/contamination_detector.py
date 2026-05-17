"""污染检测服务 - 基于形态和颜色异常检测"""
import cv2
import numpy as np
from typing import List, Tuple, Dict


class ContaminationDetector:
    """污染检测器（基于异常检测，不依赖模型）"""

    def __init__(self):
        self.circularity_threshold = 0.6  # 圆形度阈值
        self.size_outlier_factor = 3.0    # 尺寸异常因子

    def detect_contamination(self, image_bgr: np.ndarray,
                            boxes: np.ndarray,
                            scores: np.ndarray) -> List[bool]:
        """
        检测污染菌落

        Args:
            image_bgr: 原始图像
            boxes: 边界框 [[x1,y1,x2,y2], ...]
            scores: 置信度分数

        Returns:
            污染标记列表: [True=污染, False=正常, ...]
        """
        if len(boxes) == 0:
            return []

        contamination_flags = []

        # 计算所有菌落的面积
        areas = []
        for box in boxes:
            x1, y1, x2, y2 = box
            area = (x2 - x1) * (y2 - y1)
            areas.append(area)

        mean_area = np.mean(areas)
        std_area = np.std(areas)

        for i, box in enumerate(boxes):
            x1, y1, x2, y2 = map(int, box)
            area = areas[i]

            # 1. 形态异常检测
            circularity = self._calculate_circularity(image_bgr, box)

            # 2. 尺寸异常检测
            size_outlier = (area > mean_area + self.size_outlier_factor * std_area or
                           area < mean_area - self.size_outlier_factor * std_area)

            # 3. 颜色异常检测
            color_outlier = self._is_color_outlier(image_bgr, box, boxes)

            # 综合判断
            is_contaminated = (circularity < self.circularity_threshold or
                             size_outlier or
                             color_outlier)

            contamination_flags.append(is_contaminated)

        return contamination_flags

    def _calculate_circularity(self, image: np.ndarray, box: np.ndarray) -> float:
        """计算圆形度（4π*面积/周长²）"""
        x1, y1, x2, y2 = map(int, box)
        roi = image[y1:y2, x1:x2]

        if roi.size == 0:
            return 1.0

        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if not contours:
            return 1.0

        # 选择最大轮廓
        largest = max(contours, key=cv2.contourArea)
        area = cv2.contourArea(largest)
        perimeter = cv2.arcLength(largest, True)

        if perimeter == 0:
            return 0.0

        circularity = 4 * np.pi * area / (perimeter ** 2)
        return min(circularity, 1.0)

    def _is_color_outlier(self, image: np.ndarray, box: np.ndarray,
                         all_boxes: np.ndarray) -> bool:
        """检测颜色是否异常（与主流颜色差异大）"""
        x1, y1, x2, y2 = map(int, box)
        roi = image[y1:y2, x1:x2]

        if roi.size == 0:
            return False

        # 计算当前ROI的平均颜色
        mean_color = cv2.mean(roi)[:3]

        # 计算所有菌落的平均颜色
        all_colors = []
        for other_box in all_boxes:
            ox1, oy1, ox2, oy2 = map(int, other_box)
            other_roi = image[oy1:oy2, ox1:ox2]
            if other_roi.size > 0:
                all_colors.append(cv2.mean(other_roi)[:3])

        if not all_colors:
            return False

        # 计算颜色距离
        median_color = np.median(all_colors, axis=0)
        color_distance = np.linalg.norm(np.array(mean_color) - median_color)

        # 阈值：颜色距离超过50认为异常
        return color_distance > 50

    def draw_contamination_marks(self, image: np.ndarray,
                                boxes: np.ndarray,
                                contamination_flags: List[bool]) -> np.ndarray:
        """绘制污染标记"""
        annotated = image.copy()

        for box, is_contaminated in zip(boxes, contamination_flags):
            if is_contaminated:
                x1, y1, x2, y2 = map(int, box)

                # 红色虚线框
                cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 0, 255), 2, cv2.LINE_AA)

                # 添加警告标签
                cv2.putText(annotated, "CONTAMINATED", (x1, y1 - 10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

        return annotated

    def get_statistics(self, contamination_flags: List[bool]) -> Dict[str, int]:
        """统计污染情况"""
        stats = {
            'total': len(contamination_flags),
            'contaminated': sum(contamination_flags),
            'clean': len(contamination_flags) - sum(contamination_flags)
        }
        return stats
