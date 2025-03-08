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
        
        self.setWindowTitle(self.tr("About Colony Detection"))
        self.resize(600, 400)
        
        self._setup_ui()
        logger.info("AboutDialog initialization complete")
        
    def _setup_ui(self):
        """Setup dialog UI"""
        layout = QVBoxLayout()
        
        # Tab widget for different sections
        tab_widget = QTabWidget()
        
        # About section
        about_group = QGroupBox(self.tr("About"))
        about_layout = QVBoxLayout()
        about_browser = QTextBrowser()
        about_browser.setOpenExternalLinks(True)
        about_browser.setStyleSheet("""
            QTextBrowser {
                background-color: #21252b;
                border: none;
            }
        """)
        about_browser.setHtml(self._get_about_text())
        about_layout.addWidget(about_browser)
        about_group.setLayout(about_layout)
        tab_widget.addTab(about_group, self.tr("About"))
        
        # License section
        license_group = QGroupBox(self.tr("License"))
        license_layout = QVBoxLayout()
        license_browser = QTextBrowser()
        license_browser.setOpenExternalLinks(True)
        license_browser.setStyleSheet("""
            QTextBrowser {
                background-color: #21252b;
                border: none;
            }
        """)
        license_browser.setHtml(self._get_license_text())
        license_layout.addWidget(license_browser)
        license_group.setLayout(license_layout)
        tab_widget.addTab(license_group, self.tr("License"))
        
        # Third party section
        thirdparty_group = QGroupBox(self.tr("Third Party"))
        thirdparty_layout = QVBoxLayout()
        thirdparty_browser = QTextBrowser()
        thirdparty_browser.setOpenExternalLinks(True)
        thirdparty_browser.setStyleSheet("""
            QTextBrowser {
                background-color: #21252b;
                border: none;
            }
        """)
        thirdparty_browser.setHtml(self._get_thirdparty_text())
        thirdparty_layout.addWidget(thirdparty_browser)
        thirdparty_group.setLayout(thirdparty_layout)
        tab_widget.addTab(thirdparty_group, self.tr("Third Party"))
        
        layout.addWidget(tab_widget)
        
        # Dialog button
        button_box = QDialogButtonBox()
        ok_button = QPushButton(self.tr("OK"))
        ok_button.setDefault(True)
        ok_button.setToolTip(self.tr("Close this dialog"))
        button_box.addButton(ok_button, QDialogButtonBox.AcceptRole)
        button_box.accepted.connect(self.accept)
        layout.addWidget(button_box)
        
        self.setLayout(layout)
        
    def _get_about_text(self):
        """Get formatted about text"""
        return f"""
        <div style='text-align: center;'>
            <h2 style='color: #61afef;'>Colony Detection</h2>
            <p style='color: #98c379;'>Version {__version__}</p>
            <p>
            Colony Detection is an intelligent software solution for automated bacterial colony counting
            using advanced image processing and machine learning techniques.
            </p>
            <p>
            Copyright © 2025 Colony Detection Team. All rights reserved.
            </p>
            <p>
            <a href='https://github.com/example/colony-detection' style='color: #61afef;'>
                Project Homepage
            </a>
            </p>
        </div>
        """
        
    def _get_license_text(self):
        """Get formatted license text"""
        return """
        <h3 style='color: #61afef;'>Colony Detection Software License</h3>
        <p>
        This software is licensed under the MIT License.
        </p>
        <pre style='background-color: #282c34; padding: 10px; border-radius: 4px;'>
MIT License

Copyright (c) 2025 Colony Detection Team

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
        </pre>
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
        <p>From PyTorch:</p>
        <pre style='background-color: #282c34; padding: 10px; border-radius: 4px;'>
Copyright (c) 2016-     Facebook, Inc            (Adam Paszke)
Copyright (c) 2014-     Facebook, Inc            (Soumith Chintala)
Copyright (c) 2011-2014 Idiap Research Institute (Ronan Collobert)
Copyright (c) 2012-2014 Deepmind Technologies    (Koray Kavukcuoglu)
Copyright (c) 2011-2012 NEC Laboratories America (Koray Kavukcuoglu)
Copyright (c) 2011-2013 NYU                      (Clement Farabet)
Copyright (c) 2006-2010 NEC Laboratories America (Ronan Collobert, Leon Bottou, Iain Melvin, Jason Weston)
Copyright (c) 2006      Idiap Research Institute (Samy Bengio)
Copyright (c) 2001-2004 Idiap Research Institute (Ronan Collobert, Samy Bengio, Johnny Mariethoz)

Licensed under the BSD 3-Clause License.
        </pre>
        
        <h4 style='color: #98c379;'>NumPy</h4>
        <p>
        Copyright (c) 2005-2023, NumPy Developers.<br>
        Licensed under the BSD 3-Clause License.
        </p>
        
        <h4 style='color: #98c379;'>Matplotlib</h4>
        <p>
        Matplotlib is licensed under the PSF (Python Software Foundation) License.
        </p>
        """
