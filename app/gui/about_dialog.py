"""
About Dialog
"""
import os
import logging
from typing import Dict, List
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                            QPushButton, QWidget)
from PyQt6.QtGui import QPixmap, QIcon
from PyQt6.QtCore import Qt

from ..utils.i18n import tr
from ..utils.path_manager import get_resources_dir
import app

logger = logging.getLogger(__name__)

class AboutDialog(QDialog):
    """About dialog"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """Setup user interface"""
        self.setWindowTitle(tr("about.title"))
        self.setFixedSize(400, 300)
        self.setModal(True)
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Logo
        logo_path = os.path.join(get_resources_dir(), "icons", "app.png")
        if os.path.exists(logo_path):
            logo_label = QLabel()
            logo_pixmap = QPixmap(logo_path)
            if not logo_pixmap.isNull():
                scaled = logo_pixmap.scaled(
                    64, 64,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                logo_label.setPixmap(scaled)
                logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                layout.addWidget(logo_label)
        
        # App name and version
        name_label = QLabel(f"{app.APP_NAME} {app.__version__}")
        name_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(name_label)
        
        # Description
        desc_label = QLabel(tr("about.description"))
        desc_label.setWordWrap(True)
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(desc_label)
        
        # Copyright
        copyright_label = QLabel(
            f"{tr('about.copyright')} © {app.__author__}"
        )
        copyright_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(copyright_label)
        
        # License
        license_label = QLabel(
            f"{tr('about.license')}: {app.__license__}"
        )
        license_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(license_label)
        
        # Website
        website_label = QLabel(
            f"{tr('about.website')}: "
            f"<a href='{app.__website__}'>{app.__website__}</a>"
        )
        website_label.setOpenExternalLinks(True)
        website_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(website_label)
        
        # Credits
        credits_label = QLabel(tr("about.acknowledgments"))
        credits_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(credits_label)
        
        # Built with packages
        packages = [
            "Python",
            "PyQt6",
            "OpenCV",
            "NumPy",
            "TensorFlow"
        ]
        
        packages_label = QLabel(", ".join(packages))
        packages_label.setWordWrap(True)
        packages_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(packages_label)
        
        # Close button
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        close_button = QPushButton(tr("dialog.close"))
        close_button.clicked.connect(self.accept)
        button_layout.addWidget(close_button)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        # Add stretch to center content vertically
        layout.insertStretch(0)
        layout.addStretch()
