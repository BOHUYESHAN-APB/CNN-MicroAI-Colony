"""
Advanced image processing widget implementation
高级图像处理控件实现
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
                            QLabel, QComboBox, QCheckBox, QPushButton,
                            QScrollArea)
from PyQt6.QtCore import pyqtSignal
import cv2
import numpy as np

from .slider_with_value import SliderWithValue
from ..utils.gpu_utils import (gpu_gaussian_blur, gpu_canny, gpu_watershed,
                              gpu_morphology, gpu_threshold, detect_gpu)

class AdvancedProcessingWidget(QWidget):
    """Advanced image processing widget"""
    
    # Signal emitted when settings change
    settingsChanged = pyqtSignal()
    
    def __init__(self, parent=None):
        """Initialize widget"""
        super().__init__(parent)
        self.use_gpu = detect_gpu()
        self.setup_ui()
        
    def setup_ui(self):
        """Setup UI elements"""
        main_layout = QVBoxLayout(self)
        
        # Create scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(10)
        
        # Quick presets group
        preset_group = QGroupBox("快速预设")
        preset_layout = QHBoxLayout()
        
        default_btn = QPushButton("默认增强")
        default_btn.clicked.connect(self.apply_default_preset)
        preset_layout.addWidget(default_btn)
        
        auto_btn = QPushButton("自动优化")
        auto_btn.clicked.connect(self.apply_auto_preset)
        preset_layout.addWidget(auto_btn)
        
        detail_btn = QPushButton("细节增强")
        detail_btn.clicked.connect(self.apply_detail_preset)
        preset_layout.addWidget(detail_btn)
        
        edge_btn = QPushButton("边缘增强")
        edge_btn.clicked.connect(self.apply_edge_preset)
        preset_layout.addWidget(edge_btn)
        
        preset_group.setLayout(preset_layout)
        layout.addWidget(preset_group)
        
        # Edge detection group
        edge_group = QGroupBox("边缘检测")
        edge_layout = QVBoxLayout()
        
        # Edge detection type
        self.edge_type = QComboBox()
        self.edge_type.addItems(["无", "Canny算子", "Sobel算子", "Laplacian算子"])
        self.edge_type.currentIndexChanged.connect(self.settingsChanged)
        edge_layout.addWidget(QLabel("检测方法:"))
        edge_layout.addWidget(self.edge_type)
        
        # Canny parameters
        self.canny_low = SliderWithValue(0, 255, step=1)
        self.canny_low.valueChanged.connect(self.settingsChanged)
        edge_layout.addWidget(QLabel("低阈值:"))
        edge_layout.addWidget(self.canny_low)
        
        self.canny_high = SliderWithValue(0, 255, step=1)
        self.canny_high.valueChanged.connect(self.settingsChanged)
        edge_layout.addWidget(QLabel("高阈值:"))
        edge_layout.addWidget(self.canny_high)
        
        edge_group.setLayout(edge_layout)
        layout.addWidget(edge_group)
        
        # Morphological operations group
        morph_group = QGroupBox("形态学操作")
        morph_layout = QVBoxLayout()
        
        self.morph_type = QComboBox()
        self.morph_type.addItems(["无", "腐蚀", "膨胀", "开运算", "闭运算",
                                 "梯度", "顶帽", "黑帽"])
        self.morph_type.currentIndexChanged.connect(self.settingsChanged)
        morph_layout.addWidget(QLabel("操作类型:"))
        morph_layout.addWidget(self.morph_type)
        
        self.kernel_size = SliderWithValue(1, 31, step=2)
        self.kernel_size.valueChanged.connect(self.settingsChanged)
        morph_layout.addWidget(QLabel("核大小:"))
        morph_layout.addWidget(self.kernel_size)
        
        self.iterations = SliderWithValue(1, 10, step=1)
        self.iterations.valueChanged.connect(self.settingsChanged)
        morph_layout.addWidget(QLabel("迭代次数:"))
        morph_layout.addWidget(self.iterations)
        
        morph_group.setLayout(morph_layout)
        layout.addWidget(morph_group)
        
        # Segmentation group
        seg_group = QGroupBox("图像分割")
        seg_layout = QVBoxLayout()
        
        # Threshold type
        self.threshold_type = QComboBox()
        self.threshold_type.addItems(["无", "Otsu阈值", "自适应阈值",
                                    "分水岭算法"])
        self.threshold_type.currentIndexChanged.connect(self.settingsChanged)
        seg_layout.addWidget(QLabel("分割方法:"))
        seg_layout.addWidget(self.threshold_type)
        
        self.thresh_value = SliderWithValue(0, 255, step=1)
        self.thresh_value.valueChanged.connect(self.settingsChanged)
        seg_layout.addWidget(QLabel("阈值:"))
        seg_layout.addWidget(self.thresh_value)
        
        seg_group.setLayout(seg_layout)
        layout.addWidget(seg_group)
        
        # Filter group
        filter_group = QGroupBox("滤波处理")
        filter_layout = QVBoxLayout()
        
        self.filter_type = QComboBox()
        self.filter_type.addItems(["无", "高斯模糊", "中值滤波", "双边滤波",
                                  "非局部均值"])
        self.filter_type.currentIndexChanged.connect(self.settingsChanged)
        filter_layout.addWidget(QLabel("滤波类型:"))
        filter_layout.addWidget(self.filter_type)
        
        self.filter_size = SliderWithValue(1, 31, step=2)
        self.filter_size.valueChanged.connect(self.settingsChanged)
        filter_layout.addWidget(QLabel("核大小:"))
        filter_layout.addWidget(self.filter_size)
        
        self.filter_sigma = SliderWithValue(1, 200, step=1)
        self.filter_sigma.valueChanged.connect(self.settingsChanged)
        filter_layout.addWidget(QLabel("Sigma值:"))
        filter_layout.addWidget(self.filter_sigma)
        
        filter_group.setLayout(filter_layout)
        layout.addWidget(filter_group)
        
        # GPU acceleration
        if self.use_gpu:
            self.gpu_check = QCheckBox("启用GPU加速")
            self.gpu_check.setChecked(True)
            self.gpu_check.stateChanged.connect(self.settingsChanged)
            layout.addWidget(self.gpu_check)
            
        layout.addStretch()
        scroll.setWidget(content)
        main_layout.addWidget(scroll)
        
        # Set default values
        self.reset()
        
    def reset(self):
        """Reset all values to default"""
        self.edge_type.setCurrentIndex(0)
        self.canny_low.setValue(100)
        self.canny_high.setValue(200)
        self.morph_type.setCurrentIndex(0)
        self.kernel_size.setValue(3)
        self.iterations.setValue(1)
        self.threshold_type.setCurrentIndex(0)
        self.thresh_value.setValue(128)
        self.filter_type.setCurrentIndex(0)
        self.filter_size.setValue(3)
        self.filter_sigma.setValue(50)
        
    def apply_default_preset(self):
        """Apply default enhancement preset"""
        self.edge_type.setCurrentIndex(0)
        self.morph_type.setCurrentIndex(0)
        self.threshold_type.setCurrentIndex(0)
        self.filter_type.setCurrentIndex(1)  # Gaussian blur
        self.filter_size.setValue(3)
        self.filter_sigma.setValue(30)
        self.settingsChanged.emit()
        
    def apply_auto_preset(self):
        """Apply auto optimization preset"""
        self.edge_type.setCurrentIndex(0)
        self.morph_type.setCurrentIndex(0)
        self.threshold_type.setCurrentIndex(1)  # Otsu
        self.filter_type.setCurrentIndex(2)  # Median
        self.filter_size.setValue(3)
        self.settingsChanged.emit()
        
    def apply_detail_preset(self):
        """Apply detail enhancement preset"""
        self.edge_type.setCurrentIndex(0)
        self.morph_type.setCurrentIndex(5)  # Gradient
        self.kernel_size.setValue(3)
        self.iterations.setValue(1)
        self.threshold_type.setCurrentIndex(0)
        self.filter_type.setCurrentIndex(3)  # Bilateral
        self.filter_size.setValue(5)
        self.filter_sigma.setValue(75)
        self.settingsChanged.emit()
        
    def apply_edge_preset(self):
        """Apply edge detection preset"""
        self.edge_type.setCurrentIndex(1)  # Canny
        self.canny_low.setValue(50)
        self.canny_high.setValue(150)
        self.morph_type.setCurrentIndex(2)  # Dilate
        self.kernel_size.setValue(3)
        self.iterations.setValue(1)
        self.threshold_type.setCurrentIndex(0)
        self.filter_type.setCurrentIndex(1)  # Gaussian
        self.filter_size.setValue(3)
        self.filter_sigma.setValue(1)
        self.settingsChanged.emit()
        
    def process_image(self, image):
        """Process image with current settings
        
        Args:
            image: Input image (numpy array)
            
        Returns:
            Processed image
        """
        try:
            # Make a copy to avoid modifying original
            processed = image.copy()
            
            # Apply filter
            filter_type = self.filter_type.currentText()
            if filter_type != "无":
                kernel_size = self.filter_size.value()
                if kernel_size % 2 == 0:
                    kernel_size += 1
                sigma = self.filter_sigma.value()
                
                if filter_type == "高斯模糊":
                    processed = gpu_gaussian_blur(processed, kernel_size, sigma)
                elif filter_type == "中值滤波":
                    processed = cv2.medianBlur(processed, kernel_size)
                elif filter_type == "双边滤波":
                    d = kernel_size
                    sigmaColor = sigma
                    sigmaSpace = sigma
                    processed = cv2.bilateralFilter(processed, d, sigmaColor, sigmaSpace)
                elif filter_type == "非局部均值":
                    h = sigma
                    processed = cv2.fastNlMeansDenoisingColored(processed, None, h, h, 7, 21)
            
            # Apply morphological operation
            morph_type = self.morph_type.currentText()
            if morph_type != "无":
                kernel_size = self.kernel_size.value()
                iterations = self.iterations.value()
                
                if morph_type == "腐蚀":
                    op = cv2.MORPH_ERODE
                elif morph_type == "膨胀":
                    op = cv2.MORPH_DILATE
                elif morph_type == "开运算":
                    op = cv2.MORPH_OPEN
                elif morph_type == "闭运算":
                    op = cv2.MORPH_CLOSE
                elif morph_type == "梯度":
                    op = cv2.MORPH_GRADIENT
                elif morph_type == "顶帽":
                    op = cv2.MORPH_TOPHAT
                elif morph_type == "黑帽":
                    op = cv2.MORPH_BLACKHAT
                    
                processed = gpu_morphology(processed, op, kernel_size, iterations)
            
            # Apply thresholding
            thresh_type = self.threshold_type.currentText()
            if thresh_type != "无":
                if thresh_type == "Otsu阈值":
                    gray = cv2.cvtColor(processed, cv2.COLOR_BGR2GRAY)
                    processed = gpu_threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                    processed = cv2.cvtColor(processed, cv2.COLOR_GRAY2BGR)
                elif thresh_type == "自适应阈值":
                    gray = cv2.cvtColor(processed, cv2.COLOR_BGR2GRAY)
                    processed = cv2.adaptiveThreshold(gray, 255,
                                                    cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                                    cv2.THRESH_BINARY, 11, 2)
                    processed = cv2.cvtColor(processed, cv2.COLOR_GRAY2BGR)
                elif thresh_type == "分水岭算法":
                    gray = cv2.cvtColor(processed, cv2.COLOR_BGR2GRAY)
                    ret, markers = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                    markers = np.int32(markers)
                    processed = gpu_watershed(processed, markers)
            
            # Apply edge detection
            edge_type = self.edge_type.currentText()
            if edge_type != "无":
                if edge_type == "Canny算子":
                    edges = gpu_canny(processed, self.canny_low.value(), 
                                    self.canny_high.value())
                    processed = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
                elif edge_type == "Sobel算子":
                    gray = cv2.cvtColor(processed, cv2.COLOR_BGR2GRAY)
                    sobelx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
                    sobely = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
                    edges = cv2.magnitude(sobelx, sobely)
                    edges = np.uint8(edges)
                    processed = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
                elif edge_type == "Laplacian算子":
                    gray = cv2.cvtColor(processed, cv2.COLOR_BGR2GRAY)
                    edges = cv2.Laplacian(gray, cv2.CV_64F)
                    edges = np.uint8(np.absolute(edges))
                    processed = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
            
            return processed
            
        except Exception as e:
            print(f"Error in advanced processing: {str(e)}")
            return image
