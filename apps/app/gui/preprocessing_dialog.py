"""
Preprocessing settings dialog
预处理设置对话框
"""
import logging
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                            QSpinBox, QDoubleSpinBox, QCheckBox, QPushButton,
                            QGroupBox)
from PyQt6.QtCore import Qt, QSize
from .preview_widget import PreviewWidget
from ..utils.image_preprocessing import PreprocessingConfig

logger = logging.getLogger(__name__)

class PreprocessingDialog(QDialog):
    """Dialog for configuring preprocessing parameters"""
    
    def __init__(self, parent=None, image=None):
        super().__init__(parent)
        self.image = image
        self.config = PreprocessingConfig()
        self.setup_ui()
        
    def setup_ui(self):
        """Setup user interface"""
        self.setWindowTitle("图像预处理设置")
        self.setMinimumWidth(800)
        
        # Create layout
        layout = QHBoxLayout(self)
        
        # Left side: settings
        settings_layout = QVBoxLayout()
        
        # Glare removal
        glare_group = QGroupBox("光晕去除")
        glare_layout = QVBoxLayout()
        self.remove_glare_cb = QCheckBox("启用光晕去除")
        self.remove_glare_cb.setChecked(self.config.remove_glare)
        self.remove_glare_cb.stateChanged.connect(self.on_param_changed)
        glare_layout.addWidget(self.remove_glare_cb)
        
        thresh_layout = QHBoxLayout()
        thresh_layout.addWidget(QLabel("阈值:"))
        self.glare_threshold_sb = QSpinBox()
        self.glare_threshold_sb.setRange(0, 255)
        self.glare_threshold_sb.setValue(self.config.glare_threshold)
        self.glare_threshold_sb.valueChanged.connect(self.on_param_changed)
        thresh_layout.addWidget(self.glare_threshold_sb)
        glare_layout.addLayout(thresh_layout)
        glare_group.setLayout(glare_layout)
        settings_layout.addWidget(glare_group)
        
        # Normalization
        norm_group = QGroupBox("亮度归一化")
        norm_layout = QVBoxLayout()
        self.normalize_cb = QCheckBox("启用归一化")
        self.normalize_cb.setChecked(self.config.normalize)
        self.normalize_cb.stateChanged.connect(self.on_param_changed)
        norm_layout.addWidget(self.normalize_cb)
        norm_group.setLayout(norm_layout)
        settings_layout.addWidget(norm_group)
        
        # CLAHE
        clahe_group = QGroupBox("对比度增强 (CLAHE)")
        clahe_layout = QVBoxLayout()
        self.clahe_cb = QCheckBox("启用CLAHE")
        self.clahe_cb.setChecked(self.config.clahe)
        self.clahe_cb.stateChanged.connect(self.on_param_changed)
        clahe_layout.addWidget(self.clahe_cb)
        
        clip_layout = QHBoxLayout()
        clip_layout.addWidget(QLabel("对比度限制:"))
        self.clahe_clip_sb = QDoubleSpinBox()
        self.clahe_clip_sb.setRange(0.1, 10.0)
        self.clahe_clip_sb.setSingleStep(0.1)
        self.clahe_clip_sb.setValue(self.config.clahe_clip)
        self.clahe_clip_sb.valueChanged.connect(self.on_param_changed)
        clip_layout.addWidget(self.clahe_clip_sb)
        clahe_layout.addLayout(clip_layout)
        
        grid_layout = QHBoxLayout()
        grid_layout.addWidget(QLabel("网格大小:"))
        self.clahe_grid_sb = QSpinBox()
        self.clahe_grid_sb.setRange(2, 16)
        self.clahe_grid_sb.setValue(self.config.clahe_grid)
        self.clahe_grid_sb.valueChanged.connect(self.on_param_changed)
        grid_layout.addWidget(self.clahe_grid_sb)
        clahe_layout.addLayout(grid_layout)
        clahe_group.setLayout(clahe_layout)
        settings_layout.addWidget(clahe_group)
        
        # Gaussian blur
        blur_group = QGroupBox("高斯模糊")
        blur_layout = QVBoxLayout()
        self.blur_cb = QCheckBox("启用高斯模糊")
        self.blur_cb.setChecked(self.config.gaussian_blur)
        self.blur_cb.stateChanged.connect(self.on_param_changed)
        blur_layout.addWidget(self.blur_cb)
        
        kernel_layout = QHBoxLayout()
        kernel_layout.addWidget(QLabel("核大小:"))
        self.blur_kernel_sb = QSpinBox()
        self.blur_kernel_sb.setRange(3, 31)
        self.blur_kernel_sb.setSingleStep(2)
        self.blur_kernel_sb.setValue(self.config.blur_kernel)
        self.blur_kernel_sb.valueChanged.connect(self.on_param_changed)
        kernel_layout.addWidget(self.blur_kernel_sb)
        blur_layout.addLayout(kernel_layout)
        blur_group.setLayout(blur_layout)
        settings_layout.addWidget(blur_group)
        
        # Adaptive threshold
        thresh_group = QGroupBox("自适应阈值")
        thresh_layout = QVBoxLayout()
        self.threshold_cb = QCheckBox("启用自适应阈值")
        self.threshold_cb.setChecked(self.config.adaptive_threshold)
        self.threshold_cb.stateChanged.connect(self.on_param_changed)
        thresh_layout.addWidget(self.threshold_cb)
        
        block_layout = QHBoxLayout()
        block_layout.addWidget(QLabel("块大小:"))
        self.block_size_sb = QSpinBox()
        self.block_size_sb.setRange(3, 99)
        self.block_size_sb.setSingleStep(2)
        self.block_size_sb.setValue(self.config.block_size)
        self.block_size_sb.valueChanged.connect(self.on_param_changed)
        block_layout.addWidget(self.block_size_sb)
        thresh_layout.addLayout(block_layout)
        
        c_layout = QHBoxLayout()
        c_layout.addWidget(QLabel("C值:"))
        self.c_value_sb = QSpinBox()
        self.c_value_sb.setRange(-10, 10)
        self.c_value_sb.setValue(self.config.c_value)
        self.c_value_sb.valueChanged.connect(self.on_param_changed)
        c_layout.addWidget(self.c_value_sb)
        thresh_layout.addLayout(c_layout)
        thresh_group.setLayout(thresh_layout)
        settings_layout.addWidget(thresh_group)
        
        # Add stretch to keep controls at top
        settings_layout.addStretch()
        
        # Buttons
        button_layout = QHBoxLayout()
        ok_btn = QPushButton("确定")
        ok_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(ok_btn)
        button_layout.addWidget(cancel_btn)
        settings_layout.addLayout(button_layout)
        
        # Add settings to main layout
        layout.addLayout(settings_layout)
        
        # Right side: preview
        self.preview = PreviewWidget()
        if self.image is not None:
            self.preview.set_image(self.image)
            self.preview.set_config(self.config)
        layout.addWidget(self.preview)
        
    def on_param_changed(self):
        """Handle parameter change"""
        try:
            # Update config from controls
            self.config.remove_glare = self.remove_glare_cb.isChecked()
            self.config.glare_threshold = self.glare_threshold_sb.value()
            
            self.config.normalize = self.normalize_cb.isChecked()
            
            self.config.clahe = self.clahe_cb.isChecked()
            self.config.clahe_clip = self.clahe_clip_sb.value()
            self.config.clahe_grid = self.clahe_grid_sb.value()
            
            self.config.gaussian_blur = self.blur_cb.isChecked()
            self.config.blur_kernel = self.blur_kernel_sb.value()
            
            self.config.adaptive_threshold = self.threshold_cb.isChecked()
            self.config.block_size = self.block_size_sb.value()
            self.config.c_value = self.c_value_sb.value()
            
            # Update preview
            if self.image is not None:
                self.preview.set_config(self.config)
                
        except Exception as e:
            logger.error(f"Error updating parameters: {str(e)}")
            
    def load_config(self, config):
        """Load configuration into dialog
        
        Args:
            config: PreprocessingConfig object or dict
        """
        try:
            if isinstance(config, dict):
                config = PreprocessingConfig.from_dict(config)
                
            # Update controls
            self.remove_glare_cb.setChecked(config.remove_glare)
            self.glare_threshold_sb.setValue(config.glare_threshold)
            
            self.normalize_cb.setChecked(config.normalize)
            
            self.clahe_cb.setChecked(config.clahe)
            self.clahe_clip_sb.setValue(config.clahe_clip)
            self.clahe_grid_sb.setValue(config.clahe_grid)
            
            self.blur_cb.setChecked(config.gaussian_blur)
            self.blur_kernel_sb.setValue(config.blur_kernel)
            
            self.threshold_cb.setChecked(config.adaptive_threshold)
            self.block_size_sb.setValue(config.block_size)
            self.c_value_sb.setValue(config.c_value)
            
            # Update config and preview
            self.config = config
            if self.image is not None:
                self.preview.set_config(config)
                
        except Exception as e:
            logger.error(f"Error loading configuration: {str(e)}")
            
    def get_config(self):
        """Get current configuration
        
        Returns:
            Current PreprocessingConfig object
        """
        return self.config
