"""
Preprocessing settings dialog - 重构版本
预处理设置对话框重构版
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QSplitter, 
    QGroupBox, QLabel, QCheckBox, QSpinBox, QWidget,
    QDoubleSpinBox, QPushButton, QScrollArea, QGridLayout
)
from PyQt6.QtCore import Qt, pyqtSignal
import numpy as np
import cv2
import logging
from ..utils.image_preprocessing import PreprocessingConfig
from .preview_widget import PreviewWidget

logger = logging.getLogger(__name__)

class MaskDrawingWidget(QWidget):
    """Widget for drawing mask with shape presets"""
    mask_updated = pyqtSignal(object)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.drawing = False
        self.erasing = False
        self.last_pos = None
        self.current_mask = None
        self.image = None
        self.scaled_image = None
        self.scale_factor = 1.0
        self.brush_size = 10
        self.setMouseTracking(True)
        self.setMinimumSize(300, 200)
        
    def set_image(self, image):
        """Set background image"""
        self.image = image
        self.update_scaled_image()
        self.update()
        
    def update_scaled_image(self):
        """Update scaled version of image"""
        if self.image is None:
            return
            
        h, w = self.image.shape[:2]
        widget_w = self.width()
        widget_h = self.height()
        
        # Calculate scale to fit widget while maintaining aspect ratio
        scale_w = widget_w / w
        scale_h = widget_h / h
        self.scale_factor = min(scale_w, scale_h)
        
        new_w = int(w * self.scale_factor)
        new_h = int(h * self.scale_factor)
        
        self.scaled_image = cv2.resize(self.image, (new_w, new_h))
        self.current_mask = np.ones((new_h, new_w), dtype=np.uint8)
        
    def mousePressEvent(self, event):
        """Handle mouse press for drawing"""
        if event.button() == Qt.MouseButton.LeftButton and self.scaled_image is not None:
            self.drawing = True
            self.last_pos = event.pos()
            self.draw_at_position(event.pos())
            
    def mouseMoveEvent(self, event):
        """Handle mouse movement for continuous drawing"""
        if self.drawing and self.scaled_image is not None:
            self.draw_at_position(event.pos())
            self.last_pos = event.pos()
            
    def mouseReleaseEvent(self, event):
        """Handle mouse release"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.drawing = False
            self.emit_mask()
            
    def draw_at_position(self, pos):
        """Draw at specified position"""
        if self.current_mask is None:
            return
            
        x = pos.x()
        y = pos.y()
        h, w = self.current_mask.shape[:2]
        
        # Convert to image coordinates
        img_x = int(x / self.scale_factor)
        img_y = int(y / self.scale_factor)
        
        # Draw circle at position
        cv2.circle(self.current_mask, (img_x, img_y), 
                  self.brush_size, 
                  1 if not self.erasing else 0, 
                  -1)
        
        self.update()
        
    def emit_mask(self):
        """Emit current mask"""
        if self.image is None or self.current_mask is None:
            return
            
        h_orig, w_orig = self.image.shape[:2]
        original_size_mask = cv2.resize(self.current_mask, (w_orig, h_orig))
        self.mask_updated.emit(original_size_mask)

class PreprocessingDialog(QDialog):
    """重构后的预处理设置对话框"""
    config_changed = pyqtSignal()

    def __init__(self, parent=None, image=None):
        super().__init__(parent)
        self.image = image
        self.config = PreprocessingConfig()
        # 默认禁用所有处理
        self.config.normalize = False
        self.config.clahe_enabled = False 
        self.config.hist_equal = False
        self.config.sharpen = False
        self.setup_ui()

    def setup_ui(self):
        """重构后的UI设置"""
        self.setWindowTitle("新版预处理设置")
        self.resize(1000, 700)
        
        # 主布局
        main_layout = QVBoxLayout(self)
        
        # 水平分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 左侧设置区域
        settings_scroll = QScrollArea()
        settings_scroll.setWidgetResizable(True)
        settings_widget = QWidget()
        settings_layout = QVBoxLayout(settings_widget)
        settings_layout.setContentsMargins(5, 5, 5, 5)
        
        # 参数标签页
        self.tab_widget = QTabWidget()
        
        # 基本预处理标签页
        self.setup_basic_tab()
        # 高级处理标签页
        self.setup_advanced_tab()
        
        settings_layout.addWidget(self.tab_widget)
        settings_scroll.setWidget(settings_widget)
        splitter.addWidget(settings_scroll)
        
        # 右侧预览区域保持不变
        self.preview = PreviewWidget()
        if self.image is not None:
            self.preview.set_image(self.image)
        splitter.addWidget(self.preview)
        
        splitter.setSizes([400, 600])
        main_layout.addWidget(splitter)
        
    def setup_basic_tab(self):
        """设置基本预处理标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # 亮度调整组
        brightness_group = QGroupBox("亮度调整")
        brightness_layout = QVBoxLayout()
        
        self.normalize_cb = QCheckBox("亮度归一化")
        brightness_layout.addWidget(self.normalize_cb)
        
        brightness_params = QHBoxLayout()
        brightness_params.addWidget(QLabel("伽马值:"))
        self.gamma_sb = QDoubleSpinBox()
        self.gamma_sb.setRange(0.1, 3.0)
        self.gamma_sb.setValue(1.0)
        self.gamma_sb.valueChanged.connect(self.on_param_changed)
        brightness_params.addWidget(self.gamma_sb)
        brightness_layout.addLayout(brightness_params)
        
        brightness_group.setLayout(brightness_layout)
        layout.addWidget(brightness_group)
        
        # 对比度组
        contrast_group = QGroupBox("对比度增强")
        contrast_layout = QVBoxLayout()
        
        self.clahe_cb = QCheckBox("CLAHE均衡化")
        contrast_layout.addWidget(self.clahe_cb)
        
        clahe_params = QGridLayout()
        clahe_params.addWidget(QLabel("剪裁限制:"), 0, 0)
        self.clahe_clip_sb = QDoubleSpinBox()
        self.clahe_clip_sb.setRange(1.0, 10.0)
        self.clahe_clip_sb.setValue(2.0)
        clahe_params.addWidget(self.clahe_clip_sb, 0, 1)
        
        clahe_params.addWidget(QLabel("网格大小:"), 1, 0)
        self.clahe_grid_sb = QSpinBox()
        self.clahe_grid_sb.setRange(4, 64)
        self.clahe_grid_sb.setValue(8)
        clahe_params.addWidget(self.clahe_grid_sb, 1, 1)
        
        contrast_layout.addLayout(clahe_params)
        
        self.hist_equal_cb = QCheckBox("直方图均衡化")
        contrast_layout.addWidget(self.hist_equal_cb)
        
        contrast_group.setLayout(contrast_layout)
        layout.addWidget(contrast_group)
        
        # 锐化组
        sharpen_group = QGroupBox("锐化强化")
        sharpen_layout = QVBoxLayout()
        
        self.sharpen_cb = QCheckBox("启用锐化")
        sharpen_layout.addWidget(self.sharpen_cb)
        
        sharpen_params = QHBoxLayout()
        sharpen_params.addWidget(QLabel("强度:"))
        self.sharpen_amount_sb = QDoubleSpinBox()
        self.sharpen_amount_sb.setRange(0.1, 5.0)
        self.sharpen_amount_sb.setValue(1.0)
        sharpen_params.addWidget(self.sharpen_amount_sb)
        
        sharpen_layout.addLayout(sharpen_params)
        sharpen_group.setLayout(sharpen_layout)
        layout.addWidget(sharpen_group)
        
        self.tab_widget.addTab(tab, "基本预处理")

    def setup_advanced_tab(self):
        """设置高级处理标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # 遮罩绘制组
        mask_group = QGroupBox("遮罩绘制")
        mask_layout = QVBoxLayout()
        
        self.mask_widget = MaskDrawingWidget()
        if self.image is not None:
            self.mask_widget.set_image(self.image)
        self.mask_widget.mask_updated.connect(self.on_mask_updated)
        mask_layout.addWidget(self.mask_widget)
        
        # 绘制模式选择
        draw_mode_layout = QHBoxLayout()
        self.free_draw_btn = QPushButton("自由绘制")
        self.free_draw_btn.setCheckable(True)
        self.free_draw_btn.setChecked(True)
        draw_mode_layout.addWidget(self.free_draw_btn)
        
        self.erase_btn = QPushButton("擦除")
        self.erase_btn.setCheckable(True)
        draw_mode_layout.addWidget(self.erase_btn)
        
        mask_layout.addLayout(draw_mode_layout)
        
        # 画笔设置
        brush_layout = QHBoxLayout()
        brush_layout.addWidget(QLabel("画笔大小:"))
        self.brush_size_sb = QSpinBox()
        self.brush_size_sb.setRange(1, 50)
        self.brush_size_sb.setValue(10)
        brush_layout.addWidget(self.brush_size_sb)
        
        mask_layout.addLayout(brush_layout)
        mask_group.setLayout(mask_layout)
        layout.addWidget(mask_group)
        
        # 边缘检测组
        edge_group = QGroupBox("边缘检测")
        edge_layout = QVBoxLayout()
        
        self.edge_cb = QCheckBox("启用边缘检测")
        edge_layout.addWidget(self.edge_cb)
        
        edge_group.setLayout(edge_layout)
        layout.addWidget(edge_group)
        
        # 形态学操作组
        morph_group = QGroupBox("形态学操作")
        morph_layout = QVBoxLayout()
        
        self.morph_cb = QCheckBox("启用形态学操作")
        morph_layout.addWidget(self.morph_cb)
        
        morph_group.setLayout(morph_layout)
        layout.addWidget(morph_group)
        
        self.tab_widget.addTab(tab, "高级处理")

    def on_mask_updated(self, mask):
        """Handle mask updates"""
        if self.config:
            self.config.mask = mask
            self.preview.set_config(self.config)
            self.config_changed.emit()

    def on_param_changed(self):
        """Handle parameter changes"""
        if not self.image or not self.config:
            return
            
        # Update config with current values
        self.config.gamma = self.gamma_sb.value()
        self.config.clahe_enabled = self.clahe_cb.isChecked()
        self.config.clahe_clip = self.clahe_clip_sb.value()
        self.config.clahe_grid = self.clahe_grid_sb.value()
        self.config.hist_equal = self.hist_equal_cb.isChecked()
        self.config.sharpen = self.sharpen_cb.isChecked()
        self.config.sharpen_amount = self.sharpen_amount_sb.value()
        
        # Update preview
        self.preview.set_config(self.config)
        self.config_changed.emit()
