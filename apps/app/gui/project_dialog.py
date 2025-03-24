"""
Project dialog implementation
项目对话框实现
"""
import os
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                            QLabel, QLineEdit, QFileDialog, QMessageBox)
from PyQt6.QtCore import Qt

class ProjectDialog(QDialog):
    """Project selection/creation dialog"""
    
    def __init__(self, parent=None, new_project=False):
        """Initialize dialog
        
        Args:
            parent: Parent widget
            new_project: Whether this is for new project
        """
        super().__init__(parent)
        
        self.new_project = new_project
        self.project_dir = None
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup UI elements"""
        # Set title and size
        title = "新建项目" if self.new_project else "打开项目"
        self.setWindowTitle(title)
        self.resize(500, 150)
        
        # Create layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)
        
        # Project directory selection
        dir_layout = QHBoxLayout()
        
        self.dir_label = QLabel("项目位置:")
        self.dir_edit = QLineEdit()
        self.dir_edit.setReadOnly(True)
        self.browse_btn = QPushButton("浏览...")
        self.browse_btn.clicked.connect(self._browse_dir)
        
        dir_layout.addWidget(self.dir_label)
        dir_layout.addWidget(self.dir_edit, stretch=1)
        dir_layout.addWidget(self.browse_btn)
        
        layout.addLayout(dir_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.ok_btn = QPushButton("确定")
        self.ok_btn.setDefault(True)
        self.ok_btn.clicked.connect(self.accept)
        
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(self.ok_btn)
        button_layout.addWidget(self.cancel_btn)
        
        layout.addStretch()
        layout.addLayout(button_layout)
        
    def _browse_dir(self):
        """Show directory selection dialog"""
        if self.new_project:
            project_dir = QFileDialog.getExistingDirectory(
                self,
                "选择新项目位置"
            )
        else:
            project_dir = QFileDialog.getExistingDirectory(
                self,
                "选择项目文件夹"
            )
            
        if project_dir:
            self.dir_edit.setText(project_dir)
            self.project_dir = project_dir
            
    def get_project_dir(self):
        """Get selected project directory
        
        Returns:
            Selected directory path or None if cancelled
        """
        return self.project_dir
