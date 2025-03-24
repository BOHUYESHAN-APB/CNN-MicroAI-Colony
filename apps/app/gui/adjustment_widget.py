"""
Image adjustment widget implementation
图像调整控件实现
"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QGroupBox, QLabel
from PyQt6.QtCore import pyqtSignal
import numpy as np
import cv2

from .slider_with_value import SliderWithValue

class AdjustmentWidget(QWidget):
    """Basic image adjustment widget"""
    
    # Signal emitted when settings change
    settingsChanged = pyqtSignal()
    
    def __init__(self, parent=None):
        """Initialize widget"""
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """Setup UI elements"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # Brightness/Contrast group
        bc_group = QGroupBox("亮度/对比度")
        bc_layout = QVBoxLayout()
        
        # Brightness
        bc_layout.addWidget(QLabel("亮度:"))
        self.brightness = SliderWithValue(-100, 100, step=1)
        self.brightness.valueChanged.connect(self.settingsChanged)
        bc_layout.addWidget(self.brightness)
        
        # Contrast
        bc_layout.addWidget(QLabel("对比度:"))
        self.contrast = SliderWithValue(-100, 100, step=1)
        self.contrast.valueChanged.connect(self.settingsChanged)
        bc_layout.addWidget(self.contrast)
        
        bc_group.setLayout(bc_layout)
        layout.addWidget(bc_group)
        
        # Color group
        color_group = QGroupBox("颜色调整")
        color_layout = QVBoxLayout()
        
        # Saturation
        color_layout.addWidget(QLabel("饱和度:"))
        self.saturation = SliderWithValue(-100, 100, step=1)
        self.saturation.valueChanged.connect(self.settingsChanged)
        color_layout.addWidget(self.saturation)
        
        # Hue
        color_layout.addWidget(QLabel("色相:"))
        self.hue = SliderWithValue(-180, 180, step=1)
        self.hue.valueChanged.connect(self.settingsChanged)
        color_layout.addWidget(self.hue)
        
        color_group.setLayout(color_layout)
        layout.addWidget(color_group)
        
        # Filter group
        filter_group = QGroupBox("滤波")
        filter_layout = QVBoxLayout()
        
        # Blur
        filter_layout.addWidget(QLabel("模糊:"))
        self.blur = SliderWithValue(0, 20, step=1)
        self.blur.valueChanged.connect(self.settingsChanged)
        filter_layout.addWidget(self.blur)
        
        filter_group.setLayout(filter_layout)
        layout.addWidget(filter_group)
        
        layout.addStretch()
        
    def reset(self):
        """Reset all values to default"""
        self.brightness.setValue(0)
        self.contrast.setValue(0)
        self.saturation.setValue(0)
        self.hue.setValue(0)
        self.blur.setValue(0)
        
    def process_image(self, image):
        """Process image with current settings
        
        Args:
            image: Input image (numpy array)
            
        Returns:
            Processed image
        """
        try:
            # Make a copy to avoid modifying original
            image = image.copy()
            
            # Apply brightness/contrast
            brightness = self.brightness.value()
            contrast = self.contrast.value()
            
            # Convert contrast to scaling factor
            contrast_factor = (259 * (contrast + 255)) / (255 * (259 - contrast))
            
            # Apply contrast
            image = np.clip(128 + contrast_factor * (image - 128), 0, 255).astype(np.uint8)
            
            # Apply brightness
            image = np.clip(image + brightness, 0, 255).astype(np.uint8)
            
            # Apply color adjustments
            if self.saturation.value() != 0 or self.hue.value() != 0:
                hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV).astype(np.float32)
                
                # Apply hue adjustment
                hsv[:,:,0] = np.mod(hsv[:,:,0] + self.hue.value(), 180)
                
                # Apply saturation adjustment
                saturation = self.saturation.value()
                saturation_scale = (1 + saturation/100) if saturation > 0 else (1 - abs(saturation)/100)
                hsv[:,:,1] = np.clip(hsv[:,:,1] * saturation_scale, 0, 255)
                
                # Convert back
                image = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)
                
            # Apply blur
            if self.blur.value() > 0:
                blur_size = self.blur.value() * 2 + 1  # Make sure it's odd
                image = cv2.GaussianBlur(image, (blur_size, blur_size), 0)
                
            return image
            
        except Exception as e:
            print(f"Error processing image: {str(e)}")
            return image
