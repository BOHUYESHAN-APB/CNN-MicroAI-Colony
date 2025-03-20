"""
Image viewer widget implementation
图像查看器部件实现
"""
import os
import cv2
import numpy as np
from PyQt6.QtWidgets import (QLabel, QScrollArea, QSizePolicy, 
                            QVBoxLayout, QWidget)
from PyQt6.QtGui import QImage, QPixmap, QPalette, QPainter, QColor, QKeyEvent
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QPoint, QRect, QDir

import logging
logger = logging.getLogger(__name__)

class ImageLabel(QLabel):
    """Custom label for image display with zoom support"""
    
    def __init__(self):
        super().__init__()
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumSize(800, 600)
        
        # Allow expanding
        self.setSizePolicy(QSizePolicy.Policy.Expanding,
                          QSizePolicy.Policy.Expanding)
        
        # Enable background
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor(20, 20, 20))
        self.setPalette(palette)
        
        # Properties
        self._antialias = True
        self._high_quality = True
        
        # Enable focus
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
    def paintEvent(self, event):
        """Custom paint event for better image rendering"""
        if self.pixmap() and not self.pixmap().isNull():
            painter = QPainter(self)
            
            if self._antialias:
                painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
            
            # Get sizes
            pixmap_size = self.pixmap().size()
            widget_size = self.size()
            
            # Calculate scaled size maintaining aspect ratio
            scaled_size = pixmap_size.scaled(
                widget_size,
                Qt.AspectRatioMode.KeepAspectRatio
            )
            
            # Calculate position to center the image
            x = (widget_size.width() - scaled_size.width()) // 2
            y = (widget_size.height() - scaled_size.height()) // 2
            
            # Draw shadow
            if self._high_quality:
                shadow_offset = 2
                shadow = self.pixmap().scaled(
                    scaled_size,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                painter.setOpacity(0.2)
                painter.drawPixmap(
                    x + shadow_offset,
                    y + shadow_offset,
                    shadow
                )
                painter.setOpacity(1.0)
            
            # Draw main image
            target_rect = QRect(x, y, scaled_size.width(), scaled_size.height())
            painter.drawPixmap(target_rect, self.pixmap())
            
            # Draw focus indicator if has focus
            if self.hasFocus():
                focus_rect = target_rect.adjusted(-2, -2, 2, 2)
                painter.setPen(QColor(82, 148, 226))
                painter.drawRect(focus_rect)
        else:
            super().paintEvent(event)

class ImageViewer(QWidget):
    """Image viewer widget with zoom and pan"""
    
    zoom_changed = pyqtSignal(float)
    image_loaded = pyqtSignal(str)
    
    SCROLL_STEP = 50  # Pixels to scroll with keyboard
    ZOOM_FACTOR = 1.15  # Zoom factor for keyboard zoom
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
        # Image state
        self.current_path = None
        self.original_pixmap = None
        self.zoom_level = 1.0
        self.base_zoom = 1.0
        
        # Pan support
        self.panning = False
        self.pan_start = QPoint()
        self.last_pan_time = 0
        
        # Performance settings
        self._update_delay = 16  # ms (60 FPS)
        
        # Enable focus
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
        # Dark theme
        self.setStyleSheet("""
            QWidget {
                background-color: #141414;
                color: #e0e0e0;
            }
            QScrollArea {
                border: none;
                background-color: #141414;
            }
            QLabel {
                background-color: #141414;
                padding: 10px;
            }
            QScrollBar {
                background: #2d2d2d;
                border-radius: 7px;
                margin: 2px;
            }
            QScrollBar:horizontal {
                height: 14px;
            }
            QScrollBar:vertical {
                width: 14px;
            }
            QScrollBar::handle {
                background: #424242;
                border-radius: 7px;
                min-width: 25px;
                min-height: 25px;
            }
            QScrollBar::handle:hover {
                background: #616161;
            }
            QScrollBar::handle:pressed {
                background: #757575;
            }
            QScrollBar::add-line, QScrollBar::sub-line {
                width: 0px;
                height: 0px;
            }
            QScrollBar::add-page, QScrollBar::sub-page {
                background: none;
            }
        """)

    def setup_ui(self):
        """Setup user interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Scroll area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setFrameShape(self.scroll_area.Shape.NoFrame)
        
        # Image label
        self.image_label = ImageLabel()
        
        # Container
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.addWidget(self.image_label, 1, Qt.AlignmentFlag.AlignCenter)
        
        self.scroll_area.setWidget(container)
        layout.addWidget(self.scroll_area)

    def clear(self):
        """Clear displayed image"""
        self.current_path = None
        self.original_pixmap = None
        self.zoom_level = 1.0
        self.base_zoom = 1.0
        self.image_label.clear()
        
    def get_current_path(self):
        """Get path of current image"""
        return self.current_path
        
    def load_image(self, path):
        """Load and display image"""
        try:
            # Convert to absolute path and handle Windows long paths
            abs_path = os.path.abspath(path)
            if os.name == 'nt':  # Windows system
                abs_path = QDir.toNativeSeparators(abs_path)
            
            # Load image bytes
            with open(abs_path, 'rb') as f:
                buffer = f.read()
            array = np.frombuffer(buffer, dtype=np.uint8)
            image = cv2.imdecode(array, cv2.IMREAD_COLOR)
            
            if image is None:
                logger.error(f"Failed to load image: {path}")
                return False
            
            # Convert to RGB
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Create QImage
            height = image.shape[0]
            width = image.shape[1]
            bytes_per_line = 3 * width
            qimg = QImage(image.data, width, height, bytes_per_line, 
                         QImage.Format.Format_RGB888)
            
            # Create pixmap
            pixmap = QPixmap.fromImage(qimg)
            if pixmap.isNull():
                logger.error(f"Failed to create pixmap from image: {path}")
                return False
                
            # Store image
            self.current_path = path
            self.original_pixmap = pixmap
            
            # Reset zoom and fit to view
            self.base_zoom = self.calculate_zoom_to_fit()
            self.zoom_level = 1.0
            self.update_display()
            
            # Emit signal
            self.image_loaded.emit(path)
            
            return True
            
        except Exception as e:
            logger.error(f"Error loading image: {str(e)}")
            logger.debug(f"Attempted path: {abs_path}", exc_info=True)
            return False
            
    def set_pixmap(self, pixmap):
        """Set pixmap to display"""
        if pixmap and not pixmap.isNull():
            self.original_pixmap = pixmap
            self.zoom_level = 1.0
            self.base_zoom = self.calculate_zoom_to_fit()
            self.update_display()
            
    def calculate_zoom_to_fit(self):
        """Calculate zoom level to fit image to view"""
        if not self.original_pixmap or self.original_pixmap.isNull():
            return 1.0

        # Get sizes
        view_size = self.scroll_area.viewport().size()
        image_size = self.original_pixmap.size()
        
        # Add margin
        margin = 20
        view_width = max(1, view_size.width() - margin)
        view_height = max(1, view_size.height() - margin)
        
        # Calculate ratios
        width_ratio = view_width / image_size.width()
        height_ratio = view_height / image_size.height()
        
        return min(width_ratio, height_ratio)

    def update_display(self):
        """Update image display"""
        if not self.original_pixmap or self.original_pixmap.isNull():
            return
            
        # Calculate final zoom
        final_zoom = self.base_zoom * self.zoom_level
        
        # Calculate new size
        width = int(self.original_pixmap.width() * final_zoom)
        height = int(self.original_pixmap.height() * final_zoom)
        
        # Scale pixmap
        scaled = self.original_pixmap.scaled(
            width, height,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        
        # Update label
        self.image_label.setPixmap(scaled)
        
    def resizeEvent(self, event):
        """Handle resize events"""
        super().resizeEvent(event)
        if self.original_pixmap:
            old_base = self.base_zoom
            self.base_zoom = self.calculate_zoom_to_fit()
            
            if abs(old_base - self.base_zoom) > 0.01:
                self.update_display()

    def keyPressEvent(self, event):
        """Handle keyboard events"""
        if event.key() == Qt.Key.Key_Plus and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            # Zoom in
            self.zoom_level *= self.ZOOM_FACTOR
            self.zoom_level = min(10.0, self.zoom_level)
            self.update_display()
            self.zoom_changed.emit(self.zoom_level)
            
        elif event.key() == Qt.Key.Key_Minus and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            # Zoom out
            self.zoom_level /= self.ZOOM_FACTOR
            self.zoom_level = max(0.1, self.zoom_level)
            self.update_display()
            self.zoom_changed.emit(self.zoom_level)
            
        elif event.key() == Qt.Key.Key_0 and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            # Reset zoom
            self.zoom_level = 1.0
            self.update_display()
            self.zoom_changed.emit(self.zoom_level)
            
        elif event.key() == Qt.Key.Key_Left:
            # Scroll left
            self.scroll_area.horizontalScrollBar().setValue(
                self.scroll_area.horizontalScrollBar().value() - self.SCROLL_STEP)
            
        elif event.key() == Qt.Key.Key_Right:
            # Scroll right
            self.scroll_area.horizontalScrollBar().setValue(
                self.scroll_area.horizontalScrollBar().value() + self.SCROLL_STEP)
            
        elif event.key() == Qt.Key.Key_Up:
            # Scroll up
            self.scroll_area.verticalScrollBar().setValue(
                self.scroll_area.verticalScrollBar().value() - self.SCROLL_STEP)
            
        elif event.key() == Qt.Key.Key_Down:
            # Scroll down
            self.scroll_area.verticalScrollBar().setValue(
                self.scroll_area.verticalScrollBar().value() + self.SCROLL_STEP)
            
        elif event.key() == Qt.Key.Key_Home:
            # Scroll to top
            self.scroll_area.verticalScrollBar().setValue(0)
            
        elif event.key() == Qt.Key.Key_End:
            # Scroll to bottom
            self.scroll_area.verticalScrollBar().setValue(
                self.scroll_area.verticalScrollBar().maximum())
            
        elif event.key() == Qt.Key.Key_Space:
            # Toggle fit to window
            if self.zoom_level != 1.0:
                self.zoom_level = 1.0
            else:
                self.zoom_level = self.calculate_zoom_to_fit()
            self.update_display()
            self.zoom_changed.emit(self.zoom_level)
            
        else:
            super().keyPressEvent(event)
        
    def wheelEvent(self, event):
        """Handle mouse wheel events"""
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            # Get mouse position relative to viewport
            viewport_pos = self.scroll_area.viewport().mapFromGlobal(
                self.mapToGlobal(event.position().toPoint()))
            scrollbar_pos = QPoint(
                self.scroll_area.horizontalScrollBar().value(),
                self.scroll_area.verticalScrollBar().value())
            
            # Calculate zoom factor
            delta = event.angleDelta().y()
            factor = self.ZOOM_FACTOR if delta > 0 else 1/self.ZOOM_FACTOR
            
            # Update zoom level
            old_zoom = self.zoom_level
            self.zoom_level *= factor
            self.zoom_level = max(0.1, min(10.0, self.zoom_level))
            
            # Update display
            self.update_display()
            
            # Adjust scroll position to keep mouse point fixed
            if self.zoom_level != old_zoom:
                factor = self.zoom_level / old_zoom
                new_pos = QPoint(
                    int(viewport_pos.x() * factor - viewport_pos.x() + scrollbar_pos.x()),
                    int(viewport_pos.y() * factor - viewport_pos.y() + scrollbar_pos.y()))
                    
                self.scroll_area.horizontalScrollBar().setValue(new_pos.x())
                self.scroll_area.verticalScrollBar().setValue(new_pos.y())
            
            event.accept()
            self.zoom_changed.emit(self.zoom_level)
            
        else:
            super().wheelEvent(event)
            
    def mousePressEvent(self, event):
        """Handle mouse press events"""
        if event.button() == Qt.MouseButton.MiddleButton:
            self.panning = True
            self.pan_start = event.pos()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
        else:
            super().mousePressEvent(event)
            
    def mouseReleaseEvent(self, event):
        """Handle mouse release events"""
        if event.button() == Qt.MouseButton.MiddleButton:
            self.panning = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
            event.accept()
        else:
            super().mouseReleaseEvent(event)
            
    def mouseMoveEvent(self, event):
        """Handle mouse move events"""
        if self.panning:
            delta = event.pos() - self.pan_start
            self.scroll_area.horizontalScrollBar().setValue(
                self.scroll_area.horizontalScrollBar().value() - delta.x())
            self.scroll_area.verticalScrollBar().setValue(
                self.scroll_area.verticalScrollBar().value() - delta.y())
            self.pan_start = event.pos()
            event.accept()
        else:
            super().mouseMoveEvent(event)
