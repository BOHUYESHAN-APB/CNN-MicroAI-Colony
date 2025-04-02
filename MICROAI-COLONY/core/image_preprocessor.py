"""
图像预处理模块
提供菌落分析前的图像增强和处理功能
"""

import cv2
import numpy as np
from PIL import Image

class ImagePreprocessor:
    def __init__(self):
        self.methods = {
            'grayscale': self.convert_grayscale,
            'clahe': self.clahe_enhancement,
            'gaussian_blur': self.gaussian_blur,
            'edge_detect': self.edge_detection,
            'watershed': self.watershed_segmentation
        }
        
        # 默认参数
        self.params = {
            'grayscale': {},
            'clahe': {'clip_limit': 2.0, 'grid_size': 8},
            'gaussian_blur': {'kernel_size': 3},
            'edge_detect': {'threshold1': 50, 'threshold2': 150},
            'watershed': {'marker_threshold': 0.3}
        }

    def process(self, image, methods=None, params=None):
        """执行图像预处理
        
        Args:
            image: 输入图像 (numpy数组或PIL Image)
            methods: 要应用的预处理方法列表
            params: 各预处理方法的参数字典
            
        Returns:
            处理后的图像 (numpy数组)
        """
        if params:
            for method, method_params in params.items():
                if method in self.params:
                    self.params[method].update(method_params)
        if isinstance(image, Image.Image):
            img = np.array(image)
        else:
            img = image.copy()
            
        methods = methods or ['grayscale']  # 默认使用灰度化
        
        for method in methods:
            if method in self.methods:
                img = self.methods[method](img, **self.params[method])
                
        return img

    def convert_grayscale(self, image, **kwargs):
        """转换为灰度图像"""
        if len(image.shape) == 2:
            return image
        return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    def histogram_equalization(self, image, clip_limit=2.0, grid_size=8):
        """CLAHE直方图均衡化"""
        clahe = cv2.createCLAHE(
            clipLimit=clip_limit,
            tileGridSize=(grid_size, grid_size)
        )
        return clahe.apply(image)

    def gaussian_blur(self, image, kernel_size=3):
        """高斯模糊降噪"""
        return cv2.GaussianBlur(
            image,
            (kernel_size, kernel_size),
            0
        )

    def clahe_enhancement(self, image, clip_limit=2.0, grid_size=8):
        """CLAHE对比度增强"""
        if len(image.shape) == 3:
            image = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(image)
            clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=(grid_size, grid_size))
            l = clahe.apply(l)
            image = cv2.merge((l, a, b))
            image = cv2.cvtColor(image, cv2.COLOR_LAB2BGR)
            return image
        else:
            clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=(grid_size, grid_size))
            return clahe.apply(image)

    def edge_detection(self, image, threshold1=50, threshold2=150):
        """Canny边缘检测"""
        edges = cv2.Canny(image, threshold1, threshold2)
        return cv2.bitwise_and(image, image, mask=edges)

    def watershed_segmentation(self, image, marker_threshold=0.3):
        """分水岭算法分割"""
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
            
        # 阈值处理
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        
        # 去除噪声
        kernel = np.ones((3,3), np.uint8)
        opening = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=2)
        
        # 确定背景区域
        sure_bg = cv2.dilate(opening, kernel, iterations=3)
        
        # 确定前景区域
        dist_transform = cv2.distanceTransform(opening, cv2.DIST_L2, 5)
        _, sure_fg = cv2.threshold(dist_transform, marker_threshold*dist_transform.max(), 255, 0)
        
        # 找到未知区域
        sure_fg = np.uint8(sure_fg)
        unknown = cv2.subtract(sure_bg, sure_fg)
        
        # 标记连通区域
        _, markers = cv2.connectedComponents(sure_fg)
        markers = markers + 1
        markers[unknown == 255] = 0
        
        # 应用分水岭算法
        if len(image.shape) == 3:
            markers = cv2.watershed(image, markers)
            image[markers == -1] = [0, 0, 255]  # 标记边界
        else:
            markers = cv2.watershed(cv2.cvtColor(image, cv2.COLOR_GRAY2BGR), markers)
            image[markers == -1] = 255  # 标记边界
            
        return image

    def get_available_methods(self):
        """获取可用预处理方法"""
        return list(self.methods.keys())

    def update_parameters(self, method, **kwargs):
        """更新预处理参数"""
        if method in self.params:
            self.params[method].update(kwargs)
