"""
Thumbnail creation utility
缩略图生成工具
"""
import os
import cv2
import numpy as np
import logging
from PyQt6.QtGui import QImage
from PyQt6.QtCore import QDir
from .image_preprocessing import load_image

logger = logging.getLogger(__name__)

def create_thumbnail(image_path, size=(64, 64)):
    """Create a thumbnail for an image file
    
    Args:
        image_path (str): Path to image file
        size (tuple): Target size (width, height)
        
    Returns:
        QImage: Thumbnail image
        
    Raises:
        ValueError: If image cannot be loaded or processed
    """
    try:
        logger.debug(f"Creating thumbnail for: {image_path}")
        
        # Convert path to native format
        abs_path = QDir.toNativeSeparators(os.path.abspath(image_path))
        
        # Load image using our preprocessing utility
        image = load_image(abs_path)
        if image is None:
            raise ValueError("Cannot load image")
            
        # Convert to RGB
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Calculate target size maintaining aspect ratio
        h, w = image.shape[:2]
        scale = min(size[0]/w, size[1]/h)
        new_size = (int(w * scale), int(h * scale))
        
        # Resize
        image = cv2.resize(image, new_size, interpolation=cv2.INTER_AREA)
        
        # Add padding to make square
        target_w, target_h = size
        pad_x = (target_w - new_size[0]) // 2
        pad_y = (target_h - new_size[1]) // 2
        
        padded = np.full((target_h, target_w, 3), 32, dtype=np.uint8)
        padded[pad_y:pad_y+new_size[1], pad_x:pad_x+new_size[0]] = image
        
        # Convert to QImage
        height, width, channel = padded.shape
        bytes_per_line = 3 * width
        qimage = QImage(padded.data, width, height, bytes_per_line, 
                     QImage.Format.Format_RGB888)
        
        logger.debug(f"Successfully created thumbnail for: {abs_path}")
        return qimage
        
    except Exception as e:
        logger.error(f"Failed to create thumbnail: {str(e)}")
        logger.debug(f"Attempted path: {image_path}", exc_info=True)
        raise ValueError(f"Cannot create thumbnail: {str(e)}")
