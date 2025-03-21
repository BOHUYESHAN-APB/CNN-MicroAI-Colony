"""
Result image display dock implementation
结果图像显示停靠窗口实现
"""
import cv2
import numpy as np
import logging
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QImage, QPixmap
from .base_dock_widget import BaseDockWidget
from ..utils.image_preprocessing import draw_detections

logger = logging.getLogger(__name__)

class ResultImageDock(BaseDockWidget):
    """Result image display dock"""
    
    def __init__(self, parent=None):
        super().__init__("检测结果", parent)
        self.setup_ui()
        
    def setup_ui(self):
        """Setup user interface"""
        # Create image label
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet("""
            QLabel {
                background: #1e1e1e;
                border: 1px solid #3d3d3d;
            }
        """)
        
        # Set as central widget
        self.set_central_widget(self.image_label)
        
        # Enable dock features
        self.setObjectName("result_image_dock")
        
    def display_image(self, image):
        """Display a plain image
        
        Args:
            image: RGB numpy array
        """
        if image is None:
            self.clear()
            return
            
        try:
            # Convert to QImage
            height, width, channel = image.shape
            bytes_per_line = 3 * width
            q_img = QImage(
                image.data,
                width,
                height,
                bytes_per_line,
                QImage.Format.Format_RGB888
            )
            
            # Display
            self.image_label.setPixmap(QPixmap.fromImage(q_img))
            
        except Exception as e:
            logger.error(f"Error displaying image: {str(e)}")
            self.clear()
            
    def display_results(self, image, detections):
        """Display detection results
        
        Args:
            image: RGB numpy array
            detections: List of detection dictionaries
        """
        if image is None or not detections:
            self.clear()
            return
            
        try:
            # Draw detections
            result_image = draw_detections(image, detections)
            
            # Display
            if result_image is not None:
                self.display_image(result_image)
                
        except Exception as e:
            logger.error(f"Error displaying results: {str(e)}")
            self.clear()
            
    def clear(self):
        """Clear display"""
        self.image_label.clear()
        self.image_label.setText("无检测结果")
        
    def minimumSizeHint(self):
        """Provide reasonable minimum size"""
        return QSize(400, 300)
