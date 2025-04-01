"""
Preview widget for preprocessing results
预处理结果预览组件
"""
import cv2
import numpy as np
import logging
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QScrollArea, QHBoxLayout
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QImage, QPixmap

logger = logging.getLogger(__name__)

class PreviewLabel(QLabel):
    """Custom label with size hint override"""
    def __init__(self, text=""):
        super().__init__(text)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumSize(400, 300)
        
    def sizeHint(self):
        """Provide size hint"""
        if self.pixmap():
            return self.pixmap().size()
        return QSize(400, 300)

class PreviewWidget(QWidget):
    """Widget for displaying image preprocessing preview"""
    
    def __init__(self):
        super().__init__()
        self.original_image = None
        self.config = None
        self.setup_ui()
        
    def setup_ui(self):
        """Setup UI components"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create scroll areas with labels for previews
        self.original_scroll = QScrollArea()
        self.original_scroll.setWidgetResizable(True)
        self.original_scroll.setFrameShape(self.original_scroll.Shape.NoFrame)
        
        self.processed_scroll = QScrollArea()
        self.processed_scroll.setWidgetResizable(True)
        self.processed_scroll.setFrameShape(self.processed_scroll.Shape.NoFrame)
        
        # Create preview labels with titles
        original_container = QWidget()
        original_layout = QVBoxLayout(original_container)
        original_layout.setContentsMargins(0, 0, 0, 0)
        
        title_layout = QHBoxLayout()
        title_layout.addStretch()
        title_label = QLabel(" ➤ 原图(Original)")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 12px;
                font-weight: bold;
                color: #a0a0a0;
                padding: 4px 8px;
                margin-bottom: 10px; /* 增加底部外边距 */
            }
        """)
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        original_layout.addLayout(title_layout)
        
        self.original_label = PreviewLabel()
        self.original_label.setStyleSheet("""
            QLabel {
                background: #1e1e1e;
                border: 1px solid #3d3d3d;
                padding: 4px;
                color: #e0e0e0;
            }
        """)
        original_layout.addWidget(self.original_label)
        self.original_scroll.setWidget(original_container)
        
        processed_container = QWidget()
        processed_layout = QVBoxLayout(processed_container)
        processed_layout.setContentsMargins(0, 0, 0, 0)
        
        title_layout = QHBoxLayout()
        title_layout.addStretch()
        title_label = QLabel(" ➤ 预处理结果(Processed)")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 12px;
                font-weight: bold;
                color: #a0a0a0;
                padding: 4px 8px;
            }
        """)
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        processed_layout.addLayout(title_layout)
        
        self.processed_label = PreviewLabel()
        self.processed_label.setStyleSheet("""
            QLabel {
                background: #1e1e1e;
                border: 1px solid #3d3d3d;
                padding: 4px;
                color: #e0e0e0;
            }
        """)
        processed_layout.addWidget(self.processed_label)
        self.processed_scroll.setWidget(processed_container)
        
        # Add scroll areas to layout
        layout.addWidget(self.original_scroll)
        layout.addWidget(self.processed_scroll)
        
    def set_image(self, image):
        """Set original image for preview
        
        Args:
            image: OpenCV RGB image array
        """
        if image is None:
            return
            
        self.original_image = image.copy()
        self.update_preview()
        
    def set_config(self, config):
        """Set preprocessing configuration
        
        Args:
            config: PreprocessingConfig object or config dict
        """
        if isinstance(config, dict):
            from ..utils.image_preprocessing import PreprocessingConfig
            self.config = PreprocessingConfig.from_dict(config)
        else:
            self.config = config
            
        self.update_preview()
        
    def update_preview(self):
        """Update preview display"""
        if self.original_image is None:
            return
            
        try:
            # Calculate preview size to fit widget while maintaining aspect ratio
            height, width = self.original_image.shape[:2]
            max_height = self.height() // 2 - 40  # Account for titles and padding
            scale = max_height / height if height > max_height else 1.0
            preview_width = int(width * scale)
            preview_height = int(height * scale)
            
            # Original image preview with mask overlay
            orig_preview = cv2.resize(
                self.original_image,
                (preview_width, preview_height),
                interpolation=cv2.INTER_AREA
            )
            
            # Draw mask overlay on original if mask exists
            if self.config and hasattr(self.config, 'mask') and self.config.mask is not None:
                try:
                    # Ensure mask matches preview size
                    mask_preview = cv2.resize(
                        self.config.mask,
                        (preview_width, preview_height),
                        interpolation=cv2.INTER_NEAREST
                    )
                    
                    # Convert mask to 3-channel if needed
                    if len(mask_preview.shape) == 2:
                        mask_preview = np.stack([mask_preview]*3, axis=-1)
                    
                    # Create semi-transparent red overlay
                    overlay = np.zeros_like(orig_preview)
                    overlay[..., 2] = 128  # Red channel
                    
                    # Apply overlay only where mask is non-zero
                    mask_bool = mask_preview[..., 0] > 0
                    for c in range(3):
                        orig_preview[..., c] = np.where(
                            mask_bool,
                            orig_preview[..., c] * 0.7 + overlay[..., c] * 0.3,
                            orig_preview[..., c]
                        )
                except Exception as e:
                    logger.error(f"Error applying mask overlay: {str(e)}")
            
            # Convert and display original
            orig_qimg = self._array_to_qimage(orig_preview)
            self.original_label.setPixmap(QPixmap.fromImage(orig_qimg))
            
            # Process and display result
            if self.config:
                from ..utils.image_preprocessing import preprocess_image
                processed = preprocess_image(self.original_image, self.config)
                if processed is not None:
                    # Resize processed image
                    proc_preview = cv2.resize(
                        processed,
                        (preview_width, preview_height),
                        interpolation=cv2.INTER_AREA
                    )
                    
                    # Convert grayscale to RGB if needed
                    if len(proc_preview.shape) == 2:
                        proc_preview = cv2.cvtColor(proc_preview, cv2.COLOR_GRAY2RGB)
                    
                    proc_qimg = self._array_to_qimage(proc_preview)
                    self.processed_label.setPixmap(QPixmap.fromImage(proc_qimg))
                    
        except Exception as e:
            logger.error(f"Error updating preview: {str(e)}")
                
    def _array_to_qimage(self, image):
        """Convert OpenCV image array to QImage
        
        Args:
            image: OpenCV RGB image array
            
        Returns:
            QImage
        """
        height, width, channel = image.shape
        bytes_per_line = 3 * width
        return QImage(
            image.data,
            width,
            height,
            bytes_per_line,
            QImage.Format.Format_RGB888
        )
        
    def clear(self):
        """Clear previews"""
        self.original_image = None
        self.config = None
        self.original_label.clear()
        self.processed_label.clear()
        self.original_label.setText("原图")
        self.processed_label.setText("预处理结果")
        
    def resizeEvent(self, event):
        """Handle resize event"""
        super().resizeEvent(event)
        self.update_preview()
