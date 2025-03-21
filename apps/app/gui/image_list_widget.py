"""
Image list widget implementation
图像列表组件实现
"""
import os
import logging
from PyQt6.QtWidgets import (QListWidget, QListWidgetItem, QMenu, 
                            QMessageBox, QFileDialog)
from PyQt6.QtCore import Qt, pyqtSignal, QDir
from PyQt6.QtGui import QAction
from ..utils.thumbnail import create_thumbnail

logger = logging.getLogger(__name__)

class ImageListWidget(QListWidget):
    """Custom list widget for displaying images"""
    
    # Signal emitted when image selected
    image_selected = pyqtSignal(str)  # Emits image path
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Setup widget
        self.setViewMode(QListWidget.ViewMode.IconMode)
        self.setIconSize(Qt.QSize(64, 64))
        self.setSpacing(5)
        self.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.setStyleSheet("""
            QListWidget {
                background-color: #1e1e1e;
                border: 1px solid #3d3d3d;
            }
            QListWidget::item {
                background-color: #2d2d2d;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                padding: 4px;
            }
            QListWidget::item:selected {
                background-color: #404040;
                border: 1px solid #505050;
            }
            QListWidget::item:hover {
                background-color: #353535;
            }
        """)
        
        # Connect signals
        self.itemSelectionChanged.connect(self._on_selection_changed)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
        
    def add_image(self, path):
        """Add image to list
        
        Args:
            path (str): Image file path
            
        Returns:
            bool: True if successful
        """
        try:
            # Convert path to native format
            abs_path = QDir.toNativeSeparators(os.path.abspath(path))
            
            # Create thumbnail
            thumb = create_thumbnail(abs_path)
            if thumb is None:
                logger.error(f"Failed to create thumbnail: {abs_path}")
                return False
                
            # Create list item
            item = QListWidgetItem()
            item.setIcon(thumb)
            item.setText(os.path.basename(abs_path))
            item.setData(Qt.ItemDataRole.UserRole, abs_path)
            item.setToolTip(abs_path)
            
            # Add to list
            self.addItem(item)
            logger.info(f"Successfully added image to list: {abs_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding image {path}: {str(e)}")
            return False
            
    def _on_selection_changed(self):
        """Handle selection change"""
        items = self.selectedItems()
        if items:
            path = items[0].data(Qt.ItemDataRole.UserRole)
            self.image_selected.emit(path)
            
    def _show_context_menu(self, pos):
        """Show context menu"""
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #2d2d2d;
                color: #e0e0e0;
                border: 1px solid #505050;
            }
            QMenu::item:selected {
                background-color: #505050;
            }
        """)
        
        # Add actions
        remove_action = QAction("移除图片", self)
        remove_action.triggered.connect(self._remove_selected)
        menu.addAction(remove_action)
        
        menu.exec(self.mapToGlobal(pos))
        
    def _remove_selected(self):
        """Remove selected items"""
        for item in self.selectedItems():
            self.takeItem(self.row(item))
            
    def clear(self):
        """Clear all items"""
        super().clear()
        
    def get_image_paths(self):
        """Get list of all image paths"""
        paths = []
        for i in range(self.count()):
            item = self.item(i)
            path = item.data(Qt.ItemDataRole.UserRole)
            paths.append(path)
        return paths
