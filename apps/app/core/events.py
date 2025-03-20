from typing import Any
from dataclasses import dataclass
from ..models.image_data import ImageData

class Event:
    """基础事件类"""
    def dispatch(self):
        """分发事件到事件总线"""
        # 这里需要实现事件分发逻辑，例如：
        # EventBus.dispatch(self)
        pass

@dataclass
class ImageLoadedEvent(Event):
    """图像加载完成事件"""
    image_data: ImageData

@dataclass
class ProcessingCompletedEvent(Event):
    """图像处理完成事件"""
    result: ImageData
