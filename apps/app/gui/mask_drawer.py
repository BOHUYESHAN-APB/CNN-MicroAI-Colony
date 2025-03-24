"""
Mask drawing tools implementation
遮罩绘制工具实现
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                            QButtonGroup, QLabel)
from PyQt6.QtCore import Qt, QPoint, QPointF, pyqtSignal, QRect, QSize, QRectF
from PyQt6.QtGui import QPainter, QPen, QColor, QPainterPath, QImage, QPixmap
import cv2
import numpy as np

class DrawArea(QLabel):
    """Custom drawing area widget"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(400, 300)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMouseTracking(True)
        
    def resizeEvent(self, event):
        """Handle resize event"""
        super().resizeEvent(event)
        if self.parent():
            self.parent().update_image_scale()

class MaskDrawer(QWidget):
    """Mask drawing widget"""
    
    # Signal emitted when mask is updated
    mask_updated = pyqtSignal(object)  # numpy array
    
    DRAW_MODES = {
        'FREE': 0,    # 自由绘制
        'RECT': 1,    # 矩形
        'CIRCLE': 2,  # 圆形
        'POLY': 3     # 多边形
    }
    
    def __init__(self, parent=None):
        """Initialize widget"""
        super().__init__(parent)
        
        self.image = None
        self.image_pixmap = None
        self.scale_factor = 1.0
        self.offset_x = 0
        self.offset_y = 0
        
        self.mask = None
        self.drawing = False
        self.last_pos = None
        self.current_pos = None
        self.current_path = QPainterPath()
        self.paths = []
        self.temp_points = []
        
        # Drawing settings
        self.pen_size = 5
        self.draw_mode = self.DRAW_MODES['FREE']
        self.draw_color = QColor(255, 255, 255, 127)  # Semi-transparent white
        self.eraser_mode = False
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup UI elements"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Tool panel
        tool_panel = QWidget()
        tool_layout = QHBoxLayout(tool_panel)
        tool_layout.setContentsMargins(5, 5, 5, 5)
        tool_layout.setSpacing(5)
        
        # Drawing mode buttons
        self.mode_group = QButtonGroup(self)
        
        free_btn = QPushButton("自由绘制")
        free_btn.setCheckable(True)
        free_btn.setChecked(True)
        self.mode_group.addButton(free_btn, self.DRAW_MODES['FREE'])
        tool_layout.addWidget(free_btn)
        
        rect_btn = QPushButton("矩形")
        rect_btn.setCheckable(True)
        self.mode_group.addButton(rect_btn, self.DRAW_MODES['RECT'])
        tool_layout.addWidget(rect_btn)
        
        circle_btn = QPushButton("圆形")
        circle_btn.setCheckable(True)
        self.mode_group.addButton(circle_btn, self.DRAW_MODES['CIRCLE'])
        tool_layout.addWidget(circle_btn)
        
        poly_btn = QPushButton("多边形")
        poly_btn.setCheckable(True)
        self.mode_group.addButton(poly_btn, self.DRAW_MODES['POLY'])
        tool_layout.addWidget(poly_btn)
        
        self.mode_group.buttonClicked.connect(self.mode_changed)
        
        # Eraser button
        self.eraser_btn = QPushButton("橡皮擦")
        self.eraser_btn.setCheckable(True)
        self.eraser_btn.toggled.connect(self.toggle_eraser)
        tool_layout.addWidget(self.eraser_btn)
        
        # Clear button
        clear_btn = QPushButton("清除")
        clear_btn.clicked.connect(self.clear_mask)
        tool_layout.addWidget(clear_btn)
        
        tool_layout.addStretch()
        tool_panel.setLayout(tool_layout)
        layout.addWidget(tool_panel)
        
        # Drawing area
        self.draw_area = DrawArea(self)
        layout.addWidget(self.draw_area)
        
    def set_image(self, image):
        """Set background image and adjust size
        
        Args:
            image: numpy array (BGR)
        """
        if image is None:
            return
            
        self.image = image
        height, width = image.shape[:2]
        
        # Create mask
        self.mask = np.zeros((height, width), dtype=np.uint8)
        
        # Convert to QPixmap
        bytes_per_line = 3 * width
        q_image = QImage(image.data, width, height, bytes_per_line,
                        QImage.Format.Format_RGB888).rgbSwapped()
        self.image_pixmap = QPixmap.fromImage(q_image)
        
        self.update_image_scale()
        
    def update_image_scale(self):
        """Update image scale factor and offset"""
        if self.image_pixmap is None:
            return
            
        # Calculate scale factor to fit in draw area
        draw_size = self.draw_area.size()
        pixmap_size = self.image_pixmap.size()
        
        scale_w = draw_size.width() / pixmap_size.width()
        scale_h = draw_size.height() / pixmap_size.height()
        self.scale_factor = min(scale_w, scale_h)
        
        # Calculate offset to center image
        scaled_width = pixmap_size.width() * self.scale_factor
        scaled_height = pixmap_size.height() * self.scale_factor
        self.offset_x = (draw_size.width() - scaled_width) / 2
        self.offset_y = (draw_size.height() - scaled_height) / 2
        
        self.update()
        
    def get_image_coordinates(self, pos):
        """Convert widget coordinates to image coordinates
        
        Args:
            pos: QPoint in widget coordinates
            
        Returns:
            QPointF in image coordinates
        """
        pos = self.draw_area.mapFrom(self, pos)
        x = (pos.x() - self.offset_x) / self.scale_factor
        y = (pos.y() - self.offset_y) / self.scale_factor
        
        # Clamp to image bounds
        if self.image is not None:
            x = max(0, min(x, self.image.shape[1] - 1))
            y = max(0, min(y, self.image.shape[0] - 1))
            
        return QPointF(x, y)
        
    def mode_changed(self, button):
        """Handle drawing mode change"""
        self.draw_mode = self.mode_group.id(button)
        self.temp_points.clear()
        self.current_path = QPainterPath()
        self.update()
        
    def toggle_eraser(self, checked):
        """Toggle eraser mode"""
        self.eraser_mode = checked
        
    def clear_mask(self):
        """Clear current mask"""
        if self.mask is not None:
            self.mask.fill(0)
            self.paths.clear()
            self.temp_points.clear()
            self.current_path = QPainterPath()
            self.update()
            self.mask_updated.emit(self.mask)
            
    def draw_line(self, start, end):
        """Draw line on mask"""
        if self.mask is None:
            return
            
        cv2.line(self.mask,
                 (int(start.x()), int(start.y())),
                 (int(end.x()), int(end.y())),
                 255 if not self.eraser_mode else 0,
                 max(1, int(self.pen_size / self.scale_factor)))
        self.mask_updated.emit(self.mask)
        
    def draw_shape(self, start, end):
        """Draw shape on mask"""
        if self.mask is None:
            return
            
        x1, y1 = int(start.x()), int(start.y())
        x2, y2 = int(end.x()), int(end.y())
            
        if self.draw_mode == self.DRAW_MODES['RECT']:
            x1, x2 = min(x1, x2), max(x1, x2)
            y1, y2 = min(y1, y2), max(y1, y2)
            cv2.rectangle(self.mask, (x1, y1), (x2, y2),
                        255 if not self.eraser_mode else 0, -1)
                        
        elif self.draw_mode == self.DRAW_MODES['CIRCLE']:
            center = (x1, y1)
            radius = int(((x2 - x1)**2 + (y2 - y1)**2)**0.5)
            cv2.circle(self.mask, center, radius,
                      255 if not self.eraser_mode else 0, -1)
                      
        self.mask_updated.emit(self.mask)
        
    def update_mask(self):
        """Update mask from paths"""
        if self.mask is None:
            return
            
        height, width = self.mask.shape[:2]
        mask = np.zeros((height, width), dtype=np.uint8)
        
        for path in self.paths:
            points = []
            for i in range(path.elementCount()):
                e = path.elementAt(i)
                points.append([int(e.x), int(e.y)])
                
            if points:
                points = np.array(points)
                cv2.fillPoly(mask, [points], 255)
                
        self.mask = mask
        self.mask_updated.emit(self.mask)
        
    def mousePressEvent(self, event):
        if not self.draw_area.rect().contains(event.pos()):
            return
            
        if event.button() == Qt.MouseButton.LeftButton:
            self.drawing = True
            pos = self.get_image_coordinates(event.pos())
            self.current_pos = pos
            
            if self.draw_mode == self.DRAW_MODES['FREE']:
                self.current_path = QPainterPath()
                self.current_path.moveTo(pos)
                self.last_pos = pos
                
            elif self.draw_mode == self.DRAW_MODES['POLY']:
                if not self.temp_points:
                    self.current_path = QPainterPath()
                    self.current_path.moveTo(pos)
                self.temp_points.append(pos)
                
            else:  # RECT or CIRCLE
                self.last_pos = pos
                
            self.update()
            
        elif event.button() == Qt.MouseButton.RightButton:
            if self.draw_mode == self.DRAW_MODES['POLY'] and len(self.temp_points) > 2:
                self.current_path.lineTo(self.temp_points[0])
                self.paths.append(self.current_path)
                self.update_mask()
                self.temp_points.clear()
                self.current_path = QPainterPath()
                self.update()
                
    def mouseMoveEvent(self, event):
        if not self.draw_area.rect().contains(event.pos()):
            return
            
        pos = self.get_image_coordinates(event.pos())
        self.current_pos = pos
        
        if self.drawing and self.draw_mode == self.DRAW_MODES['FREE']:
            self.current_path.lineTo(pos)
            self.draw_line(self.last_pos, pos)
            self.last_pos = pos
            self.update()
            
        elif self.draw_mode in [self.DRAW_MODES['RECT'], self.DRAW_MODES['CIRCLE']]:
            if self.drawing:
                self.update()
                
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self.draw_mode != self.DRAW_MODES['POLY']:
                self.drawing = False
                if self.draw_mode == self.DRAW_MODES['FREE']:
                    self.paths.append(self.current_path)
                    self.update_mask()
                elif self.draw_mode in [self.DRAW_MODES['RECT'], self.DRAW_MODES['CIRCLE']]:
                    self.draw_shape(self.last_pos, self.current_pos)
                    
    def paintEvent(self, event):
        if self.image_pixmap is None:
            return
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw background image
        target_rect = QRect(
            int(self.offset_x),
            int(self.offset_y),
            int(self.image_pixmap.width() * self.scale_factor),
            int(self.image_pixmap.height() * self.scale_factor)
        )
        painter.drawPixmap(target_rect, self.image_pixmap, self.image_pixmap.rect())
        
        # Configure drawing style
        scaled_width = max(1, int(self.pen_size / self.scale_factor))
        pen = QPen(self.draw_color if not self.eraser_mode else Qt.GlobalColor.black)
        pen.setWidth(scaled_width)
        painter.setPen(pen)
        
        if not self.eraser_mode:
            painter.setBrush(QColor(255, 255, 255, 64))
        
        # Apply transform for drawing
        painter.translate(self.offset_x, self.offset_y)
        painter.scale(self.scale_factor, self.scale_factor)
        
        # Draw paths
        for path in self.paths:
            painter.drawPath(path)
            
        # Draw current path
        if self.current_path:
            painter.drawPath(self.current_path)
            
        # Draw temporary shapes
        if self.drawing and self.current_pos:
            if self.draw_mode == self.DRAW_MODES['RECT']:
                rect = QRectF(self.last_pos, self.current_pos).normalized()
                painter.drawRect(rect)
            elif self.draw_mode == self.DRAW_MODES['CIRCLE']:
                center = self.last_pos
                radius = ((self.current_pos.x() - center.x())**2 + 
                         (self.current_pos.y() - center.y())**2)**0.5
                painter.drawEllipse(center, radius, radius)
                
        # Draw polygon points and lines
        if self.temp_points:
            # Draw points
            point_pen = QPen(Qt.GlobalColor.red)
            point_pen.setWidth(max(1, int(8 / self.scale_factor)))
            painter.setPen(point_pen)
            for point in self.temp_points:
                painter.drawPoint(point)
                
            # Draw lines
            line_pen = QPen(self.draw_color)
            line_pen.setWidth(scaled_width)
            painter.setPen(line_pen)
            for i in range(len(self.temp_points) - 1):
                p1 = self.temp_points[i]
                p2 = self.temp_points[i + 1]
                painter.drawLine(p1, p2)
                
            # Draw line to current position
            if self.drawing and len(self.temp_points) > 0:
                painter.drawLine(self.temp_points[-1], self.current_pos)
