"""蓝白斑检测服务 - 基于颜色分析"""
import cv2
import numpy as np
from typing import List, Tuple


class BlueWhiteColonyService:
    """蓝白斑检测服务（基于HSV颜色空间）"""

    def __init__(self):
        # 蓝色范围（HSV）
        self.blue_lower = np.array([100, 50, 50])
        self.blue_upper = np.array([130, 255, 255])

        # 白色范围（HSV）
        self.white_lower = np.array([0, 0, 200])
        self.white_upper = np.array([180, 30, 255])

    def classify_colonies(self, image_bgr: np.ndarray,
                         boxes: np.ndarray) -> List[str]:
        """
        对检测到的菌落进行蓝白斑分类

        Args:
            image_bgr: 原始图像
            boxes: 边界框数组 [[x1,y1,x2,y2], ...]

        Returns:
            类型列表: ['standard', 'blue', 'white', ...]
        """
        hsv = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2HSV)
        color_types = []

        for box in boxes:
            x1, y1, x2, y2 = map(int, box)

            # 提取ROI
            roi = hsv[y1:y2, x1:x2]
            if roi.size == 0:
                color_types.append('standard')
                continue

            # 检测蓝色
            blue_mask = cv2.inRange(roi, self.blue_lower, self.blue_upper)
            blue_ratio = np.sum(blue_mask > 0) / roi.size

            # 检测白色
            white_mask = cv2.inRange(roi, self.white_lower, self.white_upper)
            white_ratio = np.sum(white_mask > 0) / roi.size

            # 分类
            if blue_ratio > 0.3:
                color_types.append('blue')
            elif white_ratio > 0.5:
                color_types.append('white')
            else:
                color_types.append('standard')

        return color_types

    def draw_colored_boxes(self, image: np.ndarray,
                          boxes: np.ndarray,
                          color_types: List[str]) -> np.ndarray:
        """绘制带颜色分类的边界框"""
        annotated = image.copy()

        color_map = {
            'blue': (255, 0, 0),      # 蓝色
            'white': (255, 255, 255),  # 白色
            'standard': (0, 255, 0)    # 绿色
        }

        for box, ctype in zip(boxes, color_types):
            x1, y1, x2, y2 = map(int, box)
            color = color_map.get(ctype, (0, 255, 0))

            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)

            # 添加标签
            label = ctype.upper()
            cv2.putText(annotated, label, (x1, y1 - 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

        return annotated

    def get_statistics(self, color_types: List[str]) -> dict:
        """统计蓝白斑数量"""
        stats = {
            'total': len(color_types),
            'blue': color_types.count('blue'),
            'white': color_types.count('white'),
            'standard': color_types.count('standard')
        }
        return stats
