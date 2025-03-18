"""
Image viewer widget implementation
图像查看器部件实现
"""
import os
import cv2
import numpy as np
from PyQt6.QtWidgets import QLabel, QScrollArea, QSizePolicy
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtCore import Qt

class ImageViewer(QScrollArea):
    """Image viewer widget with zoom and pan"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Image display label
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )
        self.setWidget(self.image_label)
        
        # Current image info
        self.current_path = None
        self.current_pixmap = None
        self.zoom_level = 1.0
        
        # Set background color
        self.setStyleSheet("background-color: #2b2b2b;")
        
    def clear_image(self):
        """Clear displayed image"""
        self.current_path = None
        self.current_pixmap = None
        self.image_label.clear()
        
    def get_current_path(self):
        """Get path of current image"""
        return self.current_path
        
    def load_image(self, path):
        """
        Load and display image from path
        
        Args:
            path (str): Image file path
            
        Returns:
            bool: True if successful
        """
        try:
            # Normalize path
            path = os.path.normpath(path)
            
            # Load image
            image = cv2.imdecode(
                np.fromfile(path, dtype=np.uint8),
                cv2.IMREAD_COLOR
            )
            if image is None:
                return False
                
            # Convert to RGB
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Create QImage
            height, width, channel = image.shape
            bytes_per_line = 3 * width
            qimg = QImage(image.data, width, height, bytes_per_line, 
                         QImage.Format.Format_RGB888)
            
            # Create pixmap
            pixmap = QPixmap.fromImage(qimg)
            
            # Store info
            self.current_path = path
            self.current_pixmap = pixmap
            
            # Display
            self.update_display()
            return True
            
        except Exception as e:
            print(f"Error loading image: {e}")
            return False
            
    def set_pixmap(self, pixmap):
        """Set pixmap to display"""
        if pixmap and not pixmap.isNull():
            self.current_pixmap = pixmap
            self.update_display()
        
    def update_display(self):
        """Update image display with current pixmap"""
        if self.current_pixmap and not self.current_pixmap.isNull():
            # Scale pixmap to fit view while maintaining aspect ratio
            scaled = self.current_pixmap.scaled(
                self.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.image_label.setPixmap(scaled)
        
    def resizeEvent(self, event):
        """Handle resize events"""
        super().resizeEvent(event)
        self.update_display()
