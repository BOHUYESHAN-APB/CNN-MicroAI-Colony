from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Dict
import json
import numpy as np
from pathlib import Path
import datetime
from enum import Enum # Import Enum

# Define SubstanceTypeEnum to match detector.py
class SubstanceTypeEnum(Enum):
    FILTER_PAPER = 1
    HOLE = 2
    UNKNOWN = 0

@dataclass
class Colony: # Represents a detected substance (filter paper or hole)
    """抑菌物质类（滤纸片或孔洞），存储其位置、大小和相关抑菌圈信息"""
    center: Tuple[int, int]
    radius: int
    contour: Optional[np.ndarray] = None # Contour might not always be needed or generated
    substance_type: SubstanceTypeEnum = SubstanceTypeEnum.UNKNOWN # Type of substance
    
    # Inhibition zone details will be stored in the result dict from detector, not directly here
    # to keep this model simpler and focused on the substance itself.
    
    detection_score: float = 0.0  # Detection quality score for this substance
    measurements: Dict[str, float] = field(default_factory=dict)  # Measurement data (e.g., diameter in mm)
    annotations: List[str] = field(default_factory=list)  # Annotations

    def calculate_measurements(self, px_per_mm: Optional[float]) -> None:
        """计算物质的测量数据"""
        if px_per_mm and px_per_mm > 0:
            self.measurements['diameter_px'] = float(2 * self.radius)
            self.measurements['diameter_mm'] = (2 * self.radius) / px_per_mm
            self.measurements['area_px'] = np.pi * (self.radius ** 2)
            self.measurements['area_mm2'] = np.pi * ((self.radius / px_per_mm) ** 2)
        else:
            self.measurements['diameter_px'] = float(2 * self.radius)
            self.measurements['area_px'] = np.pi * (self.radius ** 2)
            # mm measurements cannot be calculated without px_per_mm

    def add_annotation(self, text: str) -> None:
        """添加标注信息"""
        self.annotations.append(text)

    def to_dict(self) -> dict:
        """转换为字典格式，用于JSON序列化或传递"""
        return {
            'center': self.center,
            'radius': self.radius,
            'substance_type': self.substance_type.name, # Store enum name
            'detection_score': self.detection_score,
            'measurements': self.measurements,
            'annotations': self.annotations,
            # Contour is not easily serializable to JSON, exclude by default
            # 'contour': self.contour.tolist() if self.contour is not None else None
        }

@dataclass
class PetriDish:
    """培养皿类，存储培养皿的位置、大小和包含的抑菌物质及检测结果"""
    center: Tuple[int, int]
    radius: int
    diameter_mm: float  # 培养皿直径（毫米）
    
    # Instead of a list of Colonies, the detector will return a more complex structure.
    # This class will primarily hold dish properties.
    # detected_substances_and_zones: List[Dict] = field(default_factory=list) # Stores results from detector

    detection_score: float = 0.0  # Detection quality score for the dish itself
    analysis_timestamp: str = field(default_factory=lambda: datetime.datetime.now().isoformat())
    plate_id: str = ''  # 培养皿标识
    px_per_mm: Optional[float] = None # Calculated pixels per mm

    def calculate_px_per_mm(self) -> Optional[float]:
        """计算并存储像素到毫米的转换比例"""
        if self.radius > 0 and self.diameter_mm > 0:
            self.px_per_mm = (2 * self.radius) / self.diameter_mm
            return self.px_per_mm
        return None

    def get_summary(self, detected_substances_count: int, detected_zones_count: int) -> dict:
        """获取分析摘要，需要外部传入物质和抑菌圈数量"""
        return {
            'plate_id': self.plate_id,
            'timestamp': self.analysis_timestamp,
            'plate_diameter_mm': self.diameter_mm,
            'plate_center_px': self.center,
            'plate_radius_px': self.radius,
            'px_per_mm': self.px_per_mm,
            'substances_detected': detected_substances_count,
            'inhibition_zones_detected': detected_zones_count,
            'dish_detection_score': self.detection_score,
        }

    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            'center': self.center,
            'radius': self.radius,
            'diameter_mm': self.diameter_mm,
            'detection_score': self.detection_score,
            'analysis_timestamp': self.analysis_timestamp,
            'plate_id': self.plate_id,
            'px_per_mm': self.px_per_mm
        }

    # export_data and validate_detection might need significant rework
    # based on how the main application uses these models and the detector's output.
    # For now, we simplify or comment them out.

    # def export_data(self, output_path: Path, detection_results: List[Dict], include_annotations: bool = True) -> None:
    #     """导出分析数据, detection_results is the list from detector.process_image_pipeline"""
    #     data = {
    #         'plate_info': self.to_dict(),
    #         'detection_results': detection_results # Directly use the structured results
    #     }
    #     # Annotation handling would need to be integrated with the new structure
    #     with open(output_path, 'w', encoding='utf-8') as f:
    #         json.dump(data, f, indent=2, ensure_ascii=False, default=lambda o: '<not serializable>')


    def validate_detection(self, substances: List[Colony]) -> bool:
        """
        验证检测到的物质是否在培养皿内。
        'substances' is a list of Colony objects detected within this dish.
        """
        if not substances: # If no substances, validation might depend on context (e.g., single central zone expected)
            return True # Or False, depending on expected behavior

        for substance in substances:
            dx = substance.center[0] - self.center[0]
            dy = substance.center[1] - self.center[1]
            # Distance from dish center to substance center + substance radius should be less than dish radius
            dist_to_substance_edge = np.sqrt(dx*dx + dy*dy) + substance.radius
            if dist_to_substance_edge > self.radius * 1.05:  # Allow slight tolerance
                # print(f"Substance {substance.center} R={substance.radius} is outside dish {self.center} R={self.radius}")
                return False
        return True