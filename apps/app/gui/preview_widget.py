"""
Preview widget for preprocessing results
预处理结果预览组件
"""
import cv2
import numpy as np
import logging
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QImage, QPixmap
from pathlib import Path

logger = logging.getLogger(__name__)

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
        
        # Create preview labels
        self.original_label = QLabel("原图")
        self.original_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.original_label.setStyleSheet("""
            QLabel {
                background: #1e1e1e;
                border: 1px solid #3d3d3d;
                padding: 4px;
                color: #e0e0e0;
            }
        """)
        layout.addWidget(self.original_label)
        
        self.processed_label = QLabel("处理后")
        self.processed_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.processed_label.setStyleSheet("""
            QLabel {
                background: #1e1e1e;
                border: 1px solid #3d3d3d;
                padding: 4px;
                color: #e0e0e0;
            }
        """)
        layout.addWidget(self.processed_label)
        
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
            # Get preview size (maintain aspect ratio)
            preview_height = 200
            height, width = self.original_image.shape[:2]
            preview_width = int(width * (preview_height / height))
            
            # Original image preview
            orig_preview = cv2.resize(
                self.original_image, 
                (preview_width, preview_height),
                interpolation=cv2.INTER_AREA
            )
            orig_qimg = self._array_to_qimage(orig_preview)
            self.original_label.setPixmap(QPixmap.fromImage(orig_qimg))
            
            # Processed image preview
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
                     
    def minimumSizeHint(self):
        """Provide reasonable minimum size"""
        return QSize(300, 400)
        
    def clear(self):
        """Clear previews"""
        self.original_image = None
        self.config = None
        self.original_label.clear()
        self.processed_label.clear()
        self.original_label.setText("原图")
        self.processed_label.setText("处理后")
