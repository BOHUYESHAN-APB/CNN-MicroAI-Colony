"""
Image processing service implementation
图像处理服务实现
"""
import cv2
import numpy as np
import logging
from ..models.colony_detector import ColonyDetector  # 保持相对导入路径
from ...utils.image_preprocessing import PreprocessingConfig

logger = logging.getLogger(__name__)

class ImageProcessor:
    def __init__(self, config=None):
        self.detector = ColonyDetector()
        self.config = config or PreprocessingConfig()
        
    def process_image(self, image_path):
        """Process single image and return results"""
        try:
            # Load and preprocess image
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"Failed to load image: {image_path}")
                
            # Perform detection
            results = self.detector.detect(image)
            
            # Post-process results
            processed = self._post_process(results)
            
            return {
                'image': image,
                'results': processed,
                'stats': self._calculate_stats(processed)
            }
            
        except Exception as e:
            logger.error(f"Error processing image {image_path}: {str(e)}")
            raise
            
    def _post_process(self, detections):
        """Filter and format detection results"""
        # Implementation from original colony_detector.py
        pass
        
    def _calculate_stats(self, detections):
        """Calculate statistics from detections"""
        # Implementation from original colony_detector.py
        pass
