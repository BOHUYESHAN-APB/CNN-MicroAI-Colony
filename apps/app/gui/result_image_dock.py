"""
Result image display dock implementation
结果图像显示停靠窗口实现
"""
import cv2
import numpy as np
import logging
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QScrollArea, 
                            QHBoxLayout, QPushButton, QSpinBox)
from PyQt6.QtCore import Qt, QSize, QTimer, QEvent, QPoint, QPropertyAnimation
from PyQt6.QtGui import QImage, QPixmap, QKeySequence, QShortcut
from .base_dock_widget import BaseDockWidget

logger = logging.getLogger(__name__)

class ResultImageDock(BaseDockWidget):
    """Result image display dock"""
    
    CACHE_LIMIT = 5  # Maximum number of cached images
    
    def __init__(self, parent=None):
        super().__init__("检测结果", parent)
        self.current_image = None
        self.current_detections = None
        self.zoom_level = 1.0
        self._image_cache = {}
        self.setup_ui()
        
        # Create timer for delayed zoom-to-fit
        self.fit_timer = QTimer(self)
        self.fit_timer.setSingleShot(True)
        self.fit_timer.timeout.connect(self._zoom_to_fit)
        
        # Setup keyboard shortcuts
        self.setup_shortcuts()

[Previous content remains the same until goto_prev_colony method...]

    def goto_prev_colony(self):
        """Navigate to previous colony"""
        if self.current_detections is None or self.current_image is None:
            return
            
        # Get current viewport center
        viewport = self.scroll_area.viewport()
        viewport_center = viewport.rect().center()
        viewport_pos = viewport.mapTo(self.image_label, viewport_center)
        
        # Find closest colony to the left
        closest = None
        min_dist = float('inf')
        
        for det in self.current_detections:
            center = det.get("center", (0, 0))
            scaled_x = center[0] * self.zoom_level
            scaled_y = center[1] * self.zoom_level
            
            # Only consider colonies to the left
            if scaled_x >= viewport_pos.x():
                continue
                
            dist = ((scaled_x - viewport_pos.x()) ** 2 + 
                   (scaled_y - viewport_pos.y()) ** 2) ** 0.5
            
            if dist < min_dist:
                min_dist = dist
                closest = center
                
        if closest:
            self.scroll_to_colony(closest)
            
    def goto_next_colony(self):
        """Navigate to next colony"""
        if self.current_detections is None or self.current_image is None:
            return
            
        # Get current viewport center
        viewport = self.scroll_area.viewport()
        viewport_center = viewport.rect().center()
        viewport_pos = viewport.mapTo(self.image_label, viewport_center)
        
        # Find closest colony to the right
        closest = None
        min_dist = float('inf')
        
        for det in self.current_detections:
            center = det.get("center", (0, 0))
            scaled_x = center[0] * self.zoom_level
            scaled_y = center[1] * self.zoom_level
            
            # Only consider colonies to the right
            if scaled_x <= viewport_pos.x():
                continue
                
            dist = ((scaled_x - viewport_pos.x()) ** 2 + 
                   (scaled_y - viewport_pos.y()) ** 2) ** 0.5
            
            if dist < min_dist:
                min_dist = dist
                closest = center
                
        if closest:
            self.scroll_to_colony(closest)

[Previous content remains exactly the same...]
