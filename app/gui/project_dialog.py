"""
Project Dialog
"""
import os
import logging
from pathlib import Path
from typing import Optional, Tuple

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                            QLineEdit, QPushButton, QFileDialog, QMessageBox)
from PyQt6.QtCore import Qt

from ..utils.i18n import tr
from ..utils.path_manager import (get_projects_dir, normalize_path,
                               clean_project_name, is_valid_project_dir)

logger = logging.getLogger(__name__)

class NewProjectDialog(QDialog):
    """Project creation dialog"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.result_path = ""
        self.result_name = ""
        self.setup_ui()
        
    def setup_ui(self):
        """Setup user interface"""
        self.setWindowTitle(tr("project.new.title"))
        self.setMinimumWidth(400)
        self.setModal(True)
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Project name
        name_layout = QHBoxLayout()
        name_label = QLabel(tr("project.new.name"))
        name_layout.addWidget(name_label)
        
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText(tr("project.new.name_placeholder"))
        name_layout.addWidget(self.name_edit)
        
        layout.addLayout(name_layout)
        
        # Project location
        path_layout = QHBoxLayout()
        path_label = QLabel(tr("project.new.location"))
        path_layout.addWidget(path_label)
        
        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText(tr("project.new.location_placeholder"))
        self.path_edit.setText(get_projects_dir())
        path_layout.addWidget(self.path_edit)
        
        browse_btn = QPushButton(tr("project.new.browse"))
        browse_btn.clicked.connect(self.browse_location)
        path_layout.addWidget(browse_btn)
        
        layout.addLayout(path_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.create_btn = QPushButton(tr("project.new.create"))
        self.create_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.create_btn)
        
        cancel_btn = QPushButton(tr("dialog.cancel"))
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
        # Set default button
        self.create_btn.setDefault(True)
        
    def browse_location(self):
        """Show directory selection dialog"""
        path = QFileDialog.getExistingDirectory(
            self,
            tr("project.new.select_location"),
            self.path_edit.text()
        )
        
        if path:
            self.path_edit.setText(normalize_path(path))
            
    def get_project_info(self) -> Tuple[str, str]:
        """Get project name and path
        Returns tuple (name, path)"""
        return (self.result_name, self.result_path)
        
    def validate(self) -> bool:
        """Validate dialog inputs"""
        # Get values
        name = self.name_edit.text().strip()
        path = self.path_edit.text().strip()
        
        # Validate name
        if not name:
            QMessageBox.warning(
                self,
                tr("dialog.warning"),
                tr("project.new.error.name_empty")
            )
            self.name_edit.setFocus()
            return False
            
        # Clean and validate name
        cleaned_name = clean_project_name(name)
        if cleaned_name != name:
            reply = QMessageBox.question(
                self,
                tr("dialog.warning"),
                tr("project.new.name_changed").format(
                    original=name,
                    cleaned=cleaned_name
                ),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.No:
                self.name_edit.setFocus()
                return False
                
            name = cleaned_name
            self.name_edit.setText(name)
            
        # Validate path
        if not path:
            QMessageBox.warning(
                self,
                tr("dialog.warning"),
                tr("project.new.error.path_empty")
            )
            self.path_edit.setFocus()
            return False
            
        # Check if path exists
        path = normalize_path(path)
        if not os.path.exists(path):
            reply = QMessageBox.question(
                self,
                tr("dialog.warning"),
                tr("project.new.create_path"),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.No:
                self.path_edit.setFocus()
                return False
                
            try:
                os.makedirs(path)
            except Exception as e:
                QMessageBox.critical(
                    self,
                    tr("dialog.error"),
                    tr("project.new.error.create_path").format(error=str(e))
                )
                self.path_edit.setFocus()
                return False
                
        # Check if path is writable
        try:
            test_file = os.path.join(path, ".write_test")
            with open(test_file, 'w') as f:
                f.write("test")
            os.remove(test_file)
        except Exception as e:
            QMessageBox.critical(
                self,
                tr("dialog.error"),
                tr("project.new.error.not_writable").format(error=str(e))
            )
            self.path_edit.setFocus()
            return False
            
        # Check for existing project
        project_dir = os.path.join(path, name)
        if os.path.exists(project_dir):
            if is_valid_project_dir(project_dir):
                QMessageBox.critical(
                    self,
                    tr("dialog.error"),
                    tr("project.new.error.exists")
                )
            else:
                QMessageBox.critical(
                    self,
                    tr("dialog.error"),
                    tr("project.new.error.path_exists")
                )
            return False
            
        # Store results
        self.result_name = name
        self.result_path = path
        
        return True
        
    def accept(self):
        """Handle dialog acceptance"""
        if self.validate():
            super().accept()

class OpenProjectDialog(QDialog):
    """Project opening dialog"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.result_path = ""
        self.setup_ui()
        
    def setup_ui(self):
        """Setup user interface"""
        self.setWindowTitle(tr("project.open.title"))
        self.setMinimumWidth(400)
        self.setModal(True)
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Project location
        path_layout = QHBoxLayout()
        path_label = QLabel(tr("project.open.location"))
        path_layout.addWidget(path_label)
        
        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText(tr("project.open.location_placeholder"))
        path_layout.addWidget(self.path_edit)
        
        browse_btn = QPushButton(tr("project.open.browse"))
        browse_btn.clicked.connect(self.browse_location)
        path_layout.addWidget(browse_btn)
        
        layout.addLayout(path_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.open_btn = QPushButton(tr("project.open.open"))
        self.open_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.open_btn)
        
        cancel_btn = QPushButton(tr("dialog.cancel"))
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
        # Set default button
        self.open_btn.setDefault(True)
        
    def browse_location(self):
        """Show directory selection dialog"""
        path = QFileDialog.getExistingDirectory(
            self,
            tr("project.open.select_location"),
            get_projects_dir()
        )
        
        if path:
            self.path_edit.setText(normalize_path(path))
            
    def get_project_path(self) -> str:
        """Get selected project path"""
        return self.result_path
        
    def validate(self) -> bool:
        """Validate dialog inputs"""
        # Get values
        path = self.path_edit.text().strip()
        
        # Validate path
        if not path:
            QMessageBox.warning(
                self,
                tr("dialog.warning"),
                tr("project.open.error.path_empty")
            )
            self.path_edit.setFocus()
            return False
            
        # Check if path exists
        path = normalize_path(path)
        if not os.path.exists(path):
            QMessageBox.critical(
                self,
                tr("dialog.error"),
                tr("project.open.error.not_found")
            )
            self.path_edit.setFocus()
            return False
            
        # Validate project
        if not is_valid_project_dir(path):
            QMessageBox.critical(
                self,
                tr("dialog.error"),
                tr("project.open.error.invalid")
            )
            self.path_edit.setFocus()
            return False
            
        # Store result
        self.result_path = path
        
        return True
        
    def accept(self):
        """Handle dialog acceptance"""
        if self.validate():
            super().accept()
