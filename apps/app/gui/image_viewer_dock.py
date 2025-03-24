"""
Image viewer dock implementation
图像查看器停靠窗口实现
"""
import logging
from PyQt6.QtWidgets import QDockWidget, QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QImage
import numpy as np
import cv2

from .image_viewer import ImageViewer
from ..utils.image_preprocessing import load_image

logger = logging.getLogger(__name__)

class ImageViewerDock(QDockWidget):
    """Image viewer dock widget"""
    
    def __init__(self, parent=None):
        """Initialize dock widget"""
        super().__init__("图像查看器", parent)
        self.setObjectName("image_viewer_dock")
        
        # Create widget
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create image viewer
        self.viewer = ImageViewer()
        layout.addWidget(self.viewer)
        
        self.setWidget(widget)
        
        # Store current image
        self.current_image = None
        
    def load_image(self, path):
        """Load and display image
        
        Args:
            path: Image file path
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Load image using preprocessing utility
            image = load_image(path)
            if image is None:
                return False
                
            # Store image
            self.current_image = image
                
            # Convert to QImage
            height, width = image.shape[:2]
            bytes_per_line = 3 * width
            q_image = QImage(image.data, width, height, bytes_per_line,
                           QImage.Format.Format_RGB888).rgbSwapped()
                           
            # Display image
            pixmap = QPixmap.fromImage(q_image)
            self.viewer.set_pixmap(pixmap)
            
            return True
            
        except Exception as e:
            logger.error(f"Error loading image: {str(e)}")
            return False
            
    def get_current_image(self):
        """Get currently displayed image
        
        Returns:
            numpy.ndarray: Image data or None if no image loaded
        """
        return self.current_image
