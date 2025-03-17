"""
Results Dialog
结果对话框
"""
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                           QScrollArea, QWidget, QPushButton, QSplitter)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QPixmap, QImage
import logging

logger = logging.getLogger(__name__)

class ResultDialog(QDialog):
    """结果展示对话框"""
    
    def __init__(self, analysis_result, parent=None):
        super().__init__(parent)
        self.analysis_result = analysis_result
        self.init_ui()
        
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("分析结果")
        self.resize(1200, 800)  # 初始大小，但可以调整
        
        # 创建主布局
        layout = QHBoxLayout(self)
        
        # 创建分割器，允许用户调整左右两侧的大小
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 左侧：图像显示区域（可滚动）
        image_scroll = QScrollArea()
        image_scroll.setWidgetResizable(True)
        image_widget = QWidget()
        image_layout = QVBoxLayout(image_widget)
        
        # 加载并显示结果图像
        if "result_image" in self.analysis_result:
            pixmap = QPixmap(self.analysis_result["result_image"])
            if not pixmap.isNull():
                image_label = QLabel()
                # 保持纵横比缩放到合适大小
                scaled_pixmap = pixmap.scaled(800, 600, 
                                            Qt.AspectRatioMode.KeepAspectRatio,
                                            Qt.TransformationMode.SmoothTransformation)
                image_label.setPixmap(scaled_pixmap)
                image_layout.addWidget(image_label)
            else:
                logger.error("无法加载结果图像")
                image_layout.addWidget(QLabel("无法加载结果图像"))
        
        image_scroll.setWidget(image_widget)
        splitter.addWidget(image_scroll)
        
        # 右侧：信息显示区域
        info_widget = QWidget()
        info_layout = QVBoxLayout(info_widget)
        
        # 添加摘要信息
        if "summary" in self.analysis_result:
            summary_label = QLabel(self.analysis_result["summary"])
            summary_label.setStyleSheet("font-size: 12pt;")
            info_layout.addWidget(summary_label)
        
        # 添加更多详细信息
        details = [
            ("密度", f"{self.analysis_result.get('density', 0):.2f} colonies/mm²"),
            ("覆盖率", f"{self.analysis_result.get('area', 0):.2%}"),
            ("处理时间", f"{self.analysis_result.get('time', 0):.2f}秒"),
        ]
        
        for label, value in details:
            detail_widget = QWidget()
            detail_layout = QHBoxLayout(detail_widget)
            detail_layout.addWidget(QLabel(f"{label}:"))
            detail_layout.addWidget(QLabel(value))
            info_layout.addWidget(detail_widget)
        
        # 添加一个弹性空间
        info_layout.addStretch()
        
        # 添加关闭按钮
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.accept)
        info_layout.addWidget(close_btn)
        
        splitter.addWidget(info_widget)
        
        # 设置分割器的初始大小
        splitter.setSizes([800, 400])
        
        layout.addWidget(splitter)
        self.setLayout(layout)
