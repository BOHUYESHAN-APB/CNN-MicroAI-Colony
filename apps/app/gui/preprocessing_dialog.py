"""
Preprocessing dialog implementation
预处理对话框实现
"""
import cv2
import numpy as np
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                            QLabel, QTabWidget, QWidget, QScrollArea,
                            QSplitter, QApplication, QToolTip, QSizePolicy) # 显式导入 QSizePolicy
from PyQt6.QtCore import Qt, QSettings
from PyQt6.QtGui import QIcon, QScreen

from .preview_widget import PreviewWidget
from .mask_drawer import MaskDrawer
from .adjustment_widget import AdjustmentWidget
from .advanced_processing_widget import AdvancedProcessingWidget
from .optimizationwidget import Optimizationwidget # 导入 Optimizationwidget (全部小写)

class PreprocessingDialog(QDialog):
    """Image preprocessing configuration dialog"""
    
    def __init__(self, parent=None, image=None):
        """Initialize dialog
        
        Args:
            parent: Parent widget
            image: Input image (numpy array)
        """
        super().__init__(parent)
        
        self.original_image = image
        self.current_image = image.copy() if image is not None else None
        self.result_mask = None
        self.settings = QSettings('MicroAI', 'ColonyCounter')
        
        self.setup_ui()
        self.load_settings()
        self.update_preview()
        
    def setup_ui(self):
        """Setup UI elements"""
        # Set title and size (80% of screen)
        self.setWindowTitle("图像预处理")
        screen = QApplication.primaryScreen().geometry()
        self.resize(int(screen.width() * 0.8), int(screen.height() * 0.8))
        
        # Create layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Create main splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left panel - Parameters
        param_panel = QWidget()
        param_panel.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        param_layout = QVBoxLayout(param_panel)
        param_layout.setContentsMargins(0, 0, 0, 0)
        
        # Add scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        
        # Tab widget
        tab_widget = QTabWidget()
        
        # Advanced processing tab (prioritized)
        self.advanced_widget = AdvancedProcessingWidget()
        self.advanced_widget.settingsChanged.connect(self.update_preview)
        tab_widget.addTab(self.advanced_widget, "高级处理")
        
        # Basic adjustment tab
        self.adjustment_widget = AdjustmentWidget()
        self.adjustment_widget.settingsChanged.connect(self.update_preview)
        tab_widget.addTab(self.adjustment_widget, "基础调整")
        
        # Optimization tab
        self.optimization_widget = Optimizationwidget() # 使用 Optimizationwidget (全部小写)
        self.optimization_widget.settingsChanged.connect(self.update_preview)
        tab_widget.addTab(self.optimization_widget, "优化")
        
        # Add tabs to scroll layout
        scroll_layout.addWidget(tab_widget)
        
        # Quick preset buttons
        preset_layout = QHBoxLayout()
        
        default_btn = QPushButton("默认增强")
        default_btn.setToolTip("应用基本图像增强，适合大多数情况")
        default_btn.clicked.connect(self.apply_default_preset)
        preset_layout.addWidget(default_btn)
        
        auto_btn = QPushButton("自动优化")
        auto_btn.setToolTip("自动分析图像并应用最佳参数")
        auto_btn.clicked.connect(self.apply_auto_preset)
        preset_layout.addWidget(auto_btn)
        
        scroll_layout.addLayout(preset_layout)
        
        # Add buttons
        button_layout = QHBoxLayout()
        
        self.ok_button = QPushButton("确定")
        self.ok_button.clicked.connect(self.accept)
        
        self.cancel_button = QPushButton("取消")
        self.cancel_button.clicked.connect(self.reject)
        self.reset_button = QPushButton("重置")
        self.reset_button.clicked.connect(self.reset_params)
        
        button_layout.addWidget(self.reset_button)
        button_layout.addStretch()
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        
        scroll_layout.addLayout(button_layout)
        scroll_layout.addStretch()
        
        scroll.setWidget(scroll_content)
        param_layout.addWidget(scroll)
        splitter.addWidget(param_panel)
        
        # Right splitter for preview and mask
        right_splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Preview panel
        preview_panel = QWidget()
        preview_panel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        preview_layout = QVBoxLayout(preview_panel)
        preview_layout.setContentsMargins(0, 0, 0, 0)
        
        self.preview = PreviewWidget()
        preview_layout.addWidget(self.preview)
        
        right_splitter.addWidget(preview_panel)
        
        # Mask panel
        mask_panel = QWidget()
        mask_panel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        mask_layout = QVBoxLayout(mask_panel)
        mask_layout.setContentsMargins(0, 0, 0, 0)
        
        mask_label = QLabel("遮罩绘制")
        mask_layout.addWidget(mask_label)
        
        self.mask_drawer = MaskDrawer(self) # Pass self as parent
        self.mask_drawer.mask_updated.connect(self._on_mask_updated)
        mask_layout.addWidget(self.mask_drawer)
        
        right_splitter.addWidget(mask_panel)
        
        # Set stretch factors for right splitter
        right_splitter.setStretchFactor(0, 3)  # Preview takes more space
        right_splitter.setStretchFactor(1, 2)  # Mask drawer takes less space
        
        splitter.addWidget(right_splitter)
        
        # Set stretch factors for main splitter
        splitter.setStretchFactor(0, 0)  # Parameter panel - fixed width
        splitter.setStretchFactor(1, 1)  # Right panel - stretchable
        
        # Set minimum width for parameter panel
        param_panel.setMinimumWidth(350)
        
        layout.addWidget(splitter)
        
    def load_settings(self):
        """Load saved settings"""
        try:
            size = self.settings.value('PreprocessingDialog/size')
            if size:
                self.resize(size)
                
            if self.settings.value('PreprocessingDialog/use_saved_params', False, type=bool):
                # Load advanced processing settings
                self.advanced_widget.edge_type.setCurrentIndex(
                    self.settings.value('PreprocessingDialog/edge_type', 0, type=int))
                self.advanced_widget.morph_type.setCurrentIndex(
                    self.settings.value('PreprocessingDialog/morph_type', 0, type=int))
                self.advanced_widget.filter_type.setCurrentIndex(
                    self.settings.value('PreprocessingDialog/filter_type', 0, type=int))
                
        except Exception as e:
            print(f"Error loading settings: {str(e)}")
            
    def save_settings(self):
        """Save current settings"""
        try:
            self.settings.setValue('PreprocessingDialog/size', self.size())
            self.settings.setValue('PreprocessingDialog/use_saved_params', True)
            
            # Save advanced processing settings
            self.settings.setValue('PreprocessingDialog/edge_type', 
                                 self.advanced_widget.edge_type.currentIndex())
            self.settings.setValue('PreprocessingDialog/morph_type',
                                 self.advanced_widget.morph_type.currentIndex())
            self.settings.setValue('PreprocessingDialog/filter_type',
                                 self.advanced_widget.filter_type.currentIndex())
                                 
        except Exception as e:
            print(f"Error saving settings: {str(e)}")
            
    def closeEvent(self, event):
        """Handle dialog close"""
        self.save_settings()
        super().closeEvent(event)
        
    def update_preview(self):
        """Update preview image with current parameters"""
        if self.current_image is None:
            return
            
        try:
            # Start with original image
            processed = self.original_image.copy()
            
            # Apply advanced processing first
            processed = self.advanced_widget.process_image(processed)
            
            # Apply basic adjustments
            processed = self.adjustment_widget.process_image(processed)
            
            # Apply mask if exists
            if self.result_mask is not None:
                processed = cv2.bitwise_and(processed, processed, 
                                          mask=self.result_mask)
            
            # Update preview
            self.preview.set_image(processed)
            self.current_image = processed
            
            # Update mask drawer background if needed
            if self.mask_drawer.image is None:
                self.mask_drawer.set_image(self.original_image)
            
        except Exception as e:
            print(f"Error updating preview: {str(e)}")
            
    def _on_mask_updated(self, mask):
        """Handle mask update from drawer"""
        self.result_mask = mask
        self.update_preview()
            
    def reset_params(self):
        """Reset all parameters to defaults"""
        self.advanced_widget.reset()
        self.adjustment_widget.reset()
        self.result_mask = None
        self.mask_drawer.clear_mask()
        self.update_preview()
        
    def apply_default_preset(self):
        """Apply default enhancement preset"""
        self.advanced_widget.apply_default_preset()
        self.adjustment_widget.reset()
        
    def apply_auto_preset(self):
        """Apply automatic optimization preset"""
        self.advanced_widget.apply_auto_preset()
        self.adjustment_widget.reset()
        
    def get_result(self):
        """Get processed image"""
        return self.current_image
        
    def get_mask(self):
        """Get current mask"""
        return self.result_mask
