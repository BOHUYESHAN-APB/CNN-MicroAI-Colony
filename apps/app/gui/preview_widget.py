"""
Preview widget implementation
预览控件实现
"""
import cv2
import numpy as np
from PyQt6.QtWidgets import QLabel, QSizePolicy
from PyQt6.QtCore import Qt, QRect
from PyQt6.QtGui import QImage, QPixmap, QPainter

class PreviewWidget(QLabel):
    """Preview widget for displaying processed images"""
    
    def __init__(self, parent=None):
        """Initialize widget"""
        super().__init__(parent)
        
        self.image = None
        self.pixmap = None
        self.scale_factor = 1.0
        self.offset_x = 0
        self.offset_y = 0
        
        self.setMinimumSize(400, 300)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
    def set_image(self, image):
        """Set image to display
        
        Args:
            image: numpy array (BGR) or None
        """
        try:
            if image is None:
                self.clear()
                self.image = None
                self.pixmap = None
                return
                
            self.image = image.copy()
            
            # Convert to RGB for display
            if len(image.shape) == 3:
                height, width, channels = image.shape
                if channels == 3:
                    rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                    bytes_per_line = 3 * width
                    format = QImage.Format.Format_RGB888
                elif channels == 4:
                    rgb = cv2.cvtColor(image, cv2.COLOR_BGRA2RGB)
                    bytes_per_line = 4 * width
                    format = QImage.Format.Format_RGBA8888
                else:
                    raise ValueError(f"Unsupported number of channels: {channels}")
            else:
                # Grayscale image
                height, width = image.shape
                rgb = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
                bytes_per_line = width
                format = QImage.Format.Format_Grayscale8
                
            q_image = QImage(rgb.data, width, height, bytes_per_line, format)
            self.pixmap = QPixmap.fromImage(q_image)
            
            self.update_scale()
            self.update()
            
        except Exception as e:
            print(f"Error setting preview image: {str(e)}")
            
    def update_scale(self):
        """Update scale factor and offset"""
        if self.pixmap is None:
            return
            
        # Calculate scale factor to fit widget
        widget_size = self.size()
        pixmap_size = self.pixmap.size()
        
        scale_w = widget_size.width() / pixmap_size.width()
        scale_h = widget_size.height() / pixmap_size.height()
        self.scale_factor = min(scale_w, scale_h)
        
        # Calculate offset to center image
        scaled_width = pixmap_size.width() * self.scale_factor
        scaled_height = pixmap_size.height() * self.scale_factor
        self.offset_x = (widget_size.width() - scaled_width) / 2
        self.offset_y = (widget_size.height() - scaled_height) / 2
        
    def resizeEvent(self, event):
        """Handle resize event"""
        super().resizeEvent(event)
        self.update_scale()
        
    def paintEvent(self, event):
        """Handle paint event"""
        if self.pixmap is None:
            return
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        
        target_rect = QRect(
            int(self.offset_x),
            int(self.offset_y),
            int(self.pixmap.width() * self.scale_factor),
            int(self.pixmap.height() * self.scale_factor)
        )
        
        painter.drawPixmap(target_rect, self.pixmap, self.pixmap.rect())
        
    def clear(self):
        """Clear preview"""
        super().clear()
        self.image = None
        self.pixmap = None
