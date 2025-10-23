import cv2
import numpy as np
from typing import Tuple, Optional, Dict
from dataclasses import dataclass
from utils.logger import get_logger

logger = get_logger(__name__)

@dataclass
class ImageQuality:
    """图像质量评估结果"""
    brightness: float
    contrast: float
    noise_level: float
    blur_level: float
    score: float

class ImageProcessor:
    """图像处理类，提供各种图像增强和预处理功能"""
    
    def __init__(self):
        # 预处理参数
        self.gaussian_kernel_size = (9, 9)
        self.gaussian_sigma = 2.0
        self.clahe_clip_limit = 2.0
        self.clahe_grid_size = (8, 8)
    
    def preprocess(self, image: np.ndarray) -> np.ndarray:
        """图像预处理管线"""
        logger.info("开始图像预处理")
        # 转换为灰度图
        if len(image.shape) > 2:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
            
        # 高斯去噪
        denoised = cv2.GaussianBlur(gray, self.gaussian_kernel_size, self.gaussian_sigma)
        
        # CLAHE对比度增强
        clahe = cv2.createCLAHE(
            clipLimit=self.clahe_clip_limit,
            tileGridSize=self.clahe_grid_size
        )
        enhanced = clahe.apply(denoised)
        
        logger.info("预处理完成")
        return enhanced

    def preprocess_for_hole(self, image: np.ndarray, tophat_kernel: Tuple[int, int] = (15, 15)) -> np.ndarray:
        """
        专门用于透明孔/挖空目标的预处理：结合顶帽增强、拉普拉斯增强和 CLAHE。
        该流程能提升对比度弱的透明边界。
        """
        logger.info("开始用于孔洞的专用预处理")
        # 确保灰度
        if len(image.shape) > 2:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()

        # 轻度去噪
        denoised = cv2.GaussianBlur(gray, self.gaussian_kernel_size, self.gaussian_sigma)

        # 顶帽增强以突出亮度突变的小结构
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, tophat_kernel)
        tophat = cv2.morphologyEx(denoised, cv2.MORPH_TOPHAT, kernel)

        # Laplacian增强边缘
        lap = cv2.Laplacian(denoised, cv2.CV_64F, ksize=3)
        lap_normalized = cv2.normalize(lap, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)

        # 组合：以一定权重将原图、tophat和laplacian融合
        combined = cv2.addWeighted(denoised, 0.6, tophat, 0.2, 0)
        combined = cv2.addWeighted(combined, 0.7, lap_normalized, 0.3, 0)

        # CLAHE 增强对比
        clahe = cv2.createCLAHE(clipLimit=self.clahe_clip_limit, tileGridSize=self.clahe_grid_size)
        enhanced = clahe.apply(combined)

        logger.info("孔洞专用预处理完成")
        return enhanced
    
    def enhance_details(self, image: np.ndarray) -> np.ndarray:
        """增强图像细节"""
        logger.info("开始增强图像细节")
        # 使用不同尺度的Sobel算子
        gradients = []
        for ksize in [3, 5, 7]:
            sobelx = cv2.Sobel(image, cv2.CV_64F, 1, 0, ksize=ksize)
            sobely = cv2.Sobel(image, cv2.CV_64F, 0, 1, ksize=ksize)
            gradient = np.sqrt(sobelx**2 + sobely**2)
            gradients.append(cv2.normalize(gradient, None, 0, 255, cv2.NORM_MINMAX))
        
        # 合并不同尺度的结果
        result = np.mean(gradients, axis=0).astype(np.uint8)
        return result
    
    def remove_background(self, image: np.ndarray) -> np.ndarray:
        """移除背景"""
        logger.info("开始移除背景")
        # OTSU自适应阈值分割
        _, binary = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # 形态学操作改善分割结果
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        morphed = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
        morphed = cv2.morphologyEx(morphed, cv2.MORPH_CLOSE, kernel)
        
        # 应用掩码
        result = cv2.bitwise_and(image, image, mask=morphed)
        logger.info("细节增强完成")
        logger.info("背景移除完成")
        return result
    
    def denoise(self, image: np.ndarray, strength: float = 1.0) -> np.ndarray:
        """高级去噪"""
        logger.info(f"开始图像去噪，强度: {strength}")
        # 非局部均值去噪
        denoised = cv2.fastNlMeansDenoising(
            image,
            None,
            h=10 * strength,
            templateWindowSize=7,
            searchWindowSize=21
        )
        
        # 双边滤波进一步改善
        refined = cv2.bilateralFilter(
            denoised,
            d=5,
            sigmaColor=50 * strength,
            sigmaSpace=50 * strength
        )
        
        logger.info("去噪完成")
        return refined
    
    def enhance_contrast(self, image: np.ndarray) -> np.ndarray:
        """自适应对比度增强"""
        logger.info("开始增强对比度")
        # 计算图像统计信息
        mean, std = cv2.meanStdDev(image)
        
        # 根据图像特征调整CLAHE参数
        if std[0] < 30:  # 低对比度图像
            clip_limit = 3.0
            grid_size = (16, 16)
        else:  # 正常对比度图像
            clip_limit = 2.0
            grid_size = (8, 8)
        
        clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=grid_size)
        enhanced = clahe.apply(image)
        logger.info(f"对比度增强完成，使用参数: clip_limit={clip_limit}, grid_size={grid_size}")
        return enhanced
    
    def evaluate_quality(self, image: np.ndarray) -> ImageQuality:
        """评估图像质量"""
        logger.info("开始评估图像质量")
        # 计算亮度
        brightness = np.mean(image)
        
        # 计算对比度
        contrast = np.std(image)
        
        # 评估噪声水平
        noise_level = self._estimate_noise(image)
        
        # 评估模糊程度
        blur_level = self._estimate_blur(image)
        
        # 综合评分
        score = self._calculate_quality_score(
            brightness, contrast, noise_level, blur_level
        )
        
        quality = ImageQuality(
            brightness=brightness,
            contrast=contrast,
            noise_level=noise_level,
            blur_level=blur_level,
            score=score
        )
        
        logger.info(
            f"图像质量评估完成:\n"
            f"- 亮度: {brightness:.1f}\n"
            f"- 对比度: {contrast:.1f}\n"
            f"- 噪声水平: {noise_level:.1f}\n"
            f"- 模糊程度: {blur_level:.1f}\n"
            f"- 总分: {score:.1f}/10.0"
        )
        
        return quality
    
    def _estimate_noise(self, image: np.ndarray) -> float:
        """评估图像噪声水平"""
        logger.debug("评估图像噪声水平")
        # 使用拉普拉斯算子
        laplacian = cv2.Laplacian(image, cv2.CV_64F)
        noise_level = np.var(laplacian)
        return noise_level
    
    def _estimate_blur(self, image: np.ndarray) -> float:
        """评估图像模糊程度"""
        logger.debug("评估图像模糊程度")
        # 使用拉普拉斯算子的方差
        laplacian = cv2.Laplacian(image, cv2.CV_64F)
        blur_level = 1.0 / (np.var(laplacian) + 1e-8)
        return blur_level
    
    def _calculate_quality_score(self, brightness: float, contrast: float,
                             noise_level: float, blur_level: float) -> float:
        """计算综合图像质量评分"""
        logger.debug("计算综合图像质量评分")
        # 归一化各指标
        brightness_score = 1.0 - abs(brightness - 128) / 128
        contrast_score = min(contrast / 50, 1.0)
        noise_score = 1.0 / (1.0 + noise_level / 1000)
        blur_score = 1.0 / (1.0 + blur_level * 100)
        
        # 加权平均
        weights = {
            'brightness': 0.2,
            'contrast': 0.3,
            'noise': 0.25,
            'blur': 0.25
        }
        
        score = (weights['brightness'] * brightness_score +
                weights['contrast'] * contrast_score +
                weights['noise'] * noise_score +
                weights['blur'] * blur_score)
        
        return score * 10  # 转换到0-10分制
    
    def suggest_preprocessing(self, quality: ImageQuality) -> Dict[str, bool]:
        """根据图像质量建议预处理步骤"""
        suggestions = {
            'denoise': quality.noise_level > 1000,
            'enhance_contrast': quality.contrast < 40,
            'enhance_details': quality.blur_level > 0.1,
            'remove_background': quality.brightness > 200 or quality.brightness < 50
        }
        # 记录处理建议
        logger.info("图像处理建议:")
        for step, needed in suggestions.items():
            if needed:
                logger.info(f"- 建议执行: {step}")
        
        return suggestions