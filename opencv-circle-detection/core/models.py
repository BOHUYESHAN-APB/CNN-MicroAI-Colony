from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Dict
import json
import numpy as np
from pathlib import Path
import datetime

@dataclass
class Colony:
    """菌落类，存储菌落的位置、大小和抑菌圈信息"""
    center: Tuple[int, int]
    radius: int
    contour: np.ndarray
    primary_inhibition_zone: Optional[Tuple[int, int, int]] = None  # 主抑菌圈
    secondary_inhibition_zone: Optional[Tuple[int, int, int]] = None  # 次级抑菌圈（半透明）
    overlap_zones: List[Tuple[int, int, int]] = field(default_factory=list)  # 重叠区域
    
    # 新增属性
    detection_score: float = 0.0  # 检测质量评分
    measurements: Dict[str, float] = field(default_factory=dict)  # 测量数据
    annotations: List[str] = field(default_factory=list)  # 标注信息
    
    def calculate_measurements(self, mm_per_pixel: float) -> None:
        """计算各种测量数据"""
        # 滤纸片尺寸
        self.measurements['filter_diameter'] = 2 * self.radius * mm_per_pixel
        
        # 主抑菌圈测量
        if self.primary_inhibition_zone:
            x, y, r = self.primary_inhibition_zone
            diameter = 2 * r * mm_per_pixel
            self.measurements['primary_zone_diameter'] = diameter
            self.measurements['primary_zone_width'] = (diameter - 6.0) / 2  # 6.0mm是标准滤纸片直径
        
        # 次级抑菌圈测量
        if self.secondary_inhibition_zone:
            x, y, r = self.secondary_inhibition_zone
            diameter = 2 * r * mm_per_pixel
            self.measurements['secondary_zone_diameter'] = diameter
            self.measurements['secondary_zone_width'] = (diameter - 6.0) / 2
        
        # 重叠区域测量
        if self.overlap_zones:
            total_area = sum(np.pi * r * r * (mm_per_pixel ** 2)
                           for _, _, r in self.overlap_zones)
            self.measurements['overlap_area'] = total_area
            self.measurements['overlap_count'] = len(self.overlap_zones)
    
    def add_annotation(self, text: str) -> None:
        """添加标注信息"""
        self.annotations.append(text)
    
    def to_dict(self) -> dict:
        """转换为字典格式，用于JSON序列化"""
        return {
            'center': self.center,
            'radius': self.radius,
            'detection_score': self.detection_score,
            'measurements': self.measurements,
            'annotations': self.annotations,
            'primary_zone': self.primary_inhibition_zone,
            'secondary_zone': self.secondary_inhibition_zone,
            'overlap_zones': self.overlap_zones
        }

@dataclass
class PetriDish:
    """培养皿类，存储培养皿的位置、大小和包含的菌落"""
    center: Tuple[int, int]
    radius: int
    colonies: List[Colony]
    diameter_mm: float  # 培养皿直径（毫米）
    
    # 新增属性
    detection_score: float = 0.0  # 检测质量评分
    analysis_timestamp: str = field(default_factory=lambda: datetime.datetime.now().isoformat())
    plate_id: str = ''  # 培养皿标识
    
    def get_mm_per_pixel(self) -> float:
        """获取像素到毫米的转换比例"""
        return self.diameter_mm / (2 * self.radius)
    
    def update_measurements(self) -> None:
        """更新所有菌落的测量数据"""
        mm_per_pixel = self.get_mm_per_pixel()
        for colony in self.colonies:
            colony.calculate_measurements(mm_per_pixel)
    
    def get_summary(self) -> dict:
        """获取分析摘要"""
        return {
            'plate_id': self.plate_id,
            'timestamp': self.analysis_timestamp,
            'plate_diameter_mm': self.diameter_mm,
            'colony_count': len(self.colonies),
            'detection_score': self.detection_score,
            'has_inhibition_zones': any(c.primary_inhibition_zone for c in self.colonies),
            'has_overlaps': any(c.overlap_zones for c in self.colonies)
        }
    
    def export_data(self, output_path: Path, include_annotations: bool = True) -> None:
        """导出分析数据"""
        data = {
            'plate_info': {
                'id': self.plate_id,
                'timestamp': self.analysis_timestamp,
                'diameter_mm': self.diameter_mm,
                'center': self.center,
                'radius': self.radius,
                'detection_score': self.detection_score
            },
            'colonies': [colony.to_dict() for colony in self.colonies]
        }
        
        if not include_annotations:
            for colony_data in data['colonies']:
                colony_data.pop('annotations', None)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def validate_detection(self) -> bool:
        """验证检测结果的合理性"""
        if not self.colonies:
            return False
            
        # 检查菌落位置
        for colony in self.colonies:
            dx = colony.center[0] - self.center[0]
            dy = colony.center[1] - self.center[1]
            dist = np.sqrt(dx*dx + dy*dy)
            if dist > self.radius * 0.9:  # 菌落不应太靠近培养皿边缘
                return False
        
        # 检查菌落间距
        for i, c1 in enumerate(self.colonies):
            for j, c2 in enumerate(self.colonies[i+1:], i+1):
                dx = c1.center[0] - c2.center[0]
                dy = c1.center[1] - c2.center[1]
                dist = np.sqrt(dx*dx + dy*dy)
                if dist < (c1.radius + c2.radius):  # 菌落不应重叠
                    return False
        
        return True