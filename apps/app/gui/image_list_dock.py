"""
Image list dock implementation
图像列表停靠窗口实现
"""
import os
import logging
from PyQt6.QtWidgets import QDockWidget, QWidget, QVBoxLayout
from PyQt6.QtCore import Qt, pyqtSignal

from .thumbnail_list_widget import ThumbnailListWidget

logger = logging.getLogger(__name__)

class ImageListDock(QDockWidget):
    """Image list dock widget"""
    
    # Signal emitted when image is selected
    image_selected = pyqtSignal(str)  # path
    
    def __init__(self, parent=None):
        """Initialize dock widget"""
        super().__init__("图像列表", parent)
        self.setObjectName("image_list_dock")
        
        # Setup UI
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.list_widget = ThumbnailListWidget(thumbnail_size=80)
        self.list_widget.image_selected.connect(self._on_selection_changed)
        layout.addWidget(self.list_widget)
        
        self.setWidget(widget)
        
    def add_image(self, path):
        """Add image to list
        
        Args:
            path: Image file path
        """
        try:
            self.list_widget.add_image(path)
            logger.info(f"Successfully added image to list: {path}")
            
        except Exception as e:
            logger.error(f"Failed to add image: {str(e)}")
            
    def clear(self):
        """Clear image list"""
        self.list_widget.clear()
        
    def _on_selection_changed(self, path):
        """Handle image selection
        
        Args:
            path: Selected image path
        """
        self.image_selected.emit(path)
