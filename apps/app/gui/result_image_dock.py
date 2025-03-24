"""
Result image display dock implementation
结果图像显示停靠窗口实现
"""
import cv2
import numpy as np
import logging
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QScrollArea, 
                            QHBoxLayout, QPushButton, QSpinBox, QSizePolicy,
                            QFileDialog)
from PyQt6.QtCore import Qt, QSize, QTimer, QEvent, QPoint, QPropertyAnimation
from PyQt6.QtGui import QImage, QPixmap, QKeySequence, QShortcut
from .base_dock_widget import BaseDockWidget

logger = logging.getLogger(__name__)

class ResultImageDock(BaseDockWidget):
    """Result image display dock"""
    
    def __init__(self, parent=None):
        super().__init__("检测结果", parent)
        self.setObjectName("result_image_dock")
        self.current_image = None
        self.current_detections = None
        self.zoom_level = 1.0
        self._image_cache = {}
        
        self.setup_ui()
        
        # Create timer for delayed zoom-to-fit
        self.fit_timer = QTimer(self)
        self.fit_timer.setSingleShot(True)
        self.fit_timer.timeout.connect(self._zoom_to_fit)
        
    def setup_ui(self):
        """Setup user interface"""
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.setSpacing(4)
        
        # Create toolbar
        toolbar = QWidget()
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(0, 0, 0, 0)
        
        # Colony count
        count_label = QLabel("菌落数:")
        self.count_display = QLabel("0")
        toolbar_layout.addWidget(count_label)
        toolbar_layout.addWidget(self.count_display)
        
        # View options
        self.show_centers = QPushButton("显示中心点 (C)")
        self.show_centers.setCheckable(True)
        self.show_centers.setChecked(True)
        self.show_centers.clicked.connect(self.update_display)
        toolbar_layout.addWidget(self.show_centers)
        
        self.show_numbers = QPushButton("显示置信度 (N)")
        self.show_numbers.setCheckable(True)
        self.show_numbers.setChecked(True)
        self.show_numbers.clicked.connect(self.update_display)
        toolbar_layout.addWidget(self.show_numbers)
        
        toolbar_layout.addStretch()
        
        # Zoom controls
        zoom_label = QLabel("缩放:")
        self.zoom_sb = QSpinBox()
        self.zoom_sb.setRange(10, 400)
        self.zoom_sb.setValue(100)
        self.zoom_sb.setSuffix("%")
        self.zoom_sb.valueChanged.connect(lambda v: self.set_zoom(v / 100))
        
        zoom_fit = QPushButton("适应窗口")
        zoom_fit.clicked.connect(self._zoom_to_fit)
        
        toolbar_layout.addWidget(zoom_label)
        toolbar_layout.addWidget(self.zoom_sb)
        toolbar_layout.addWidget(zoom_fit)
        
        main_layout.addWidget(toolbar)
        
        # Create scroll area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        
        # Create image container and label
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet("background: #1e1e1e; border: 1px solid #3d3d3d;")
        container_layout.addWidget(self.image_label)
        
        self.scroll_area.setWidget(container)
        main_layout.addWidget(self.scroll_area)
        
        self.set_central_widget(main_widget)
        
    def display_results(self, image, detections):
        """Display detection results"""
        if image is None:
            self.clear()
            return
            
        try:
            # Convert to BGR for OpenCV
            if len(image.shape) == 2:
                image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
            elif len(image.shape) == 3 and image.shape[2] == 3:
                image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
                
            self.current_image = image
            self.current_detections = detections
            self._clear_cache()
            
            # Update colony count
            if detections:
                self.count_display.setText(str(len(detections)))
                
            # Schedule zoom-to-fit
            self.fit_timer.start(100)
            
        except Exception as e:
            logger.error(f"Error displaying results: {str(e)}")
            self.clear()
            
    def update_display(self):
        """Update display with current settings"""
        if self.current_image is None:
            return
            
        try:
            cache_key = (
                self.zoom_level,
                self.show_centers.isChecked(),
                self.show_numbers.isChecked()
            )
            
            if cache_key in self._image_cache:
                self.image_label.setPixmap(self._image_cache[cache_key])
                return
                
            # Create resized image
            height, width = self.current_image.shape[:2]
            new_width = int(width * self.zoom_level)
            new_height = int(height * self.zoom_level)
            
            display_image = cv2.resize(self.current_image.copy(), 
                                     (new_width, new_height),
                                     interpolation=cv2.INTER_AREA)
                                     
            # Draw detections
            if self.current_detections:
                for det in self.current_detections:
                    # Get detection info
                    center = det.get("center", (0, 0))
                    x = int(center[0] * self.zoom_level)
                    y = int(center[1] * self.zoom_level)
                    diameter = int(det.get("diameter", 0) * self.zoom_level)
                    confidence = det.get("confidence", 0)
                    
                    # Draw circle with color based on confidence
                    r = int(255 * (1 - confidence))
                    g = int(255 * confidence)
                    thickness = max(1, int(2 * self.zoom_level))
                    
                    cv2.circle(display_image, (x, y), diameter // 2, 
                             (0, g, r), thickness)
                    
                    if self.show_centers.isChecked():
                        # Draw center point
                        center_size = max(1, int(3 * self.zoom_level))
                        cv2.circle(display_image, (x, y), center_size, 
                                 (255, 0, 0), -1)
                        
                    if self.show_numbers.isChecked():
                        # Draw confidence score
                        font_scale = max(0.3, min(0.8, 0.5 * self.zoom_level))
                        text = f"{confidence:.2f}"
                        
                        (text_width, text_height), baseline = cv2.getTextSize(
                            text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, 1)
                            
                        text_x = x - text_width // 2
                        text_y = y - diameter // 2 - 5
                        
                        # Draw background
                        cv2.rectangle(display_image,
                                    (text_x - 2, text_y - text_height - 2),
                                    (text_x + text_width + 2, text_y + 2),
                                    (0, 0, 0),
                                    -1)
                                    
                        # Draw text
                        cv2.putText(display_image, text,
                                  (text_x, text_y),
                                  cv2.FONT_HERSHEY_SIMPLEX,
                                  font_scale,
                                  (255, 255, 0),
                                  1)
                                  
            # Convert to QPixmap and display
            height, width = display_image.shape[:2]
            bytes_per_line = 3 * width
            
            q_img = QImage(display_image.data, width, height,
                          bytes_per_line, QImage.Format.Format_BGR888)
            pixmap = QPixmap.fromImage(q_img)
            
            # Cache and display
            self._cache_image(cache_key, pixmap)
            self.image_label.setPixmap(pixmap)
            
        except Exception as e:
            logger.error(f"Error updating display: {str(e)}")
            
    def _cache_image(self, key, pixmap):
        """Add image to cache, removing oldest if needed"""
        if len(self._image_cache) >= 5:  # Keep last 5 images
            self._image_cache.pop(next(iter(self._image_cache)))
        self._image_cache[key] = pixmap
        
    def _clear_cache(self):
        """Clear image cache"""
        self._image_cache.clear()
        
    def set_zoom(self, level):
        """Set zoom level"""
        self.zoom_level = max(0.1, min(4.0, level))
        self.zoom_sb.setValue(int(self.zoom_level * 100))
        self.update_display()
        
    def _zoom_to_fit(self):
        """Zoom to fit window"""
        if self.current_image is None:
            return
            
        viewport_size = self.scroll_area.viewport().size()
        image_height, image_width = self.current_image.shape[:2]
        
        width_ratio = viewport_size.width() / image_width
        height_ratio = viewport_size.height() / image_height
        zoom_level = min(width_ratio, height_ratio) * 0.95
        
        self.set_zoom(zoom_level)
        
    def clear(self):
        """Clear display"""
        self.current_image = None
        self.current_detections = None
        self.zoom_level = 1.0
        self.zoom_sb.setValue(100)
        self.count_display.setText("0")
        self.image_label.clear()
        self._clear_cache()
