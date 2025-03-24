"""
Image optimization widget implementation
图像优化控件实现
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                            QLabel, QCheckBox, QGroupBox)
from PyQt6.QtCore import pyqtSignal

from .slider_with_value import SliderWithValue
from ..utils.image_processing_steps import (auto_optimize, default_optimize,
                                          denoise, sharpen, color_balance)

class Optimizationwidget(QWidget):  # 类名改为 Optimizationwidget (全部小写)
    """Image optimization widget"""
    
    # Signal emitted when settings change
    settingsChanged = pyqtSignal()
    
    def __init__(self, parent=None):
        """Initialize widget"""
        super().__init__(parent)
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup UI elements"""
        layout = QVBoxLayout(self)
        
        # Optimization mode
        mode_group = QGroupBox("优化模式")
        mode_layout = QVBoxLayout()
        
        # Default mode button
        default_btn = QPushButton("默认优化")
        default_btn.clicked.connect(self.apply_default)
        mode_layout.addWidget(default_btn)
        
        # Auto mode button
        auto_btn = QPushButton("自动优化")
        auto_btn.clicked.connect(self.apply_auto)
        mode_layout.addWidget(auto_btn)
        
        mode_group.setLayout(mode_layout)
        layout.addWidget(mode_group)
        
        # Manual adjustments
        manual_group = QGroupBox("手动调整")
        manual_layout = QVBoxLayout()
        
        # Denoise
        self.denoise_check = QCheckBox("降噪")
        self.denoise_check.stateChanged.connect(self.settingsChanged)
        manual_layout.addWidget(self.denoise_check)
        
        self.denoise_strength = SliderWithValue(1, 30, step=1)
        self.denoise_strength.valueChanged.connect(self.settingsChanged)
        self.denoise_strength.setValue(10)
        manual_layout.addWidget(self.denoise_strength)
        
        # Sharpness
        self.sharpen_check = QCheckBox("锐化")
        self.sharpen_check.stateChanged.connect(self.settingsChanged)
        manual_layout.addWidget(self.sharpen_check)
        
        self.sharpen_amount = SliderWithValue(0.1, 2.0, decimal=True, step=0.1)
        self.sharpen_amount.valueChanged.connect(self.settingsChanged)
        self.sharpen_amount.setValue(1.0)
        manual_layout.addWidget(self.sharpen_amount)
        
        # Color balance
        self.color_balance_check = QCheckBox("色彩平衡")
        self.color_balance_check.stateChanged.connect(self.settingsChanged)
        manual_layout.addWidget(self.color_balance_check)
        
        manual_group.setLayout(manual_layout)
        layout.addWidget(manual_group)
        
        layout.addStretch()
        
    def apply_default(self):
        """Apply default optimization"""
        self.denoise_check.setChecked(True)
        self.denoise_strength.setValue(3)
        self.sharpen_check.setChecked(False)
        self.color_balance_check.setChecked(False)
        self.settingsChanged.emit()
        
    def apply_auto(self):
        """Apply auto optimization"""
        self.denoise_check.setChecked(True)
        self.denoise_strength.setValue(5)
        self.sharpen_check.setChecked(True)
        self.sharpen_amount.setValue(0.5)
        self.color_balance_check.setChecked(True)
        self.settingsChanged.emit()
        
    def process_image(self, image):
        """Process image with current settings
        
        Args:
            image: Input image (numpy array)
            
        Returns:
            Processed image
        """
        if self.denoise_check.isChecked():
            image = denoise(image, self.denoise_strength.value())
            
        if self.sharpen_check.isChecked():
            image = sharpen(image, self.sharpen_amount.value())
            
        if self.color_balance_check.isChecked():
            image = color_balance(image)
            
        return image
