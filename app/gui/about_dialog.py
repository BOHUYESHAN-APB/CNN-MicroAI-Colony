"""
About Dialog
"""
import os
import logging
from typing import Dict, List
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                            QPushButton, QWidget, QTabWidget, QScrollArea,
                            QTextEdit)
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
        self.resize(600, 400)
        self.setModal(True)
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Header section
        header_layout = QVBoxLayout()
        
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
                header_layout.addWidget(logo_label)
        
        # App name and version
        name_label = QLabel(f"{app.APP_NAME} {app.__version__}")
        name_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(name_label)
        
        # Description
        desc_label = QLabel(tr("about.description"))
        desc_label.setWordWrap(True)
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(desc_label)
        
        layout.addLayout(header_layout)
        
        # Tab widget
        self.tabs = QTabWidget()
        
        # License tab
        license_tab = QWidget()
        license_layout = QVBoxLayout()
        license_tab.setLayout(license_layout)
        
        license_text = QTextEdit()
        license_text.setReadOnly(True)
        
        # Read license from file
        try:
            with open("LICENSE", "r", encoding="utf-8") as f:
                license_content = f.read()
            license_text.setText(license_content)
        except Exception as e:
            logger.error(f"Error reading LICENSE file: {e}")
            license_text.setText(tr("error.license_load_failed"))
            
        license_layout.addWidget(license_text)
        self.tabs.addTab(license_tab, tr("about.tab.license"))
        
        # Usage tab (Dependencies)
        usage_tab = QWidget()
        usage_layout = QVBoxLayout()
        usage_tab.setLayout(usage_layout)
        
        deps_text = QTextEdit()
        deps_text.setReadOnly(True)
        
        # Core dependencies
        core_deps = [
            "Python - " + tr("about.deps.python"),
            "PyQt6 - " + tr("about.deps.pyqt"),
            "OpenCV - " + tr("about.deps.opencv"),
            "NumPy - " + tr("about.deps.numpy"),
            "TensorFlow - " + tr("about.deps.tensorflow")
        ]
        
        # Format dependencies text
        deps_content = tr("about.deps.title") + "\n\n"
        deps_content += "\n".join(f"• {dep}" for dep in core_deps)
        deps_text.setText(deps_content)
        
        usage_layout.addWidget(deps_text)
        self.tabs.addTab(usage_tab, tr("about.tab.usage"))
        
        # GitHub tab
        github_tab = QWidget()
        github_layout = QVBoxLayout()
        github_tab.setLayout(github_layout)
        
        github_label = QLabel(
            f"""<p>{tr("about.github.description")}</p>
            <p><a href='{app.__website__}'>{app.__website__}</a></p>"""
        )
        github_label.setOpenExternalLinks(True)
        github_label.setWordWrap(True)
        github_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        github_layout.addWidget(github_label)
        
        self.tabs.addTab(github_tab, tr("about.tab.github"))
        
        layout.addWidget(self.tabs)
        
        # Bottom buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        close_button = QPushButton(tr("dialog.close"))
        close_button.clicked.connect(self.accept)
        button_layout.addWidget(close_button)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)

    def retranslateUi(self):
        """Update translations"""
        self.setWindowTitle(tr("about.title"))
        
        # Update description
        for child in self.findChildren(QLabel):
            if child.text() == tr("about.description", locale="en"):
                child.setText(tr("about.description"))
                break
        
        # Update tab titles
        self.tabs.setTabText(0, tr("about.tab.license"))
        self.tabs.setTabText(1, tr("about.tab.usage"))
        self.tabs.setTabText(2, tr("about.tab.github"))
        
        # Update close button
        for button in self.findChildren(QPushButton):
            if button.text() == tr("dialog.close", locale="en"):
                button.setText(tr("dialog.close"))
