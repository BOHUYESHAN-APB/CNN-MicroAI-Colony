"""
Image List Widget - Minimal Implementation with clear and add_image
"""
import os
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QListWidget, QListWidgetItem
from PyQt6.QtCore import pyqtSignal, Qt

class ImageListWidget(QWidget):
    """Minimal image list widget with clear and add_image methods"""

    image_selected = pyqtSignal(str)
    image_removed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout()
        self.header_label = QLabel("Images")
        layout.addWidget(self.header_label)
        
        self.list_widget = QListWidget()
        self.list_widget.itemSelectionChanged.connect(self._on_selection_changed)
        layout.addWidget(self.list_widget)
        
        # Apply dark theme
        self.setStyleSheet("""
            QLabel {
                color: #e0e0e0;
                font-weight: bold;
                font-size: 14px;
                margin-bottom: 4px;
            }
            QListWidget {
                background-color: #2b2b2b;
                border: 1px solid #1e1e1e;
                border-radius: 4px;
                color: #e0e0e0;
            }
            QListWidget::item {
                padding: 4px;
                border-bottom: 1px solid #3a3a3a;
            }
            QListWidget::item:selected {
                background-color: #3c4147;
                color: #ffffff;
            }
            QListWidget::item:hover {
                background-color: #353b41;
            }
        """)
        
        self.setLayout(layout)
        self.update_header()

    def _on_selection_changed(self):
        """Handle selection change in list widget"""
        items = self.list_widget.selectedItems()
        if items:
            image_path = items[0].data(Qt.ItemDataRole.UserRole)
            self.image_selected.emit(image_path)

    def update_header(self):
        """Update header label with image count"""
        self.header_label.setText(f"Images ({self.list_widget.count()})")

    def clear(self):
        """Clear image list"""
        self.list_widget.clear()
        self.update_header()

    def add_image(self, image_path):
        """Add image to list"""
        item = QListWidgetItem(os.path.basename(image_path))
        item.setData(Qt.ItemDataRole.UserRole, image_path)
        self.list_widget.addItem(item)
        self.update_header()
