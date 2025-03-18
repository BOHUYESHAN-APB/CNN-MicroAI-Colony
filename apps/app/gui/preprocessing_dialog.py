"""
Dialog for configuring image preprocessing settings
"""
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
                           QCheckBox, QSpinBox, QDoubleSpinBox, QPushButton,
                           QGroupBox, QComboBox, QLabel)
from PyQt6.QtCore import Qt

DIALOG_STYLE = """
QDialog {
    background-color: #2b2b2b;
    color: #e0e0e0;
}
QGroupBox {
    color: #e0e0e0;
    border: 1px solid #3a3a3a;
    border-radius: 4px;
    margin-top: 12px;
    padding-top: 12px;
}
QGroupBox::title {
    color: #e0e0e0;
    padding: 0 3px;
}
QLabel {
    color: #e0e0e0;
}
QComboBox, QSpinBox, QDoubleSpinBox {
    background-color: #3a3a3a;
    color: #e0e0e0;
    border: 1px solid #505050;
    border-radius: 4px;
    padding: 3px;
}
QCheckBox {
    color: #e0e0e0;
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
QPushButton:pressed {
    background-color: #303030;
}
"""

class PreprocessingDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("图像预处理设置")
        self.setMinimumWidth(400)
        self.setStyleSheet(DIALOG_STYLE)
        self.setup_ui()

    def setup_ui(self):
        """Setup dialog UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Mode selection
        mode_group = QGroupBox("处理模式", self)
        mode_layout = QVBoxLayout()
        
        # Add mode description labels
        mode_descriptions = {
            "默认参数": "使用标准参数进行基础预处理",
            "自定义参数": "手动配置预处理步骤和参数",
            "自动优化": "根据图像特征自动调整参数"
        }
        
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(list(mode_descriptions.keys()))
        self.mode_combo.currentIndexChanged.connect(self.on_mode_changed)
        mode_layout.addWidget(self.mode_combo)
        
        # Description label
        self.desc_label = QLabel()
        self.desc_label.setWordWrap(True)
        self.desc_label.setStyleSheet("color: #909090; font-size: 11px;")
        mode_layout.addWidget(self.desc_label)
        
        mode_group.setLayout(mode_layout)
        layout.addWidget(mode_group)
        
        # Settings group
        settings_group = QGroupBox("处理步骤")
        settings_layout = QFormLayout()
        settings_layout.setSpacing(8)
        
        # Enable controls with descriptions
        self.remove_glare_check = QCheckBox("启用")
        self.normalize_check = QCheckBox("启用")
        self.clahe_check = QCheckBox("启用")
        self.blur_check = QCheckBox("启用")
        self.threshold_check = QCheckBox("启用")
        
        # Parameter controls with tooltips
        self.glare_threshold = QSpinBox()
        self.glare_threshold.setRange(100, 255)
        self.glare_threshold.setValue(220)
        self.glare_threshold.setToolTip("调整光晕检测的亮度阈值")
        
        self.clahe_clip = QDoubleSpinBox()
        self.clahe_clip.setRange(0.5, 10.0)
        self.clahe_clip.setValue(2.0)
        self.clahe_clip.setSingleStep(0.5)
        self.clahe_clip.setToolTip("限制对比度增强的强度")
        
        self.clahe_grid = QSpinBox()
        self.clahe_grid.setRange(2, 32)
        self.clahe_grid.setValue(8)
        self.clahe_grid.setToolTip("调整对比度增强的网格大小")
        
        self.blur_kernel = QSpinBox()
        self.blur_kernel.setRange(3, 15)
        self.blur_kernel.setValue(5)
        self.blur_kernel.setSingleStep(2)
        self.blur_kernel.setToolTip("调整模糊处理的强度")
        
        # Add to layout with descriptions
        settings_layout.addRow("去除光晕:", self.remove_glare_check)
        settings_layout.addRow("光晕阈值:", self.glare_threshold)
        
        settings_layout.addRow("光照归一化:", self.normalize_check)
        
        settings_layout.addRow("CLAHE增强:", self.clahe_check)
        settings_layout.addRow("对比度限制:", self.clahe_clip)
        settings_layout.addRow("网格大小:", self.clahe_grid)
        
        settings_layout.addRow("高斯模糊:", self.blur_check)
        settings_layout.addRow("核大小:", self.blur_kernel)
        
        settings_layout.addRow("自适应阈值:", self.threshold_check)
        
        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        ok_button = QPushButton("确定")
        ok_button.setDefault(True)
        ok_button.clicked.connect(self.accept)
        cancel_button = QPushButton("取消")
        cancel_button.clicked.connect(self.reject)
        button_layout.addStretch()
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)
        
        # Set default state
        self.set_default_values()
        self.on_mode_changed(0)  # Update description
        
    def set_default_values(self):
        """Set default values for controls"""
        self.remove_glare_check.setChecked(True)
        self.normalize_check.setChecked(True)
        self.clahe_check.setChecked(True)
        self.blur_check.setChecked(False)
        self.threshold_check.setChecked(False)
        self.on_mode_changed(0)  # Default mode
        
    def on_mode_changed(self, index):
        """Handle mode selection change"""
        is_manual = index == 1  # Manual mode
        
        # Update description
        descriptions = [
            "使用标准参数进行基础预处理",
            "手动配置预处理步骤和参数",
            "根据图像特征自动调整参数"
        ]
        self.desc_label.setText(descriptions[index])
        
        # Enable/disable parameter controls
        for widget in [self.remove_glare_check, self.normalize_check,
                      self.clahe_check, self.blur_check, self.threshold_check,
                      self.glare_threshold, self.clahe_clip, self.clahe_grid,
                      self.blur_kernel]:
            widget.setEnabled(is_manual)

    def load_config(self, config):
        """Load configuration into dialog"""
        if config.get('auto_optimize', False):
            self.mode_combo.setCurrentIndex(2)  # Auto mode
        elif config:
            self.mode_combo.setCurrentIndex(1)  # Manual mode
            
            # Load enabled states
            self.remove_glare_check.setChecked(config.get('remove_glare', True))
            self.normalize_check.setChecked(config.get('normalize_lighting', True))
            self.clahe_check.setChecked(config.get('clahe', True))
            self.blur_check.setChecked(config.get('gaussian_blur', False))
            self.threshold_check.setChecked(config.get('adaptive_thresholding', False))
            
            # Load parameters
            self.glare_threshold.setValue(config.get('glare_threshold', 220))
            self.clahe_clip.setValue(config.get('clahe_clip_limit', 2.0))
            self.clahe_grid.setValue(config.get('clahe_grid_size', 8))
            self.blur_kernel.setValue(config.get('blur_kernel_size', 5))
        else:
            self.mode_combo.setCurrentIndex(0)  # Default mode

    def get_config(self):
        """Get current configuration"""
        mode = self.mode_combo.currentIndex()
        
        if mode == 0:  # Default mode
            return None
        elif mode == 2:  # Auto mode
            return {'auto_optimize': True}
            
        # Manual mode
        return {
            'remove_glare': self.remove_glare_check.isChecked(),
            'normalize_lighting': self.normalize_check.isChecked(),
            'clahe': self.clahe_check.isChecked(),
            'gaussian_blur': self.blur_check.isChecked(),
            'adaptive_thresholding': self.threshold_check.isChecked(),
            'glare_threshold': self.glare_threshold.value(),
            'clahe_clip_limit': self.clahe_clip.value(),
            'clahe_grid_size': self.clahe_grid.value(),
            'blur_kernel_size': self.blur_kernel.value(),
        }
