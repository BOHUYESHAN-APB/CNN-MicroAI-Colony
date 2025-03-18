"""
Project dialog implementations
项目对话框实现
"""
import os
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                           QLineEdit, QPushButton, QFileDialog)

DIALOG_STYLE = """
QDialog {
    background-color: #2b2b2b;
    color: #e0e0e0;
}
QLabel {
    color: #e0e0e0;
}
QLineEdit {
    background-color: #3a3a3a;
    color: #e0e0e0;
    border: 1px solid #505050;
    border-radius: 4px;
    padding: 5px;
}
QPushButton {
    background-color: #3a3a3a;
    color: #e0e0e0;
    border: 1px solid #505050;
    border-radius: 4px;
    padding: 5px 15px;
    min-width: 80px;
}
QPushButton:hover {
    background-color: #454545;
}
"""

class NewProjectDialog(QDialog):
    """Dialog for creating new project"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("新建项目")
        self.setStyleSheet(DIALOG_STYLE)
        self.setup_ui()
        
    def setup_ui(self):
        """Setup dialog UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Description
        desc = QLabel("选择一个文件夹作为图像处理项目。\n这个文件夹将用于存储图像和分析结果。")
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #909090; font-size: 11px; padding: 5px;")
        layout.addWidget(desc)
        
        # Project name
        name_layout = QHBoxLayout()
        name_label = QLabel("项目名称:")
        self.name_edit = QLineEdit()
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.name_edit)
        layout.addLayout(name_layout)
        
        # Project path
        path_layout = QHBoxLayout()
        path_label = QLabel("项目路径:")
        self.path_edit = QLineEdit()
        browse_btn = QPushButton("浏览...")
        browse_btn.clicked.connect(self.browse_path)
        path_layout.addWidget(path_label)
        path_layout.addWidget(self.path_edit)
        path_layout.addWidget(browse_btn)
        layout.addLayout(path_layout)
        
        # Buttons
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("确定")
        ok_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
        
    def browse_path(self):
        """Browse for project path"""
        path = QFileDialog.getExistingDirectory(
            self,
            "选择项目路径",
            os.path.expanduser("~")
        )
        if path:
            self.path_edit.setText(path)
            # 如果没有设置名称，使用文件夹名作为项目名
            if not self.name_edit.text():
                self.name_edit.setText(os.path.basename(path))
            
    def get_project_info(self):
        """Get project information"""
        return (
            self.name_edit.text(),
            self.path_edit.text()
        )

class OpenProjectDialog(QDialog):
    """Dialog for opening existing project"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("打开项目")
        self.setStyleSheet(DIALOG_STYLE)
        self.setup_ui()
        
    def setup_ui(self):
        """Setup dialog UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Description
        desc = QLabel("选择包含图像的文件夹。\n将自动导入所有支持的图像文件。")
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #909090; font-size: 11px; padding: 5px;")
        layout.addWidget(desc)
        
        # Project path
        path_layout = QHBoxLayout()
        path_label = QLabel("项目文件夹:")
        self.path_edit = QLineEdit()
        browse_btn = QPushButton("浏览...")
        browse_btn.clicked.connect(self.browse_path)
        path_layout.addWidget(path_label)
        path_layout.addWidget(self.path_edit)
        path_layout.addWidget(browse_btn)
        layout.addLayout(path_layout)
        
        # Buttons
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("确定")
        ok_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
        
    def browse_path(self):
        """Browse for project path"""
        path = QFileDialog.getExistingDirectory(
            self,
            "选择项目文件夹",
            os.path.expanduser("~")
        )
        if path:
            self.path_edit.setText(path)
            
    def get_project_path(self):
        """Get project path"""
        return self.path_edit.text()
