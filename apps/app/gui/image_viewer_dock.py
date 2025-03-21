"""
Image viewer dock implementation
图像查看器停靠窗口实现
"""
import os
import logging
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QToolBar, QMessageBox
from PyQt6.QtCore import Qt, QSize, QDir
from PyQt6.QtGui import QAction
from .base_dock_widget import BaseDockWidget
from .toolbar_constants import SMALL_ICON_SIZE, TOOLBAR_STYLE
from .image_viewer import ImageViewer
from ..utils.i18n import translate

logger = logging.getLogger(__name__)

class ImageViewerDock(BaseDockWidget):
    """Image viewer dock widget with enhanced docking capabilities"""
    
    def __init__(self, parent=None):
        super().__init__("图像查看", parent)
        self.setup_ui()
        
    def setup_ui(self):
        """Setup user interface"""
        # Create toolbar
        toolbar = QToolBar()
        toolbar.setIconSize(SMALL_ICON_SIZE)
        toolbar.setStyleSheet(TOOLBAR_STYLE)
        
        # Add zoom actions
        zoom_in_action = QAction(translate("放大 (Ctrl++)"), self)
        zoom_in_action.triggered.connect(self.zoom_in)
        toolbar.addAction(zoom_in_action)
        
        zoom_out_action = QAction(translate("缩小 (Ctrl+-)"), self)
        zoom_out_action.triggered.connect(self.zoom_out)
        toolbar.addAction(zoom_out_action)
        
        zoom_fit_action = QAction(translate("适应窗口 (Ctrl+0)"), self)
        zoom_fit_action.triggered.connect(self.zoom_fit)
        toolbar.addAction(zoom_fit_action)
        
        # Add toolbar to dock
        self.add_widget(toolbar)
        
        # Create image viewer
        self.viewer = ImageViewer()
        self.set_central_widget(self.viewer)
        
        # Enable dock features
        self.setObjectName("image_viewer_dock")
        
    def load_image(self, path):
        """Load image from path"""
        try:
            # Convert path to native format
            abs_path = QDir.toNativeSeparators(os.path.abspath(path))
            logger.debug(f"Loading image from: {abs_path}")
            
            # Try to load the image
            success = self.viewer.load_image(abs_path)
            
            # Log result
            if success:
                logger.info(f"Successfully loaded image: {abs_path}")
            else:
                logger.error(f"Failed to load image: {abs_path}")
                QMessageBox.critical(
                    self,
                    translate("错误"),
                    translate("无法加载图片: {}").format(abs_path)
                )
                
            return success
            
        except Exception as e:
            logger.error(f"Error loading image: {str(e)}")
            logger.debug(f"Attempted path: {abs_path}", exc_info=True)
            QMessageBox.critical(
                self,
                translate("错误"),
                translate("加载图片时发生错误: {}").format(str(e))
            )
            return False
            
    def zoom_in(self):
        """Zoom in"""
        self.viewer.zoom_level *= self.viewer.ZOOM_FACTOR
        self.viewer.zoom_level = min(10.0, self.viewer.zoom_level)
        self.viewer.update_display()
        
    def zoom_out(self):
        """Zoom out"""
        self.viewer.zoom_level /= self.viewer.ZOOM_FACTOR
        self.viewer.zoom_level = max(0.1, self.viewer.zoom_level)
        self.viewer.update_display()
        
    def zoom_fit(self):
        """Fit image to window"""
        self.viewer.zoom_level = 1.0
        self.viewer.update_display()
        
    def reset_zoom(self):
        """Reset zoom to original size"""
        self.viewer.zoom_level = 1.0
        self.viewer.update_display()

    def clear(self):
        """Clear current image"""
        self.viewer.clear()

    def minimumSizeHint(self):
        """Provide reasonable minimum size"""
        return QSize(640, 480)
