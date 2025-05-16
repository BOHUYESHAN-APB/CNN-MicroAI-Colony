from dataclasses import dataclass
from typing import List, Optional, Tuple
import numpy as np

@dataclass
class Colony:
    """菌落类，存储菌落的位置、大小和抑菌圈信息"""
    center: Tuple[int, int]
    radius: int
    contour: np.ndarray
    primary_inhibition_zone: Optional[Tuple[int, int, int]] = None  # 主抑菌圈
    secondary_inhibition_zone: Optional[Tuple[int, int, int]] = None  # 次级抑菌圈（半透明）
    overlap_zones: List[Tuple[int, int, int]] = None  # 重叠区域

@dataclass
class PetriDish:
    """培养皿类，存储培养皿的位置、大小和包含的菌落"""
    center: Tuple[int, int]
    radius: int
    colonies: List[Colony]
    diameter_mm: float  # 培养皿直径（毫米）