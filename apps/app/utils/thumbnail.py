"""
Thumbnail generation utilities
缩略图生成工具
"""
import cv2
import numpy as np
import logging
from pathlib import Path
from PyQt6.QtGui import QImage

from .image_preprocessing import load_image

logger = logging.getLogger(__name__)

def create_thumbnail(path, size=(64, 64)):
    """Create thumbnail from image file
    
    Args:
        path (str): Image file path
        size (tuple): Target thumbnail size (width, height)
        
    Returns:
        QImage: Thumbnail image, or None if failed
    """
    try:
        # Load image using our Unicode safe loader
        image = load_image(path)
        if image is None:
            raise ValueError("Cannot load image")
            
        # Get original dimensions
        height, width = image.shape[:2]
        
        # Calculate scaling factor
        scale = min(size[0]/width, size[1]/height)
        
        # Calculate new dimensions
        new_width = int(width * scale)
        new_height = int(height * scale)
        
        # Resize image
        resized = cv2.resize(image, (new_width, new_height),
                           interpolation=cv2.INTER_AREA)
                           
        # Create QImage
        height, width, channel = resized.shape
        bytes_per_line = 3 * width
        qimg = QImage(resized.data, width, height, bytes_per_line,
                     QImage.Format.Format_RGB888)
                     
        return qimg
        
    except Exception as e:
        logger.error(f"Failed to create thumbnail: {str(e)}")
        return None
