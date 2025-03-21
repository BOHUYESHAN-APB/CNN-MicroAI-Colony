"""
Basic image viewer widget
基础图像查看器组件
"""
import cv2
import numpy as np
from PyQt6 import QtCore
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QSizePolicy
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QImage, QPixmap, QPainter, QPen
from pathlib import Path

class ImageViewer(QWidget):
    """Basic image viewer widget with zoom support"""
    
    ZOOM_FACTOR = 1.2  # Zoom step multiplier
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.image = None  # Original image (numpy array)
        self.zoom_level = 1.0  # Current zoom level
        
        # Setup UI
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create image label
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )
        layout.addWidget(self.image_label)
        
        # Initialize empty state
        self.clear()
        
    def load_image(self, path):
        """Load image from path
        
        Args:
            path: Image file path
            
        Returns:
            bool: True if successful
        """
        try:
            # Convert path to Path object
            img_path = Path(path)
            
            # Read image using numpy to handle Unicode paths
            with open(img_path, 'rb') as f:
                img_array = np.frombuffer(f.read(), dtype=np.uint8)
                image = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
                
            if image is None:
                return False
                
            # Convert to RGB
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Store and display
            self.image = image
            self.update_display()
            return True
            
        except Exception:
            return False
            
    def clear(self):
        """Clear current image"""
        self.image = None
        self.zoom_level = 1.0
        self.image_label.clear()
        
    def set_image(self, image):
        """Set image from numpy array
        
        Args:
            image: RGB numpy array
        """
        if image is None:
            self.clear()
            return
            
        self.image = image.copy()
        self.update_display()
        
    def update_display(self):
        """Update displayed image with current zoom"""
        if self.image is None:
            return
            
        # Get widget size
        w = self.image_label.width()
        h = self.image_label.height()
        if w <= 0 or h <= 0:
            return
            
        # Calculate size maintaining aspect ratio
        image_ratio = self.image.shape[1] / self.image.shape[0]
        widget_ratio = w / h
        
        if widget_ratio > image_ratio:
            # Widget is wider than image
            target_h = h
            target_w = int(h * image_ratio)
        else:
            # Widget is taller than image
            target_w = w
            target_h = int(w / image_ratio)
            
        # Apply zoom
        target_w = int(target_w * self.zoom_level)
        target_h = int(target_h * self.zoom_level)
        
        if target_w > 0 and target_h > 0:
            # Resize image
            resized = cv2.resize(
                self.image,
                (target_w, target_h),
                interpolation=cv2.INTER_AREA if self.zoom_level < 1.0 else cv2.INTER_LINEAR
            )
            
            # Convert to QPixmap
            height, width, channel = resized.shape
            bytes_per_line = 3 * width
            q_img = QImage(
                resized.data,
                width,
                height,
                bytes_per_line,
                QImage.Format.Format_RGB888
            )
            
            # Display
            self.image_label.setPixmap(QPixmap.fromImage(q_img))
            
    def resizeEvent(self, event):
        """Handle widget resize"""
        super().resizeEvent(event)
        self.update_display()
        
    def minimumSizeHint(self):
        """Provide reasonable minimum size"""
        return QSize(200, 200)
