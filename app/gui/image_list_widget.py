"""
Image List Widget
"""
import os
import logging
from typing import List, Optional
from pathlib import Path

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                            QListWidget, QListWidgetItem, QFileDialog, QLabel,
                            QMessageBox)
from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QIcon, QPixmap

from ..utils.i18n import tr
from ..utils.project_manager import ProjectManager

logger = logging.getLogger(__name__)

class ImageListWidget(QWidget):
    """Widget for displaying and managing list of images"""
    
    # Signals
    image_selected = pyqtSignal(str)  # Emits path of selected image
    image_added = pyqtSignal(str)     # Emits path of added image
    image_removed = pyqtSignal(str)   # Emits path of removed image
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.project = ProjectManager()
        self.setup_ui()
        
    def setup_ui(self):
        """Setup user interface"""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Toolbar
        toolbar = QHBoxLayout()
        
        # Import button
        self.import_btn = QPushButton(tr("image_browser.import_images"))
        self.import_btn.clicked.connect(self.import_images)
        toolbar.addWidget(self.import_btn)
        
        # Clear button
        self.clear_btn = QPushButton(tr("image_browser.clear_all"))
        self.clear_btn.clicked.connect(self.clear_all)
        toolbar.addWidget(self.clear_btn)
        
        toolbar.addStretch()
        layout.addLayout(toolbar)
        
        # Image list
        self.list_widget = QListWidget()
        self.list_widget.currentItemChanged.connect(self.on_selection_changed)
        layout.addWidget(self.list_widget)
        
        # Preview
        preview_layout = QVBoxLayout()
        preview_label = QLabel(tr("image_browser.preview"))
        preview_layout.addWidget(preview_label)
        
        self.preview_image = QLabel()
        self.preview_image.setFixedSize(200, 200)
        self.preview_image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        preview_layout.addWidget(self.preview_image)
        
        layout.addLayout(preview_layout)

    def retranslateUi(self):
        """Retranslate UI elements"""
        self.import_btn.setText(tr("image_browser.import_images"))
        self.clear_btn.setText(tr("image_browser.clear_all"))
        # Find the preview label and update its text
        for child in self.findChildren(QLabel):
            if child.text() == "Preview":  # Just check for default text
                child.setText(tr("image_browser.preview"))
                break

    def clear(self):
        """Clear image list"""
        self.list_widget.clear()
        self.preview_image.clear()
        
    def clear_all(self):
        """Clear all images after confirmation"""
        if self.list_widget.count() == 0:
            return
            
        reply = QMessageBox.question(
            self,
            tr("dialog.warning"),
            tr("image_browser.clear_confirm"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            paths = []
            for i in range(self.list_widget.count()):
                item = self.list_widget.item(i)
                paths.append(item.data(Qt.ItemDataRole.UserRole))
                
            for path in paths:
                self.remove_image(path)
                
            self.clear()
        
    def add_image(self, path: str):
        """Add image to list"""
        path = str(Path(path))
        
        # Create list item
        item = QListWidgetItem()
        item.setText(os.path.basename(path))
        item.setData(Qt.ItemDataRole.UserRole, path)
        
        # Add thumbnail if possible
        thumb = QPixmap(path)
        if not thumb.isNull():
            thumb = thumb.scaled(
                32, 32,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            item.setIcon(QIcon(thumb))
            
        self.list_widget.addItem(item)
        self.image_added.emit(path)
        
    def remove_image(self, path: str):
        """Remove image from list"""
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == path:
                self.list_widget.takeItem(i)
                self.image_removed.emit(path)
                break
                
    def import_images(self):
        """Open file dialog to import images"""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            tr("image_browser.import_images"),
            "",
            "Images (*.png *.jpg *.jpeg *.tif *.tiff);;All Files (*.*)"
        )
        
        if files:
            for file in files:
                if self.project.add_image(file):
                    self.add_image(file)
                    
    @pyqtSlot('QListWidgetItem*', 'QListWidgetItem*')
    def on_selection_changed(self, current, previous):
        """Handle list selection change"""
        if current:
            path = current.data(Qt.ItemDataRole.UserRole)
            self.update_preview(path)
            self.image_selected.emit(path)
        else:
            self.preview_image.clear()
            
    def update_preview(self, path: str):
        """Update preview image"""
        pixmap = QPixmap(path)
        if not pixmap.isNull():
            scaled = pixmap.scaled(
                200, 200,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.preview_image.setPixmap(scaled)
        else:
            self.preview_image.clear()
            
    def get_selected_image(self) -> Optional[str]:
        """Get path of selected image"""
        item = self.list_widget.currentItem()
        if item:
            return item.data(Qt.ItemDataRole.UserRole)
        return None
        
    def get_all_images(self) -> List[str]:
        """Get list of all image paths"""
        paths = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            paths.append(item.data(Qt.ItemDataRole.UserRole))
        return paths
