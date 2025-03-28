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
        self.current_detections = []  # Changed from None to empty list
        self.zoom_level = 1.0
        self._image_cache = {}
        self.setup_ui()
        
        # Create timer for delayed zoom-to-fit
        self.fit_timer = QTimer(self)
        self.fit_timer.setSingleShot(True)
        self.fit_timer.timeout.connect(self._zoom_to_fit)
        
        # Setup keyboard shortcuts
        self.setup_shortcuts()
        
    def setup_shortcuts(self):
        """Setup keyboard shortcuts"""
        shortcuts = {
            Qt.Key.Key_Left: self.goto_prev_colony,
            Qt.Key.Key_Right: self.goto_next_colony,
            Qt.Key.Key_Plus: lambda: self.set_zoom(self.zoom_level * 1.2),
            Qt.Key.Key_Minus: lambda: self.set_zoom(self.zoom_level / 1.2),
            Qt.Key.Key_0: self._zoom_to_fit,
            Qt.Key.Key_C: lambda: self.toggle_centers(),
            Qt.Key.Key_N: lambda: self.toggle_numbers(),
            Qt.Key.Key_Space: self._zoom_to_fit
        }
        
        for key, slot in shortcuts.items():
            shortcut = QShortcut(QKeySequence(key), self)
            shortcut.activated.connect(slot)
            
    def toggle_centers(self):
        """Toggle center points display"""
        self.show_centers.setChecked(not self.show_centers.isChecked())
        self._clear_cache()
        self.update_display()
        
    def toggle_numbers(self):
        """Toggle confidence numbers display"""
        self.show_numbers.setChecked(not self.show_numbers.isChecked())
        self._clear_cache()
        self.update_display()
        
    def _clear_cache(self):
        """Clear image cache"""
        self._image_cache.clear()
        
    def _manage_cache(self, key, pixmap):
        """Manage cache size"""
        while len(self._image_cache) >= self.CACHE_LIMIT:
            self._image_cache.pop(next(iter(self._image_cache)))
        self._image_cache[key] = pixmap
        
    def setup_ui(self):
        """Setup user interface"""
        # Create main widget and layout
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.setSpacing(4)
        
        # Create toolbar
        toolbar = QHBoxLayout()
        toolbar.setContentsMargins(0, 0, 0, 0)
        
        # Navigation controls
        nav_group = QHBoxLayout()
        nav_group.setSpacing(2)
        
        # Colony count display with styling
        count_label = QLabel("菌落数:")
        count_label.setStyleSheet("color: #e0e0e0;")
        nav_group.addWidget(count_label)
        
        self.count_display = QLabel("0")
        self.count_display.setMinimumWidth(40)
        self.count_display.setStyleSheet("color: #e0e0e0;")
        self.count_display.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        nav_group.addWidget(self.count_display)
        
        # Navigation buttons with styling
        button_style = """
            QPushButton {
                background-color: #404040;
                border-radius: 12px;
                font-size: 14px;
                color: #e0e0e0;
            }
            QPushButton:hover {
                background-color: #505050;
            }
            QPushButton:pressed {
                background-color: #606060;
            }
            QPushButton:disabled {
                background-color: #303030;
                color: #808080;
            }
        """
        
        nav_prev = QPushButton("◀")
        nav_prev.setFixedSize(24, 24)
        nav_prev.setStyleSheet(button_style)
        nav_prev.setToolTip("上一个菌落 (←)")
        nav_prev.clicked.connect(self.goto_prev_colony)
        nav_group.addWidget(nav_prev)
        
        nav_next = QPushButton("▶")
        nav_next.setFixedSize(24, 24)
        nav_next.setStyleSheet(button_style)
        nav_next.setToolTip("下一个菌落 (→)")
        nav_next.clicked.connect(self.goto_next_colony)
        nav_group.addWidget(nav_next)
        
        toolbar.addLayout(nav_group)
        
        toolbar.addSpacing(20)
        
        # Zoom controls
        zoom_label = QLabel("缩放:")
        zoom_label.setStyleSheet("color: #e0e0e0;")
        toolbar.addWidget(zoom_label)
        
        self.zoom_sb = QSpinBox()
        self.zoom_sb.setRange(10, 400)
        self.zoom_sb.setValue(100)
        self.zoom_sb.setSuffix("%")
        self.zoom_sb.setStyleSheet("""
            QSpinBox {
                background-color: #404040;
                color: #e0e0e0;
                border: 1px solid #505050;
                border-radius: 4px;
                padding: 2px;
            }
            QSpinBox:hover {
                border-color: #606060;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                border: none;
                background: #505050;
                width: 16px;
            }
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {
                background: #606060;
            }
        """)
        self.zoom_sb.valueChanged.connect(lambda v: self.set_zoom(v / 100))
        toolbar.addWidget(self.zoom_sb)
        
        zoom_fit_btn = QPushButton("适应窗口")
        zoom_fit_btn.clicked.connect(self._zoom_to_fit)
        zoom_fit_btn.setFixedWidth(80)
        zoom_fit_btn.setToolTip("适应窗口大小 (空格)")
        zoom_fit_btn.setStyleSheet("""
            QPushButton {
                background-color: #404040;
                color: #e0e0e0;
                border-radius: 4px;
                padding: 4px;
            }
            QPushButton:hover {
                background-color: #505050;
            }
            QPushButton:pressed {
                background-color: #606060;
            }
        """)
        toolbar.addWidget(zoom_fit_btn)
        
        toolbar.addStretch()
        
        # View options
        view_group = QHBoxLayout()
        view_group.setSpacing(2)
        
        toggle_button_style = """
            QPushButton {
                background-color: #404040;
                color: #e0e0e0;
                border-radius: 4px;
                padding: 4px 8px;
            }
            QPushButton:hover {
                background-color: #505050;
            }
            QPushButton:pressed {
                background-color: #606060;
            }
            QPushButton:checked {
                background-color: #00574B;
            }
            QPushButton:checked:hover {
                background-color: #006D5B;
            }
            QPushButton:disabled {
                background-color: #303030;
                color: #808080;
            }
        """
        
        self.show_centers = QPushButton("显示中心点 (C)")
        self.show_centers.setCheckable(True)
        self.show_centers.setChecked(True)
        self.show_centers.setToolTip("显示/隐藏中心点标记")
        self.show_centers.clicked.connect(self.update_display)
        self.show_centers.setStyleSheet(toggle_button_style)
        view_group.addWidget(self.show_centers)
        
        self.show_numbers = QPushButton("显示置信度 (N)")
        self.show_numbers.setCheckable(True)
        self.show_numbers.setChecked(True)
        self.show_numbers.setToolTip("显示/隐藏置信度数值")
        self.show_numbers.clicked.connect(self.update_display)
        self.show_numbers.setStyleSheet(toggle_button_style)
        view_group.addWidget(self.show_numbers)
        
        toolbar.addLayout(view_group)
        
        main_layout.addLayout(toolbar)
        
        # Create scroll area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setFrameShape(self.scroll_area.Shape.NoFrame)
        self.scroll_area.setStyleSheet("""
            QScrollBar:horizontal {
                border: none;
                background: #2d2d2d;
                height: 12px;
            }
            QScrollBar::handle:horizontal {
                background: #404040;
                min-width: 20px;
                border-radius: 6px;
            }
            QScrollBar::handle:horizontal:hover {
                background: #505050;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px;
            }
            QScrollBar:vertical {
                border: none;
                background: #2d2d2d;
                width: 12px;
            }
            QScrollBar::handle:vertical {
                background: #404040;
                min-height: 20px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical:hover {
                background: #505050;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        
        # Enable mouse wheel zoom
        self.scroll_area.viewport().installEventFilter(self)
        
        # Create image container
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create image label
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setMinimumSize(400, 300)
        self.image_label.setStyleSheet("""
            QLabel {
                background: #1e1e1e;
                border: 1px solid #3d3d3d;
            }
        """)
        container_layout.addWidget(self.image_label)
        
        # Add container to scroll area
        self.scroll_area.setWidget(container)
        main_layout.addWidget(self.scroll_area)
        
        # Set as central widget
        self.set_central_widget(main_widget)
        
        # Enable dock features
        self.setObjectName("result_image_dock")
        
    def set_zoom(self, level):
        """Set zoom level"""
        # Get old zoom center
        viewport = self.scroll_area.viewport()
        old_pos = viewport.mapToGlobal(viewport.rect().center())
        
        # Update zoom level
        self.zoom_level = max(0.1, min(4.0, level))
        self.zoom_sb.setValue(int(self.zoom_level * 100))
        
        # Update display
        self.update_display()
        
        # Maintain zoom center
        new_pos = viewport.mapToGlobal(viewport.rect().center())
        diff = old_pos - new_pos
        self.scroll_area.horizontalScrollBar().setValue(
            self.scroll_area.horizontalScrollBar().value() + diff.x())
        self.scroll_area.verticalScrollBar().setValue(
            self.scroll_area.verticalScrollBar().value() + diff.y())
            
    def _zoom_to_fit(self):
        """Zoom to fit window"""
        if self.current_image is None:
            return
            
        viewport_size = self.scroll_area.viewport().size()
        image_height, image_width = self.current_image.shape[:2]
        
        width_ratio = viewport_size.width() / image_width
        height_ratio = viewport_size.height() / image_height
        zoom_level = min(width_ratio, height_ratio) * 0.95  # Add small margin
        
        self.set_zoom(zoom_level)
        
    def update_display(self):
        """Update display with current zoom level"""
        if self.current_image is None:
            return
            
        try:
            # Use cache if available
            cache_key = (self.zoom_level, 
                        self.show_centers.isChecked(),
                        self.show_numbers.isChecked())
            
            if cache_key in self._image_cache:
                self.image_label.setPixmap(self._image_cache[cache_key])
                return
            
            # Convert input image to BGR for OpenCV operations
            working_image = cv2.cvtColor(self.current_image, cv2.COLOR_RGB2BGR)
            
            # Calculate new size
            height, width = working_image.shape[:2]
            new_width = max(1, int(width * self.zoom_level))
            new_height = max(1, int(height * self.zoom_level))
            
            # Resize image
            resized = cv2.resize(working_image, (new_width, new_height),
                               interpolation=cv2.INTER_AREA)
            
            # Draw detections if available
            if self.current_detections:
                count = len(self.current_detections)
                conf_avg = sum(det.get("confidence", 0) for det in self.current_detections) / count
                self.count_display.setText(str(count))
                self.count_display.setToolTip(f"平均置信度: {conf_avg:.2f}")
                
                for det in self.current_detections:
                    # Scale detection coordinates
                    center = det.get("center", (0, 0))
                    x = int(round(center[0] * self.zoom_level))
                    y = int(round(center[1] * self.zoom_level))
                    diameter = int(round(det.get("diameter", 0) * self.zoom_level))
                    confidence = det.get("confidence", 0)
                    
                    # Draw colony circle
                    thickness = max(1, int(2 * self.zoom_level))
                    cv2.circle(resized, (x, y), diameter // 2, (0, 0, 255), thickness)
                    
                    # Draw center point if enabled
                    if self.show_centers.isChecked():
                        center_size = max(1, int(3 * self.zoom_level))
                        cv2.circle(resized, (x, y), center_size, (255, 0, 0), -1)
                        cv2.circle(resized, (x, y), center_size + 1, (255, 0, 0), 1)
                    
                    # Draw confidence score if enabled
                    if self.show_numbers.isChecked():
                        font_scale = max(0.3, min(0.8, 0.6 * self.zoom_level))
                        text = f"{confidence:.2f}"
                        thickness = max(1, int(1.5 * self.zoom_level))
                        
                        # Calculate text size and position
                        (text_width, text_height), _ = cv2.getTextSize(
                            text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness)
                        
                        text_x = x - text_width // 2
                        text_y = y - diameter // 2 - 5
                        
                        # Draw text background
                        bg_pts = np.array([
                            [text_x - 2, text_y + 2],
                            [text_x + text_width + 2, text_y + 2],
                            [text_x + text_width + 2, text_y - text_height - 2],
                            [text_x - 2, text_y - text_height - 2]
                        ], dtype=np.int32)
                        cv2.fillPoly(resized, [bg_pts], (0, 0, 0))
                        
                        # Draw text
                        cv2.putText(resized,
                                  text,
                                  (text_x, text_y),
                                  cv2.FONT_HERSHEY_SIMPLEX,
                                  font_scale,
                                  (255, 255, 0),
                                  thickness)
            
            # Convert back to RGB for Qt
            display_image = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
            
            # Create QImage
            height, width = display_image.shape[:2]
            bytes_per_line = 3 * width
            q_img = QImage(display_image.data.tobytes(), width, height,
                          bytes_per_line, QImage.Format.Format_RGB888)
            
            # Create pixmap and cache
            pixmap = QPixmap.fromImage(q_img)
            self._manage_cache(cache_key, pixmap)
            
            # Display
            self.image_label.setPixmap(pixmap)
            
        except Exception as e:
            logger.error(f"Error updating display: {str(e)}")
            logger.debug("Error details:", exc_info=True)
            
    def eventFilter(self, obj, event):
        """Filter events for scroll area viewport"""
        if obj is self.scroll_area.viewport():
            if event.type() == QEvent.Type.Wheel and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
                # Handle zoom with Ctrl + mouse wheel
                delta = event.angleDelta().y()
                try:
                    if delta > 0:
                        self.set_zoom(self.zoom_level * 1.1)
                    else:
                        self.set_zoom(self.zoom_level / 1.1)
                except Exception as e:
                    logger.warning(f"缩放失败: {str(e)}")
                return True
                
            elif event.type() == QEvent.Type.MouseButtonPress:
                # Handle middle button for zoom-to-fit
                if event.button() == Qt.MouseButton.MiddleButton:
                    self._zoom_to_fit()
                    return True
                    
        return super().eventFilter(obj, event)
        
    def display_image(self, image):
        """Display a plain image"""
        if image is None:
            self.clear()
            return
            
        try:
            self.current_image = image
            self.current_detections = []  # Changed to empty list
            self._clear_cache()
            
            # Schedule zoom-to-fit after widget is properly laid out
            self.fit_timer.start(100)
            
        except Exception as e:
            logger.error(f"Error displaying image: {str(e)}")
            self.clear()
            
    def display_results(self, image, detections):
        """Display detection results"""
        if image is None:
            self.clear()
            return
            
        try:
            self.current_image = image
            self.current_detections = detections if detections else []  # Ensure list
            self._clear_cache()
            
            # Schedule zoom-to-fit after widget is properly laid out
            self.fit_timer.start(100)
                
        except Exception as e:
            logger.error(f"Error displaying results: {str(e)}")
            self.clear()
            
    def get_annotated_image(self):
        """Get the current annotated image with detection results"""
        if self.current_image is None or not self.current_detections:
            return None
            
        # Make a copy of the image
        annotated_img = self.current_image.copy()
        
        # Draw detections
        for det in self.current_detections:
            center = det.get("center", (0, 0))
            diameter = det.get("diameter", 0)
            confidence = det.get("confidence", 0)
            
            # Color based on confidence
            color = (
                int(255 * (1 - confidence)),  # Red
                int(255 * confidence),       # Green
                0                            # Blue
            )
            
            # Draw circle
            cv2.circle(annotated_img, center, diameter // 2, color, 2)
            
            # Draw confidence text
            cv2.putText(annotated_img, f"{confidence:.2f}",
                       (center[0], center[1] - diameter // 2 - 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                       
        return annotated_img
            
    def clear(self):
        """Clear display"""
        self.current_image = None
        self.current_detections = []  # Changed to empty list
        self.zoom_level = 1.0
        self.zoom_sb.setValue(100)
        self.count_display.setText("0")
        self.count_display.setToolTip("")
        self.image_label.clear()
        self.image_label.setText("无检测结果")
        self._clear_cache()
        
    def goto_prev_colony(self):
        """Navigate to previous colony"""
        if not self.current_detections or self.current_image is None:  # Changed condition
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
        if not self.current_detections or self.current_image is None:  # Changed condition
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
            
    def scroll_to_colony(self, center):
        """Scroll view to center on colony"""
        try:
            # Calculate scaled position
            scaled_x = int(center[0] * self.zoom_level)
            scaled_y = int(center[1] * self.zoom_level)
            
            # Get viewport size
            viewport = self.scroll_area.viewport()
            viewport_size = viewport.size()
            
            # Calculate scroll position to center on colony
            scroll_x = max(0, scaled_x - viewport_size.width() // 2)
            scroll_y = max(0, scaled_y - viewport_size.height() // 2)
            
            # Set scroll position with animation
            scroll_bar = self.scroll_area.horizontalScrollBar()
            animation = QPropertyAnimation(scroll_bar, b"value")
            animation.setDuration(200)  # 200ms
            animation.setStartValue(scroll_bar.value())
            animation.setEndValue(scroll_x)
            animation.start()
            
            scroll_bar = self.scroll_area.verticalScrollBar()
            animation = QPropertyAnimation(scroll_bar, b"value")
            animation.setDuration(200)
            animation.setStartValue(scroll_bar.value())
            animation.setEndValue(scroll_y)
            animation.start()
            
        except Exception as e:
            logger.warning(f"滚动到目标位置失败: {str(e)}")
            
    def minimumSizeHint(self):
        """Provide reasonable minimum size"""
        return QSize(400, 300)
        
    def resizeEvent(self, event):
        """Handle resize event"""
        super().resizeEvent(event)
        # Auto-fit on initial display
        if event.oldSize().width() == -1:
            self.fit_timer.start(100)
