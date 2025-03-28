"""
Settings dialog implementation
设置对话框实现
"""
import os
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                            QLabel, QLineEdit, QFileDialog, QGroupBox)
from PyQt6.QtCore import Qt
from ..utils.i18n import translate

class SettingsDialog(QDialog):
    """Application settings dialog"""
    def __init__(self, parent=None, config=None):
        super().__init__(parent)
        self.config = config
        self._ = translate
        self.setup_ui()
        
    def setup_ui(self):
        """Setup user interface"""
        self.setWindowTitle(self._("设置"))
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout()
        
        # Model settings group
        model_group = QGroupBox(self._("模型设置"))
        model_layout = QVBoxLayout()
        
        # Model path
        model_path_layout = QHBoxLayout()
        model_path_layout.addWidget(QLabel(self._("模型路径:")))
        
        self.model_path_edit = QLineEdit()
        if self.config and self.config.model_path:
            self.model_path_edit.setText(self.config.model_path)
        model_path_layout.addWidget(self.model_path_edit)
        
        browse_btn = QPushButton(self._("浏览..."))
        browse_btn.clicked.connect(self.browse_model_path)
        model_path_layout.addWidget(browse_btn)
        
        model_layout.addLayout(model_path_layout)
        model_group.setLayout(model_layout)
        layout.addWidget(model_group)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        ok_btn = QPushButton(self._("确定"))
        ok_btn.clicked.connect(self.accept)
        btn_layout.addWidget(ok_btn)
        
        cancel_btn = QPushButton(self._("取消"))
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        layout.addLayout(btn_layout)
        self.setLayout(layout)
        
    def browse_model_path(self):
        """Browse for model file"""
        path, _ = QFileDialog.getOpenFileName(
            self,
            self._("选择模型文件"),
            "",
            "Model Files (*.pth *.pt *.onnx)"
        )
        if path:
            self.model_path_edit.setText(path)
            
    def get_settings(self):
        """Get current settings"""
        return {
            'model_path': self.model_path_edit.text() or None
        }
