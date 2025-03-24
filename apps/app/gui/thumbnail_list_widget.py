"""
Thumbnail list widget implementation
缩略图列表窗口实现
"""
from PyQt6.QtWidgets import (QListWidget, QListWidgetItem)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QIcon, QPixmap, QImage
import os
import cv2

from ..utils.image_preprocessing import load_image

class ThumbnailListWidget(QListWidget):
    """Thumbnail list widget with image preview"""
    
    # Signal emitted when image is selected
    image_selected = pyqtSignal(str)  # image path
    
    def __init__(self, parent=None, thumbnail_size=64):
        """Initialize widget
        
        Args:
            parent: Parent widget
            thumbnail_size: Size of thumbnail in pixels
        """
        super().__init__(parent)
        
        self.thumbnail_size = thumbnail_size
        self.setIconSize(QSize(thumbnail_size, thumbnail_size))
        self.setViewMode(QListWidget.ViewMode.IconMode)
        self.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.setSpacing(5)
        self.setMovement(QListWidget.Movement.Static)
        
        # Connect signals
        self.itemSelectionChanged.connect(self._on_selection_changed)
        
    def add_image(self, image_path):
        """Add image to list
        
        Args:
            image_path: Path to image file
        """
        try:
            # Load image using preprocessing utility
            image = load_image(image_path)
            if image is None:
                raise ValueError(f"Failed to load image: {image_path}")
                
            # Resize image to thumbnail size
            height, width = image.shape[:2]
            aspect = width / height
            if width > height:
                new_width = self.thumbnail_size
                new_height = int(new_width / aspect)
            else:
                new_height = self.thumbnail_size
                new_width = int(new_height * aspect)
                
            thumbnail = cv2.resize(image, (new_width, new_height))
            
            # Convert to QPixmap
            height, width = thumbnail.shape[:2]
            bytes_per_line = 3 * width
            q_image = QImage(thumbnail.data, width, height, bytes_per_line,
                           QImage.Format.Format_RGB888).rgbSwapped()
            pixmap = QPixmap.fromImage(q_image)
            
            # Create list item
            item = QListWidgetItem(
                QIcon(pixmap),
                os.path.basename(image_path)
            )
            item.setData(Qt.ItemDataRole.UserRole, image_path)
            
            # Set size hint for proper layout
            item.setSizeHint(
                QSize(self.thumbnail_size + 20, self.thumbnail_size + 20)
            )
            
            self.addItem(item)
            
        except Exception as e:
            print(f"Error adding image to list: {str(e)}")
            
    def clear(self):
        """Clear list"""
        super().clear()
            
    def _on_selection_changed(self):
        """Handle selection change"""
        items = self.selectedItems()
        if items:
            path = items[0].data(Qt.ItemDataRole.UserRole)
            self.image_selected.emit(path)
