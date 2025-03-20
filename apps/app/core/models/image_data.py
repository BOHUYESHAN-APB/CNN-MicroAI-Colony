from dataclasses import dataclass
from typing import Optional, List
import numpy as np
import os

@dataclass
class ImageData:
    """图像数据模型，支持处理历史追溯"""
    original: np.ndarray  # 原始图像数据
    path: str             # 文件路径
    metadata: dict        # 元数据
    parent: Optional['ImageData'] = None  # 上级处理结果
    annotations: Optional[dict] = None    # 分析标注数据

    @property
    def processing_history(self) -> List['ImageData']:
        """获取完整处理历史记录"""
        history = []
        current = self
        while current:
            history.append(current)
            current = current.parent
        return list(reversed(history))  # 按处理顺序返回
    
    @property
    def current_image(self) -> np.ndarray:
        """获取当前处理阶段的图像"""
        return self.original
        
    def get_metadata_field(self, key: str, default=None):
        """安全获取元数据字段"""
        return self.metadata.get(key, default)
