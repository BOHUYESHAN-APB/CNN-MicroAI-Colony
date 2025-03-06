import logging
from pathlib import Path
from typing import List, Optional
from PySide6.QtWidgets import (QListWidget, QAbstractItemView,
                           QListWidgetItem, QMessageBox)
from PySide6.QtCore import Qt, Signal
from app_pyside6.utils.i18n import i18n

logger = logging.getLogger(__name__)

class ImageListWidget(QListWidget):
    """Widget for displaying and managing image list"""
    
    image_selected = Signal(str)  # Signal emitted when image is selected
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setDragDropMode(QAbstractItemView.InternalMove)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.itemSelectionChanged.connect(self._on_selection_changed)
        self.processed_items = set()
        self.setToolTip(i18n.get('info.add_image_tip'))
        
    def dragEnterEvent(self, event):
        """Handle drag enter event"""
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()
            
    def dragMoveEvent(self, event):
        """Handle drag move event"""
        if event.mimeData().hasUrls():
            event.setDropAction(Qt.CopyAction)
            event.accept()
        else:
            event.ignore()
            
    def dropEvent(self, event):
        """Handle drop event"""
        if event.mimeData().hasUrls():
            event.setDropAction(Qt.CopyAction)
            event.accept()
            
            paths = []
            for url in event.mimeData().urls():
                path = url.toLocalFile()
                if Path(path).suffix.lower() in ['.jpg', '.jpeg', '.png']:
                    paths.append(path)
                    
            if paths:
                self.add_images(paths)
        else:
            event.ignore()
            
    def add_images(self, paths: List[str]):
        """Add images to list"""
        for path in paths:
            if not self._has_image(path):
                item = QListWidgetItem(Path(path).name)
                item.setData(Qt.UserRole, path)
                self.addItem(item)
                logger.info(f"Image loaded: {Path(path).name}")
                
    def _has_image(self, path: str) -> bool:
        """Check if image already exists in list"""
        path = str(Path(path))
        for i in range(self.count()):
            if str(Path(self.item(i).data(Qt.UserRole))) == path:
                return True
        return False
        
    def get_images(self, selected_only: bool = False) -> List[str]:
        """Get paths of all or selected images"""
        if selected_only:
            items = self.selectedItems()
        else:
            items = [self.item(i) for i in range(self.count())]
            
        return [item.data(Qt.UserRole) for item in items]
        
    def mark_processed(self, path: str, success: bool = True):
        """Mark image as processed"""
        path = str(Path(path))
        for i in range(self.count()):
            item = self.item(i)
            if str(Path(item.data(Qt.UserRole))) == path:
                if success:
                    item.setForeground(Qt.green)
                    self.processed_items.add(path)
                else:
                    item.setForeground(Qt.red)
                logger.info(f"Processing complete: {Path(path).name}")
                break
                
    def clear(self):
        """Clear all items from list and reset state"""
        # Clear items
        while self.count() > 0:
            self.takeItem(0)
        
        # Reset state
        self.processed_items.clear()
        self.clearSelection()
        self.setToolTip(i18n.get('info.add_image_tip'))
        
    def _on_selection_changed(self):
        """Handle selection change"""
        items = self.selectedItems()
        if items:
            self.image_selected.emit(items[0].data(Qt.UserRole))
            
    def retranslate_ui(self):
        """Update interface language"""
        self.setToolTip(i18n.get('info.add_image_tip'))
