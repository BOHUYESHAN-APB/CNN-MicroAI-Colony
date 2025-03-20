"""
Thumbnail generation utilities
缩略图生成工具
"""
import cv2
import numpy as np
import logging
from pathlib import Path
from PyQt6.QtGui import QImage

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
        # Convert path to proper Path object
        img_path = Path(path)
        
        # Read image using numpy to handle Unicode paths
        with open(img_path, 'rb') as f:
            img_array = np.frombuffer(f.read(), dtype=np.uint8)
            image = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
            
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
                           
        # Convert to RGB
        rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
        
        # Create QImage
        height, width, channel = rgb.shape
        bytes_per_line = 3 * width
        qimg = QImage(rgb, width, height, bytes_per_line,
                     QImage.Format.Format_RGB888)
                     
        return qimg
        
    except Exception as e:
        logger.error(f"Failed to create thumbnail: {str(e)}")
        return None
