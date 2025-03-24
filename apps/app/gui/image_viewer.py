"""
Image viewer implementation
图像查看器实现
"""
from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene
from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QPixmap, QPainter

class ImageViewer(QGraphicsView):
    """Image viewer widget"""
    
    def __init__(self, parent=None):
        """Initialize viewer"""
        super().__init__(parent)
        
        # Create scene
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        
        # Setup viewer
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        
        # Variables for panning
        self.pan_start = None
        self.last_pos = None
        
        # Current scale
        self.current_scale = 1.0
        
        # Current pixmap item
        self.pixmap_item = None
        
    def set_pixmap(self, pixmap):
        """Set pixmap to display
        
        Args:
            pixmap: QPixmap to display
        """
        # Remove old pixmap
        self.scene.clear()
        
        # Add new pixmap
        self.pixmap_item = self.scene.addPixmap(pixmap)
        
        # Reset view
        self.reset_view()
        
    def reset_view(self):
        """Reset view to show entire image"""
        if not self.pixmap_item:
            return
            
        # Get pixmap rect
        rect = self.pixmap_item.boundingRect()
        
        # Reset transformation
        self.resetTransform()
        self.current_scale = 1.0
        
        # Scale to fit viewport
        view_rect = self.viewport().rect().adjusted(10, 10, -10, -10)
        scale = min(view_rect.width() / rect.width(),
                   view_rect.height() / rect.height())
        self.scale(scale, scale)
        self.current_scale = scale
        
        # Center image
        self.centerOn(rect.center())
        
    def wheelEvent(self, event):
        """Handle mouse wheel for zooming"""
        if not self.pixmap_item:
            return
            
        # Get scale factor
        factor = 1.1
        if event.angleDelta().y() < 0:
            factor = 0.9
            
        # Calculate new scale
        new_scale = self.current_scale * factor
        
        # Limit zoom range
        if 0.1 <= new_scale <= 10.0:
            self.scale(factor, factor)
            self.current_scale = new_scale
            
    def mousePressEvent(self, event):
        """Handle mouse press for panning"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.pan_start = event.pos()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
        else:
            super().mousePressEvent(event)
            
    def mouseMoveEvent(self, event):
        """Handle mouse move for panning"""
        if self.pan_start is not None:
            # Calculate movement
            delta = event.pos() - self.pan_start
            self.pan_start = event.pos()
            
            # Pan view
            self.horizontalScrollBar().setValue(
                self.horizontalScrollBar().value() - delta.x()
            )
            self.verticalScrollBar().setValue(
                self.verticalScrollBar().value() - delta.y()
            )
            
            event.accept()
        else:
            super().mouseMoveEvent(event)
            
    def mouseReleaseEvent(self, event):
        """Handle mouse release"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.pan_start = None
            self.setCursor(Qt.CursorShape.ArrowCursor)
            event.accept()
        else:
            super().mouseReleaseEvent(event)
            
    def resizeEvent(self, event):
        """Handle resize event"""
        super().resizeEvent(event)
        
        if self.pixmap_item:
            self.reset_view()
