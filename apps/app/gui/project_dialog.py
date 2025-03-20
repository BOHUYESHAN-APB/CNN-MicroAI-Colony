"""
Project dialog implementation
项目对话框实现
"""
import os
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                            QLineEdit, QPushButton, QFileDialog, QMessageBox)
from PyQt6.QtCore import Qt
from ..utils.i18n import translate

class ProjectDialog(QDialog):
    """Dialog for creating or opening projects"""
    
    # Class-level translation function
    _ = staticmethod(translate)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
        # State
        self.project_path = None
        
    def setup_ui(self):
        """Setup user interface"""
        self.setWindowTitle(self._("项目"))
        self.setMinimumWidth(500)
        self.setModal(True)
        
        # Layout
        layout = QVBoxLayout(self)
        
        # Project path
        path_layout = QHBoxLayout()
        
        path_label = QLabel(self._("项目路径:"))
        path_layout.addWidget(path_label)
        
        self.path_edit = QLineEdit()
        self.path_edit.setReadOnly(True)
        self.path_edit.setPlaceholderText(self._("选择或创建项目文件夹..."))
        path_layout.addWidget(self.path_edit)
        
        browse_btn = QPushButton(self._("浏览..."))
        browse_btn.clicked.connect(self.browse_path)
        path_layout.addWidget(browse_btn)
        
        layout.addLayout(path_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.cancel_btn = QPushButton(self._("取消"))
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        self.ok_btn = QPushButton(self._("确定"))
        self.ok_btn.clicked.connect(self.accept)
        self.ok_btn.setEnabled(False)
        button_layout.addWidget(self.ok_btn)
        
        layout.addLayout(button_layout)
        
        # Style
        self.setStyleSheet("""
            QDialog {
                background-color: #1e1e1e;
                color: #e0e0e0;
            }
            QLabel {
                color: #e0e0e0;
            }
            QLineEdit {
                background-color: #2d2d2d;
                color: #e0e0e0;
                border: 1px solid #3d3d3d;
                padding: 5px;
                border-radius: 4px;
            }
            QLineEdit:disabled {
                background-color: #252525;
                color: #808080;
            }
            QPushButton {
                background-color: #424242;
                color: #e0e0e0;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #505050;
            }
            QPushButton:pressed {
                background-color: #616161;
            }
            QPushButton:disabled {
                background-color: #2d2d2d;
                color: #808080;
            }
        """)
        
    def browse_path(self):
        """Browse for project path"""
        path = QFileDialog.getExistingDirectory(
            self,
            self._("选择项目文件夹"),
            "",
            QFileDialog.Option.ShowDirsOnly
        )
        
        if path:
            # Check if it's a valid project folder
            if self.validate_project_path(path):
                self.project_path = path
                self.path_edit.setText(path)
                self.ok_btn.setEnabled(True)
            else:
                # Ask if want to create new project
                reply = QMessageBox.question(
                    self,
                    self._("新建项目"),
                    self._("该文件夹不是有效的项目。是否要在此创建新项目？"),
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                
                if reply == QMessageBox.StandardButton.Yes:
                    if self.create_project(path):
                        self.project_path = path
                        self.path_edit.setText(path)
                        self.ok_btn.setEnabled(True)
                    else:
                        QMessageBox.critical(
                            self,
                            self._("错误"),
                            self._("创建项目失败。")
                        )
                        
    def validate_project_path(self, path):
        """Check if path is a valid project folder"""
        # Check for project.json
        project_file = os.path.join(path, "project.json")
        if not os.path.exists(project_file):
            return False
            
        return True
        
    def create_project(self, path):
        """Create new project at path"""
        try:
            # Create project structure
            os.makedirs(os.path.join(path, "images"), exist_ok=True)
            os.makedirs(os.path.join(path, "results"), exist_ok=True)
            
            # Create project file
            project_file = os.path.join(path, "project.json")
            with open(project_file, "w", encoding="utf-8") as f:
                f.write("{}")
                
            return True
            
        except Exception as e:
            print(f"Failed to create project: {e}")
            return False
            
    def get_project_path(self):
        """Get selected project path"""
        return self.project_path
