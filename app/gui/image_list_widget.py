import os
import json
import shutil
from PySide6.QtWidgets import (
    QWidget, QListWidget, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QMessageBox,
    QFileDialog, QListWidgetItem, QFrame,
    QGroupBox
)
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QPixmap, QImage

import logging
logger = logging.getLogger(__name__)

class ImageBrowser(QWidget):
    image_selected = Signal(str)  # Image path signal
    images_changed = Signal(list)  # Signal emitted when images list changes

    def __init__(self):
        super().__init__()
        logger.info("Initializing ImageBrowser")
        # Initialize attributes
        self.project_dir = None
        self.list_widget = QListWidget()
        self.preview_label = QLabel()
        self.preview_label.setMinimumSize(200, 200)
        self.preview_label.setAlignment(Qt.AlignCenter)
        logger.info("Preview label initialized")

        # Create buttons
        self.btn_import = QPushButton(self.tr("Import Images"))
        self.btn_import.setToolTip(self.tr("Import images for analysis"))
        logger.info("btn_import created")
        
        self.btn_remove = QPushButton(self.tr("Remove Selected"))
        self.btn_remove.setToolTip(self.tr("Remove selected images"))
        logger.info("btn_remove created")
        
        self.btn_clear = QPushButton(self.tr("Clear All"))
        self.btn_clear.setToolTip(self.tr("Clear all images"))
        logger.info("btn_clear created")
        logger.info("Buttons created")

        # Setup UI
        self._setup_ui()
        logger.info("ImageBrowser initialization complete")

    def _setup_ui(self):
        logger.info("Setting up ImageBrowser UI")
        # Main layout
        layout = QHBoxLayout()
        logger.info("QHBoxLayout created")

        # Create button group
        button_group = QGroupBox(self.tr("Actions"))
        button_layout = QVBoxLayout()
        button_layout.addWidget(self.btn_import)
        button_layout.addWidget(self.btn_remove)
        button_layout.addWidget(self.btn_clear)
        button_group.setLayout(button_layout)
        logger.info("Button group created")
        
        # Create image list group
        list_group = QGroupBox(self.tr("Image List"))
        list_layout = QVBoxLayout()
        list_layout.addWidget(self.list_widget)
        list_group.setLayout(list_layout)
        logger.info("List group created")
        
        # Left panel
        left_panel = QVBoxLayout()
        logger.info("QVBoxLayout created")
        left_panel.addWidget(button_group)
        left_panel.addWidget(list_group)
        logger.info("Groups added to left panel")

        # Preview group
        preview_group = QGroupBox(self.tr("Preview"))
        preview_layout = QVBoxLayout()
        preview_layout.addWidget(self.preview_label)
        preview_group.setLayout(preview_layout)

        # Layout setup
        layout.addLayout(left_panel, 30)
        logger.info("Left panel added to layout")
        layout.addWidget(preview_group, 70)
        logger.info("Preview group added to layout")
        self.setLayout(layout)
        logger.info("Layout set")

        # Initial button states and preview
        self._update_button_states()
        logger.info("Button states updated")
        self.preview_label.setText(self.tr("No image selected")) # Set initial text directly
        logger.info("UI setup complete")

        # Connect signals
        self.btn_import.clicked.connect(self.import_images)
        self.btn_remove.clicked.connect(self._remove_selected)
        self.btn_clear.clicked.connect(self._confirm_clear)
        self.list_widget.itemClicked.connect(self._display_image)
        self.list_widget.itemSelectionChanged.connect(self._on_selection_changed)
        logger.info("Signals connected")

    def set_project_directory(self, project_dir):
        """Set the current project directory"""
        self.project_dir = project_dir
        self.list_widget.clear()
        self.preview_label.clear()
        self.preview_label.setText(self.tr("No image selected"))
        self._update_button_states()

    def _get_image_list(self):
        """Get list of all image paths in the list"""
        image_paths = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            path = item.data(Qt.UserRole)
            if path and os.path.exists(path):
                image_paths.append(path)
        return image_paths

    def retranslate_ui(self):
        logger.info("Retranslating ImageBrowser UI")
        self.btn_import.setText(self.tr("Import Images"))
        self.btn_remove.setText(self.tr("Remove Selected"))
        self.btn_clear.setText(self.tr("Clear All"))
        self.preview_label.setText(self.tr("No image selected"))
        logger.info("ImageBrowser UI retranslated")

    def _update_button_states(self):
        """Update button enabled states based on current selection"""
        has_items = self.list_widget.count() > 0
        has_selection = len(self.list_widget.selectedItems()) > 0
        
        self.btn_remove.setEnabled(has_selection)
        self.btn_clear.setEnabled(has_items)

    @Slot()
    def import_images(self):
        """Open file dialog to import images"""
        if not self.project_dir:
            QMessageBox.warning(self, self.tr("Warning"), 
                              self.tr("Please create or open a project first"))
            return

        file_dialog = QFileDialog()
        file_paths, _ = file_dialog.getOpenFileNames(
            self,
            self.tr("Select Images"),
            "",
            self.tr("Images (*.png *.jpg *.jpeg *.tiff *.bmp)")
        )

        if file_paths:
            for file_path in file_paths:
                # Create list item
                item = QListWidgetItem(os.path.basename(file_path))
                item.setData(Qt.UserRole, file_path)
                self.list_widget.addItem(item)
            
            self._update_button_states()
            self.images_changed.emit(self._get_image_list())

    @Slot()
    def _remove_selected(self):
        """Remove selected images from list"""
        selected_items = self.list_widget.selectedItems()
        if not selected_items:
            return

        for item in selected_items:
            self.list_widget.takeItem(self.list_widget.row(item))

        self._update_button_states()
        self.images_changed.emit(self._get_image_list())
        
        if self.list_widget.count() == 0:
            self.preview_label.clear()
            self.preview_label.setText(self.tr("No image selected"))

    @Slot()
    def _confirm_clear(self):
        """Show confirmation dialog before clearing all images"""
        if self.list_widget.count() == 0:
            return

        reply = QMessageBox.question(
            self,
            self.tr("Confirmation"),
            self.tr("Are you sure you want to remove all images?"),
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.list_widget.clear()
            self._update_button_states()
            self.images_changed.emit([])
            self.preview_label.clear()
            self.preview_label.setText(self.tr("No image selected"))

    @Slot(QListWidgetItem)
    def _display_image(self, item):
        """Display selected image in preview label"""
        if not item:
            return

        image_path = item.data(Qt.UserRole)
        if not os.path.exists(image_path):
            QMessageBox.warning(
                self,
                self.tr("Error"),
                self.tr("Image file not found: {}").format(image_path)
            )
            return

        pixmap = QPixmap(image_path)
        if pixmap.isNull():
            QMessageBox.warning(
                self,
                self.tr("Error"),
                self.tr("Failed to load image: {}").format(image_path)
            )
            return

        # Scale pixmap to fit label while maintaining aspect ratio
        scaled_pixmap = pixmap.scaled(
            self.preview_label.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        self.preview_label.setPixmap(scaled_pixmap)
        self.image_selected.emit(image_path)

    @Slot()
    def _on_selection_changed(self):
        """Handle list selection changes"""
        selected_items = self.list_widget.selectedItems()
        if selected_items:
            self._display_image(selected_items[0])
        else:
            self.preview_label.clear()
            self.preview_label.setText(self.tr("No image selected"))
        self._update_button_states()
