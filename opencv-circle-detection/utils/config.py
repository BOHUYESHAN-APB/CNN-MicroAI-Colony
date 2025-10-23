from dataclasses import dataclass
from typing import Tuple, Dict

@dataclass
class DetectionConfig:
    """检测相关配置"""
    # 培养皿检测参数
    plate_min_radius_ratio: float = 1/3  # 培养皿最小半径与图像高度的比例
    plate_max_radius_ratio: float = 1/1.8  # 培养皿最大半径与图像高度的比例
    plate_detection_params: Dict = None
    
    def __post_init__(self):
        self.plate_detection_params = {
            'dp': 1,  # 累加器分辨率
            'minDist': 400,  # 最小圆心距离
            'param1': 50,  # Canny边缘检测高阈值
            'param2': 35,  # 累加器阈值
        }

@dataclass
class ColonyConfig:
    """菌落检测相关配置"""
    # 菌落尺寸限制
    min_radius_ratio: float = 0.03  # 最小半径与培养皿半径的比例
    max_radius_ratio: float = 0.15  # 最大半径与培养皿半径的比例
    
    # 形状过滤参数
    min_circularity: float = 0.7  # 最小圆形度
    min_compactness: float = 0.8  # 最小紧凑度
    min_aspect_ratio: float = 0.8  # 最小长宽比
    
    # 位置限制
    max_distance_ratio: float = 0.9  # 到培养皿中心的最大距离与培养皿半径的比例
    # Hough 默认搜索参数（若 px/mm 可用，会基于直径换算）
    hough_dp: float = 1.2
    hough_minDist_factor: float = 1.8  # 与预期半径的乘子来作为 minDist
    # 对于未标定情况的像素范围回退
    fallback_min_radius_px: int = 8
    fallback_max_radius_px: int = 40

@dataclass
class InhibitionZoneConfig:
    """抑菌圈检测相关配置"""
    # 标准滤纸片尺寸（毫米）
    filter_paper_diameter_mm: float = 6.0
    # 主抑菌圈半径至少应是滤纸或孔洞半径的多少倍 / 像素下限
    primary_zone_min_ratio: float = 1.6
    primary_zone_min_radius_px: int = 16
    
    # 搜索范围
    max_radius_multiplier: float = 5.0  # 相对于菌落半径的最大搜索半径倍数
    max_plate_radius_ratio: float = 0.8  # 最大不超过培养皿半径的比例
    
    # 阈值参数
    primary_zone_thresholds: Dict[str, int] = None  # 主抑菌圈阈值
    secondary_zone_thresholds: Dict[str, int] = None  # 次级抑菌圈阈值
    
    def __post_init__(self):
        self.primary_zone_thresholds = {
            'low': 40,
            'high': 180
        }
        self.secondary_zone_thresholds = {
            'low': 70,
            'high': 150
        }
        # Hough/验证的默认值针对滤纸片和孔洞
        self.default_for_filter_paper = {
            'hough_param1': 60,
            'hough_param2': 28,
            'brightness_threshold': 120,
            'max_std_dev': 25.0,
            'radius_factor_min': 0.85,
            'radius_factor_max': 1.15
        }
        self.default_for_hole = {
            'hough_param1': 40,
            'hough_param2': 12,
            'brightness_threshold': 90,
            'max_std_dev': 35.0,
            'radius_factor_min': 0.8,
            'radius_factor_max': 1.2
        }

@dataclass
class ImageProcessingConfig:
    """图像处理相关配置"""
    # 预处理参数
    gaussian_blur_kernel: Tuple[int, int] = (9, 9)
    gaussian_blur_sigma: float = 2.0
    
    # CLAHE参数
    clahe_clip_limit: float = 2.0
    clahe_grid_size: Tuple[int, int] = (8, 8)
    
    # 形态学处理参数
    morph_kernel_small: Tuple[int, int] = (3, 3)
    morph_kernel_large: Tuple[int, int] = (5, 5)
    # 顶帽／闭运算内核，用于增强微弱边缘
    tophat_kernel: Tuple[int, int] = (15, 15)

@dataclass
class VisualizationConfig:
    """可视化相关配置"""
    # 颜色配置 (B, G, R)
    plate_color: Tuple[int, int, int] = (0, 255, 0)  # 绿色
    colony_color: Tuple[int, int, int] = (0, 0, 255)  # 红色
    contour_color: Tuple[int, int, int] = (255, 0, 0)  # 蓝色
    primary_zone_color: Tuple[int, int, int] = (255, 255, 0)  # 青色
    secondary_zone_color: Tuple[int, int, int] = (0, 255, 255)  # 黄色
    overlap_zone_color: Tuple[int, int, int] = (255, 0, 255)  # 粉色
    
    # 线条宽度
    plate_thickness: int = 2
    colony_thickness: int = 2
    contour_thickness: int = 1
    zone_thickness: int = 2

class Config:
    """全局配置类"""
    def __init__(self):
        self.detection = DetectionConfig()
        self.colony = ColonyConfig()
        self.inhibition_zone = InhibitionZoneConfig()
        self.image_processing = ImageProcessingConfig()
        self.visualization = VisualizationConfig()
        # Tuned profiles for special cases
        self.profiles = {
            'dark_blob': {
                'tophat_kernel': (7, 7),
                'clahe_clip': 1.0,
                'minArea': 20,
                'maxArea': 4000,
                'minCircularity': 0.12,
                'minInertiaRatio': 0.05
            }
        }
        
    @classmethod
    def default(cls) -> 'Config':
        """返回默认配置"""
        return cls()