import cv2
import numpy as np
from typing import Tuple, Optional

class ImageProcessor:
    """图像处理工具类"""
    
    @staticmethod
    def enhance_contrast(image: np.ndarray, clip_limit: float = 2.0,
                        tile_grid_size: Tuple[int, int] = (8, 8)) -> np.ndarray:
        """增强图像对比度"""
        clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid_size)
        if len(image.shape) == 3:
            # 彩色图像，在LAB空间增强L通道
            lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
            lab[:,:,0] = clahe.apply(lab[:,:,0])
            return cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
        else:
            # 灰度图像直接增强
            return clahe.apply(image)

    @staticmethod
    def denoise(image: np.ndarray, method: str = 'gaussian', kernel_size: int = 5) -> np.ndarray:
        """去噪处理
        
        参数:
            method: 'gaussian' | 'median' | 'bilateral'
            kernel_size: 核大小（奇数）
        """
        if method == 'gaussian':
            return cv2.GaussianBlur(image, (kernel_size, kernel_size), 0)
        elif method == 'median':
            return cv2.medianBlur(image, kernel_size)
        elif method == 'bilateral':
            return cv2.bilateralFilter(image, kernel_size, 75, 75)
        else:
            raise ValueError(f"不支持的去噪方法: {method}")

    @staticmethod
    def create_circular_mask(image_shape: Tuple[int, int],
                           center: Tuple[int, int],
                           radius: int) -> np.ndarray:
        """创建圆形掩码"""
        mask = np.zeros(image_shape[:2], dtype=np.uint8)
        cv2.circle(mask, center, radius, 255, -1)
        return mask

    @staticmethod
    def apply_morphology(binary: np.ndarray,
                        operation: str = 'open',
                        kernel_shape: str = 'ellipse',
                        kernel_size: int = 5) -> np.ndarray:
        """应用形态学操作
        
        参数:
            operation: 'open' | 'close' | 'dilate' | 'erode'
            kernel_shape: 'ellipse' | 'rect' | 'cross'
            kernel_size: 核大小
        """
        # 创建结构元素
        if kernel_shape == 'ellipse':
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
        elif kernel_shape == 'rect':
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_size, kernel_size))
        elif kernel_shape == 'cross':
            kernel = cv2.getStructuringElement(cv2.MORPH_CROSS, (kernel_size, kernel_size))
        else:
            raise ValueError(f"不支持的核形状: {kernel_shape}")

        # 应用形态学操作
        if operation == 'open':
            return cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
        elif operation == 'close':
            return cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        elif operation == 'dilate':
            return cv2.dilate(binary, kernel)
        elif operation == 'erode':
            return cv2.erode(binary, kernel)
        else:
            raise ValueError(f"不支持的形态学操作: {operation}")

    @staticmethod
    def detect_edges(image: np.ndarray, method: str = 'sobel',
                    ksize: int = 3) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        """边缘检测
        
        参数:
            method: 'sobel' | 'scharr' | 'laplacian' | 'canny'
            ksize: Sobel算子大小
        
        返回:
            magnitude: 边缘强度图
            direction: 边缘方向图（仅Sobel和Scharr方法返回）
        """
        if method in ['sobel', 'scharr']:
            # Sobel/Scharr边缘检测
            if method == 'sobel':
                dx = cv2.Sobel(image, cv2.CV_64F, 1, 0, ksize=ksize)
                dy = cv2.Sobel(image, cv2.CV_64F, 0, 1, ksize=ksize)
            else:  # Scharr
                dx = cv2.Scharr(image, cv2.CV_64F, 1, 0)
                dy = cv2.Scharr(image, cv2.CV_64F, 0, 1)
            
            magnitude = np.sqrt(dx**2 + dy**2)
            magnitude = cv2.normalize(magnitude, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
            direction = np.arctan2(dy, dx)
            return magnitude, direction
            
        elif method == 'laplacian':
            edges = cv2.Laplacian(image, cv2.CV_64F, ksize=ksize)
            magnitude = np.absolute(edges)
            magnitude = cv2.normalize(magnitude, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
            return magnitude, None
            
        elif method == 'canny':
            magnitude = cv2.Canny(image, 100, 200)
            return magnitude, None
            
        else:
            raise ValueError(f"不支持的边缘检测方法: {method}")

    @staticmethod
    def adaptive_threshold(image: np.ndarray,
                         block_size: int = 11,
                         c: int = 2) -> np.ndarray:
        """自适应阈值分割"""
        return cv2.adaptiveThreshold(
            image,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV,
            block_size,
            c
        )