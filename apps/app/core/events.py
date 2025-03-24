"""
Core event classes
核心事件类
"""
from .models.image_data import ImageData

class ImageLoadedEvent:
    """Image loaded event"""
    
    def __init__(self, image_data: ImageData):
        self.image_data = image_data

class ProcessingCompletedEvent:
    """Processing completed event"""
    
    def __init__(self, image_data: ImageData, results=None):
        self.image_data = image_data
        self.results = results
