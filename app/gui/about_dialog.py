import logging
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QTextBrowser,
    QDialogButtonBox, QTabWidget, QPushButton,
    QGroupBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from .. import __version__

logger = logging.getLogger(__name__)

class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        logger.info("Initializing AboutDialog")
        
        self.setWindowTitle(self.tr("About MicroAI-Colony"))
        self.resize(600, 400)
        
        self._setup_ui()
        logger.info("AboutDialog initialization complete")

    def retranslateUi(self):
        """Retranslate UI elements."""
        self.setWindowTitle(self.tr("About MicroAI-Colony"))
        self.about_group.setTitle(self.tr("About"))
        self.license_group.setTitle(self.tr("License"))
        self.thirdparty_group.setTitle(self.tr("Third Party"))
        self.ok_button.setText(self.tr("OK"))
        self.ok_button.setToolTip(self.tr("Close this dialog"))

        # Update tab texts
        self.tab_widget.setTabText(0, self.tr("About"))
        self.tab_widget.setTabText(1, self.tr("License"))
        self.tab_widget.setTabText(2, self.tr("Third Party"))
        
    def _setup_ui(self):
        """Setup dialog UI"""
        layout = QVBoxLayout()
        
        # Tab widget for different sections
        self.tab_widget = QTabWidget()
        
        # About section
        self.about_group = QGroupBox(self.tr("About"))
        about_layout = QVBoxLayout()
        self.about_browser = QTextBrowser()
        self.about_browser.setOpenExternalLinks(True)
        self.about_browser.setStyleSheet("""
            QTextBrowser {
                background-color: #21252b;
                border: none;
            }
        """)
        self.about_browser.setHtml(self._get_about_text())
        about_layout.addWidget(self.about_browser)
        self.about_group.setLayout(about_layout)
        self.tab_widget.addTab(self.about_group, self.tr("About"))
        
        # License section
        self.license_group = QGroupBox(self.tr("License"))
        license_layout = QVBoxLayout()
        self.license_browser = QTextBrowser()
        self.license_browser.setOpenExternalLinks(True)
        self.license_browser.setStyleSheet("""
            QTextBrowser {
                background-color: #21252b;
                border: none;
            }
        """)
        self.license_browser.setHtml(self._get_license_text())
        license_layout.addWidget(self.license_browser)
        self.license_group.setLayout(license_layout)
        self.tab_widget.addTab(self.license_group, self.tr("License"))
        
        # Third party section
        self.thirdparty_group = QGroupBox(self.tr("Third Party"))
        thirdparty_layout = QVBoxLayout()
        self.thirdparty_browser = QTextBrowser()
        self.thirdparty_browser.setOpenExternalLinks(True)
        self.thirdparty_browser.setStyleSheet("""
            QTextBrowser {
                background-color: #21252b;
                border: none;
            }
        """)
        self.thirdparty_browser.setHtml(self._get_thirdparty_text())
        thirdparty_layout.addWidget(self.thirdparty_browser)
        self.thirdparty_group.setLayout(thirdparty_layout)
        self.tab_widget.addTab(self.thirdparty_group, self.tr("Third Party"))
        
        layout.addWidget(self.tab_widget)
        
        # Dialog button
        button_box = QDialogButtonBox()
        self.ok_button = QPushButton(self.tr("OK"))
        self.ok_button.setDefault(True)
        self.ok_button.setToolTip(self.tr("Close this dialog"))
        button_box.addButton(self.ok_button, QDialogButtonBox.AcceptRole)
        button_box.accepted.connect(self.accept)
        layout.addWidget(button_box)
        
        self.setLayout(layout)
        
    def _get_about_text(self):
        """Get formatted about text"""
        return f"""
        <div style='text-align: center;'>
            <h2 style='color: #61afef;'>MicroAI-Colony</h2>
            <p style='color: #98c379;'>Version {__version__}</p>
            <p>
            MicroAI-Colony is an intelligent software solution for automated bacterial colony counting
            using advanced image processing and machine learning techniques.
            </p>
            <p>
            Copyright © 2025 MicroAI Team. All rights reserved.
            </p>
            <p>
            <a href='https://github.com/BOHUYESHAN-APB/CNN-MicroAI-Colony' style='color: #61afef;'>
                Project Homepage
            </a>
            </p>
        </div>
        """
        
    def _get_license_text(self):
        """Get formatted license text"""
        return """
        <h3 style='color: #61afef;'>GNU General Public License v3.0</h3>
        <p>
        This program is free software: you can redistribute it and/or modify
        it under the terms of the GNU General Public License as published by
        the Free Software Foundation, either version 3 of the License, or
        (at your option) any later version.
        </p>
        <p>
        This program is distributed in the hope that it will be useful,
        but WITHOUT ANY WARRANTY; without even the implied warranty of
        MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
        GNU General Public License for more details.
        </p>
        <p>
        You should have received a copy of the GNU General Public License
        along with this program. If not, see 
        <a href='https://www.gnu.org/licenses/' style='color: #61afef;'>
            https://www.gnu.org/licenses/
        </a>.
        </p>
        """
        
    def _get_thirdparty_text(self):
        """Get formatted third party licenses text"""
        return """
        <h3 style='color: #61afef;'>Third Party Software</h3>
        
        <h4 style='color: #98c379;'>PySide6</h4>
        <p>
        The Qt for Python project (PySide6) is licensed under the GNU Lesser General Public License (LGPL) version 3.
        </p>
        <p>
        <a href='https://www.qt.io/licensing/' style='color: #61afef;'>Qt Licensing</a>
        </p>
        
        <h4 style='color: #98c379;'>PyTorch</h4>
        <p>
        PyTorch is licensed under the BSD-style license.
        </p>
        <p>
        <a href='https://github.com/pytorch/pytorch/blob/master/LICENSE' style='color: #61afef;'>
            PyTorch License
        </a>
        </p>
        
        <h4 style='color: #98c379;'>NumPy</h4>
        <p>
        Copyright (c) 2005-2023, NumPy Developers.<br>
        Licensed under the BSD 3-Clause License.
        </p>
        
        <h4 style='color: #98c379;'>OpenCV</h4>
        <p>
        OpenCV is released under a BSD 3-Clause License.
        </p>
        <p>
        <a href='https://github.com/opencv/opencv/blob/master/LICENSE' style='color: #61afef;'>
            OpenCV License
        </a>
        </p>
        
        <h4 style='color: #98c379;'>Matplotlib</h4>
        <p>
        Matplotlib is licensed under the PSF (Python Software Foundation) License.
        </p>
        """
