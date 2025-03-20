"""
Image list dock widget implementation
图像列表停靠窗口实现
"""
import os
import logging
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QListWidget,
                            QPushButton, QFileDialog, QListWidgetItem,
                            QMenu, QMessageBox, QToolBar)
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QDir
from PyQt6.QtGui import QPixmap, QIcon, QAction
from .base_dock_widget import BaseDockWidget
from .toolbar_constants import SMALL_ICON_SIZE, TOOLBAR_STYLE
from ..utils.thumbnail import create_thumbnail
from ..utils.i18n import translate

logger = logging.getLogger(__name__)

class ImageListWidget(QListWidget):
    """Custom list widget for images"""
    def __init__(self):
        super().__init__()
        self.setIconSize(QSize(64, 64))
        self.setStyleSheet("""
            QListWidget {
                background: #1e1e1e;
                border: none;
            }
            QListWidget::item {
                background: #2d2d2d;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                margin: 2px;
                padding: 4px;
            }
            QListWidget::item:selected {
                background: #404040;
                border: 1px solid #4b6eaf;
            }
            QListWidget::item:hover {
                background: #353535;
            }
        """)

class ImageListDock(BaseDockWidget):
    """Image list dock widget with enhanced docking capabilities"""
    
    # Signal emitted when image is selected
    image_selected = pyqtSignal(str)  # path of selected image
    
    def __init__(self, parent=None):
        super().__init__("图像列表", parent)
        self.setup_ui()
        
    def setup_ui(self):
        """Setup user interface"""
        # Create toolbar
        toolbar = QToolBar()
        toolbar.setIconSize(SMALL_ICON_SIZE)
        toolbar.setStyleSheet(TOOLBAR_STYLE)
        
        # Add images button
        self.add_btn = QPushButton(translate("添加图片"))
        self.add_btn.clicked.connect(self.add_images)
        self.add_btn.setEnabled(False)  # Disabled until project is opened
        toolbar.addWidget(self.add_btn)
        
        self.add_widget(toolbar)
        
        # Image list
        self.list_widget = ImageListWidget()
        self.list_widget.itemSelectionChanged.connect(self.on_selection_changed)
        self.list_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(self.show_context_menu)
        
        self.set_central_widget(self.list_widget)
        
        # Enable dock features
        self.setObjectName("image_list_dock")
                
    def add_images(self):
        """Add images to list"""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            translate("选择图片"),
            "",
            "Images (*.png *.jpg *.jpeg *.bmp)"
        )
        
        if files:
            for file_path in files:
                self.add_image(file_path)
                
    def add_image(self, path):
        """Add single image to list"""
        try:
            # Convert path to native format
            abs_path = QDir.toNativeSeparators(os.path.abspath(path))
            logger.debug(f"Adding image to list: {abs_path}")
            
            # Create thumbnail
            thumbnail = create_thumbnail(abs_path, (64, 64))
            
            # Create item
            item = QListWidgetItem()
            item.setIcon(QIcon(QPixmap.fromImage(thumbnail)))
            item.setText(os.path.basename(abs_path))
            item.setData(Qt.ItemDataRole.UserRole, abs_path)
            
            # Add to list
            self.list_widget.addItem(item)
            logger.info(f"Successfully added image to list: {abs_path}")
            
        except Exception as e:
            logger.error(f"Failed to add image: {str(e)}")
            logger.debug(f"Attempted path: {path}", exc_info=True)
            QMessageBox.critical(
                self,
                translate("错误"),
                translate("无法加载图片: ") + str(e)
            )
            
    def on_selection_changed(self):
        """Handle selection change"""
        items = self.list_widget.selectedItems()
        if items:
            path = items[0].data(Qt.ItemDataRole.UserRole)
            logger.debug(f"Selected image: {path}")
            self.image_selected.emit(path)
            
    def show_context_menu(self, pos):
        """Show context menu"""
        item = self.list_widget.itemAt(pos)
        if not item:
            return
            
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background: #2d2d2d;
                border: 1px solid #3d3d3d;
            }
            QMenu::item {
                padding: 5px 20px;
                color: #e0e0e0;
            }
            QMenu::item:selected {
                background: #404040;
            }
        """)
        
        # Add actions
        remove_action = QAction(translate("移除"), self)
        remove_action.triggered.connect(lambda: self.remove_image(item))
        menu.addAction(remove_action)
        
        menu.exec(self.list_widget.viewport().mapToGlobal(pos))
        
    def remove_image(self, item):
        """Remove image from list"""
        path = item.data(Qt.ItemDataRole.UserRole)
        logger.debug(f"Removing image from list: {path}")
        self.list_widget.takeItem(self.list_widget.row(item))
        logger.info(f"Successfully removed image: {path}")
        
    def get_all_images(self):
        """Get paths of all images"""
        paths = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            paths.append(item.data(Qt.ItemDataRole.UserRole))
        return paths
