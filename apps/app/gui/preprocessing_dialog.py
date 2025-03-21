"""
Preprocessing settings dialog
预处理设置对话框
"""
import cv2
import numpy as np
import logging
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                            QSpinBox, QDoubleSpinBox, QCheckBox, QPushButton,
                            QGroupBox, QWidget, QSplitter)
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QPoint
from PyQt6.QtGui import QPainter, QPen, QColor, QMouseEvent, QImage
from .preview_widget import PreviewWidget
from ..utils.image_preprocessing import PreprocessingConfig

logger = logging.getLogger(__name__)

class MaskDrawingWidget(QWidget):
    """Widget for drawing mask"""
    mask_updated = pyqtSignal(object)  # Emits the mask array
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.drawing = False
        self.mask_points = []
        self.current_mask = None
        self.image = None
        self.scaled_image = None
        self.scale_factor = 1.0
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
        
    def mousePressEvent(self, event: QMouseEvent):
        """Handle mouse press"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.drawing = True
            self.mask_points = [event.pos()]
            self.update()
            
    def mouseMoveEvent(self, event: QMouseEvent):
        """Handle mouse move"""
        if self.drawing:
            self.mask_points.append(event.pos())
            self.update()
            
    def mouseReleaseEvent(self, event: QMouseEvent):
        """Handle mouse release"""
        if event.button() == Qt.MouseButton.LeftButton and self.drawing:
            self.drawing = False
            self.finalize_mask()
            
    def finalize_mask(self):
        """Create mask from drawn points"""
        if not self.mask_points or self.scaled_image is None:
            return
            
        # Convert points to numpy array
        points = np.array([(p.x(), p.y()) for p in self.mask_points])
        
        # Create mask
        mask = np.zeros_like(self.current_mask)
        cv2.fillPoly(mask, [points.astype(np.int32)], 1)
        
        # Update current mask
        self.current_mask = mask
        
        # Scale mask back to original image size
        h, w = self.image.shape[:2]
        original_size_mask = cv2.resize(mask, (w, h))
        
        # Emit mask
        self.mask_updated.emit(original_size_mask)
        
    def paintEvent(self, event):
        """Paint widget"""
        painter = QPainter(self)
        
        # Draw background image
        if self.scaled_image is not None:
            height, width = self.scaled_image.shape[:2]
            
            # Calculate position to center image
            x = (self.width() - width) // 2
            y = (self.height() - height) // 2
            
            # Convert image to QImage
            bytes_per_line = 3 * width
            q_img = QImage(
                self.scaled_image.data,
                width,
                height,
                bytes_per_line,
                QImage.Format.Format_RGB888
            )
            painter.drawImage(x, y, q_img)
            
            # Draw current mask
            if self.current_mask is not None:
                painter.setOpacity(0.3)
                mask_color = QColor(255, 0, 0)  # Red for masked areas
                for i in range(height):
                    for j in range(width):
                        if self.current_mask[i, j] == 1:
                            painter.fillRect(x + j, y + i, 1, 1, mask_color)
            
            # Draw current line
            if self.drawing and len(self.mask_points) > 1:
                painter.setOpacity(1.0)
                pen = QPen(Qt.GlobalColor.yellow, 2)
                painter.setPen(pen)
                for i in range(len(self.mask_points)-1):
                    painter.drawLine(self.mask_points[i], self.mask_points[i+1])
                
    def resizeEvent(self, event):
        """Handle resize"""
        super().resizeEvent(event)
        self.update_scaled_image()
        
    def clear_mask(self):
        """Clear current mask"""
        if self.current_mask is not None:
            self.current_mask.fill(1)
            self.mask_points = []
            self.update()
            # Emit cleared mask
            h, w = self.image.shape[:2]
            self.mask_updated.emit(np.ones((h, w), dtype=np.uint8))

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
        self.setMinimumWidth(1200)
        
        # Create main layout
        layout = QVBoxLayout(self)
        
        # Create horizontal splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left side: settings
        settings_widget = QWidget()
        settings_layout = QVBoxLayout(settings_widget)
        settings_layout.setContentsMargins(0, 0, 0, 0)
        
        # Quick mode selection
        mode_group = QGroupBox("快速模式选择")
        mode_layout = QHBoxLayout()
        
        self.default_btn = QPushButton("默认参数")
        self.default_btn.clicked.connect(self.use_default_params)
        mode_layout.addWidget(self.default_btn)
        
        self.auto_btn = QPushButton("自动优化")
        self.auto_btn.clicked.connect(self.use_auto_params)
        mode_layout.addWidget(self.auto_btn)
        
        mode_group.setLayout(mode_layout)
        settings_layout.addWidget(mode_group)
        
        # Mask drawing
        mask_group = QGroupBox("培养基区域选择")
        mask_layout = QVBoxLayout()
        
        self.mask_widget = MaskDrawingWidget()
        if self.image is not None:
            self.mask_widget.set_image(self.image)
        self.mask_widget.mask_updated.connect(self.on_mask_updated)
        mask_layout.addWidget(self.mask_widget)
        
        mask_buttons = QHBoxLayout()
        clear_mask_btn = QPushButton("清除区域")
        clear_mask_btn.clicked.connect(self.mask_widget.clear_mask)
        mask_buttons.addWidget(clear_mask_btn)
        mask_layout.addLayout(mask_buttons)
        
        mask_group.setLayout(mask_layout)
        settings_layout.addWidget(mask_group)
        
        # Parameter groups
        params_group = QGroupBox("预处理参数")
        params_layout = QVBoxLayout()
        
        # Glare removal
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
        params_layout.addLayout(glare_layout)
        
        # Normalization
        norm_layout = QVBoxLayout()
        self.normalize_cb = QCheckBox("启用亮度归一化")
        self.normalize_cb.setChecked(self.config.normalize)
        self.normalize_cb.stateChanged.connect(self.on_param_changed)
        norm_layout.addWidget(self.normalize_cb)
        params_layout.addLayout(norm_layout)
        
        # CLAHE
        clahe_layout = QVBoxLayout()
        self.clahe_cb = QCheckBox("启用CLAHE对比度增强")
        self.clahe_cb.setChecked(self.config.clahe)
        self.clahe_cb.stateChanged.connect(self.on_param_changed)
        clahe_layout.addWidget(self.clahe_cb)
        
        clahe_params = QHBoxLayout()
        clahe_params.addWidget(QLabel("对比度限制:"))
        self.clahe_clip_sb = QDoubleSpinBox()
        self.clahe_clip_sb.setRange(0.1, 10.0)
        self.clahe_clip_sb.setSingleStep(0.1)
        self.clahe_clip_sb.setValue(self.config.clahe_clip)
        self.clahe_clip_sb.valueChanged.connect(self.on_param_changed)
        clahe_params.addWidget(self.clahe_clip_sb)
        
        clahe_params.addWidget(QLabel("网格大小:"))
        self.clahe_grid_sb = QSpinBox()
        self.clahe_grid_sb.setRange(2, 16)
        self.clahe_grid_sb.setValue(self.config.clahe_grid)
        self.clahe_grid_sb.valueChanged.connect(self.on_param_changed)
        clahe_params.addWidget(self.clahe_grid_sb)
        
        clahe_layout.addLayout(clahe_params)
        params_layout.addLayout(clahe_layout)
        
        # Gaussian blur
        blur_layout = QVBoxLayout()
        self.blur_cb = QCheckBox("启用高斯模糊")
        self.blur_cb.setChecked(self.config.gaussian_blur)
        self.blur_cb.stateChanged.connect(self.on_param_changed)
        blur_layout.addWidget(self.blur_cb)
        
        blur_params = QHBoxLayout()
        blur_params.addWidget(QLabel("核大小:"))
        self.blur_kernel_sb = QSpinBox()
        self.blur_kernel_sb.setRange(3, 31)
        self.blur_kernel_sb.setSingleStep(2)
        self.blur_kernel_sb.setValue(self.config.blur_kernel)
        self.blur_kernel_sb.valueChanged.connect(self.on_param_changed)
        blur_params.addWidget(self.blur_kernel_sb)
        blur_layout.addLayout(blur_params)
        params_layout.addLayout(blur_layout)
        
        # Adaptive threshold
        thresh_layout = QVBoxLayout()
        self.threshold_cb = QCheckBox("启用自适应阈值")
        self.threshold_cb.setChecked(self.config.adaptive_threshold)
        self.threshold_cb.stateChanged.connect(self.on_param_changed)
        thresh_layout.addWidget(self.threshold_cb)
        
        thresh_params = QHBoxLayout()
        thresh_params.addWidget(QLabel("块大小:"))
        self.block_size_sb = QSpinBox()
        self.block_size_sb.setRange(3, 99)
        self.block_size_sb.setSingleStep(2)
        self.block_size_sb.setValue(self.config.block_size)
        self.block_size_sb.valueChanged.connect(self.on_param_changed)
        thresh_params.addWidget(self.block_size_sb)
        
        thresh_params.addWidget(QLabel("C值:"))
        self.c_value_sb = QSpinBox()
        self.c_value_sb.setRange(-10, 10)
        self.c_value_sb.setValue(self.config.c_value)
        self.c_value_sb.valueChanged.connect(self.on_param_changed)
        thresh_params.addWidget(self.c_value_sb)
        
        thresh_layout.addLayout(thresh_params)
        params_layout.addLayout(thresh_layout)
        
        params_group.setLayout(params_layout)
        settings_layout.addWidget(params_group)
        
        # Bottom buttons
        button_layout = QHBoxLayout()
        ok_btn = QPushButton("确定")
        ok_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(ok_btn)
        button_layout.addWidget(cancel_btn)
        settings_layout.addLayout(button_layout)
        
        # Add settings widget to splitter
        splitter.addWidget(settings_widget)
        
        # Right side: preview
        self.preview = PreviewWidget()
        if self.image is not None:
            self.preview.set_image(self.image)
            self.preview.set_config(self.config)
        splitter.addWidget(self.preview)
        
        # Set initial sizes
        splitter.setSizes([400, 800])
        
        # Add splitter to main layout
        layout.addWidget(splitter)
        
    def use_default_params(self):
        """Use default parameters"""
        self.config = PreprocessingConfig()
        self.update_controls()
        self.preview.set_config(self.config)
        
    def use_auto_params(self):
        """Use auto-optimized parameters"""
        self.config = PreprocessingConfig()
        self.config.auto_optimize = True
        self.preview.set_config(self.config)
        
    def on_mask_updated(self, mask):
        """Handle mask updates"""
        if self.config:
            self.config.mask = mask
            self.preview.set_config(self.config)
        
    def update_controls(self):
        """Update controls from config"""
        # Glare removal
        self.remove_glare_cb.setChecked(self.config.remove_glare)
        self.glare_threshold_sb.setValue(self.config.glare_threshold)
        
        # Normalization
        self.normalize_cb.setChecked(self.config.normalize)
        
        # CLAHE
        self.clahe_cb.setChecked(self.config.clahe)
        self.clahe_clip_sb.setValue(self.config.clahe_clip)
        self.clahe_grid_sb.setValue(self.config.clahe_grid)
        
        # Gaussian blur
        self.blur_cb.setChecked(self.config.gaussian_blur)
        self.blur_kernel_sb.setValue(self.config.blur_kernel)
        
        # Adaptive threshold
        self.threshold_cb.setChecked(self.config.adaptive_threshold)
        self.block_size_sb.setValue(self.config.block_size)
        self.c_value_sb.setValue(self.config.c_value)
        
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
        """Load configuration into dialog"""
        if isinstance(config, dict):
            self.config = PreprocessingConfig.from_dict(config)
        else:
            self.config = config
        self.update_controls()
        if self.image is not None:
            self.preview.set_config(self.config)
            
    def get_config(self):
        """Get current configuration"""
        return self.config
