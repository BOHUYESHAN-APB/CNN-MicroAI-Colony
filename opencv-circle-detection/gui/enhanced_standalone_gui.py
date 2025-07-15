"""
增强版独立GUI界面
集成批量处理功能的完整抑菌圈检测系统
"""
import os
import sys
import cv2
import numpy as np
import logging
from pathlib import Path
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QFileDialog, QMessageBox, 
                             QSplitter, QGroupBox, QComboBox, QSpinBox,
                             QDoubleSpinBox, QCheckBox, QProgressBar, QTextEdit,
                             QTabWidget, QTableWidget, QTableWidgetItem,
                             QScrollArea, QFrame, QSlider, QApplication)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QPixmap, QImage, QPainter, QPen, QColor, QFont

# 导入批量处理组件
from .batch_processing_widget import BatchProcessingWidget
from .standalone_gui import (SimpleDetector, SimpleDetectionWorker, 
                           ImageDisplayWidget, StandaloneCircleDetectionGUI)

logger = logging.getLogger(__name__)

class EnhancedCircleDetectionGUI(StandaloneCircleDetectionGUI):
    """增强版抑菌圈检测GUI界面，包含批量处理功能"""
    
    def __init__(self):
        # 调用父类初始化但不直接运行
        QMainWindow.__init__(self)
        self.current_image_path = None
        self.detection_worker = None
        self.current_results = None
        
        self.init_enhanced_ui()
        self.apply_dark_theme()
        
    def init_enhanced_ui(self):
        """初始化增强版用户界面"""
        self.setWindowTitle("抑菌圈检测系统 - 完整版")
        self.setMinimumSize(1200, 800)
        
        # 创建中央组件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QVBoxLayout(central_widget)
        
        # 创建主标签页
        self.main_tab_widget = QTabWidget()
        main_layout.addWidget(self.main_tab_widget)
        
        # 单张图像处理标签页
        single_tab = QWidget()
        self.setup_single_processing_tab(single_tab)
        self.main_tab_widget.addTab(single_tab, "单张图像处理")
        
        # 批量处理标签页
        batch_tab = BatchProcessingWidget()
        self.main_tab_widget.addTab(batch_tab, "批量处理")
        
        # 创建状态栏
        self.statusBar().showMessage("就绪")
        
        # 创建进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.hide()
        self.statusBar().addPermanentWidget(self.progress_bar)
        
    def setup_single_processing_tab(self, tab_widget):
        """设置单张图像处理标签页"""
        tab_layout = QHBoxLayout(tab_widget)
        
        # 创建分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)
        tab_layout.addWidget(splitter)
        
        # 左侧控制面板
        self.create_control_panel(splitter)
        
        # 右侧图像显示区域
        self.create_image_area(splitter)
        
        # 设置分割器比例
        splitter.setSizes([300, 900])
        
    def create_control_panel(self, parent):
        """创建控制面板（继承自父类但稍作修改）"""
        control_widget = QWidget()
        control_layout = QVBoxLayout(control_widget)
        
        # 文件操作组
        file_group = QGroupBox("文件操作")
        file_layout = QVBoxLayout(file_group)
        
        self.open_btn = QPushButton("打开图像")
        self.open_btn.clicked.connect(self.open_image)
        file_layout.addWidget(self.open_btn)
        
        self.save_btn = QPushButton("保存结果")
        self.save_btn.clicked.connect(self.save_results)
        self.save_btn.setEnabled(False)
        file_layout.addWidget(self.save_btn)
        
        control_layout.addWidget(file_group)
        
        # 参数设置组
        params_group = QGroupBox("参数设置")
        params_layout = QVBoxLayout(params_group)
        
        # 培养皿直径
        params_layout.addWidget(QLabel("培养皿直径(mm):"))
        self.plate_diameter_spin = QDoubleSpinBox()
        self.plate_diameter_spin.setRange(50, 150)
        self.plate_diameter_spin.setValue(90)
        self.plate_diameter_spin.setSuffix(" mm")
        params_layout.addWidget(self.plate_diameter_spin)
        
        # 物质类型
        params_layout.addWidget(QLabel("抑菌物质类型:"))
        self.substance_combo = QComboBox()
        self.substance_combo.addItems(["auto", "filter_paper", "hole"])
        params_layout.addWidget(self.substance_combo)
        
        control_layout.addWidget(params_group)
        
        # 检测控制组
        detection_group = QGroupBox("检测控制")
        detection_layout = QVBoxLayout(detection_group)
        
        self.detect_btn = QPushButton("开始检测")
        self.detect_btn.clicked.connect(self.start_detection)
        self.detect_btn.setEnabled(False)
        detection_layout.addWidget(self.detect_btn)
        
        self.clear_btn = QPushButton("清除结果")
        self.clear_btn.clicked.connect(self.clear_results)
        self.clear_btn.setEnabled(False)
        detection_layout.addWidget(self.clear_btn)
        
        control_layout.addWidget(detection_group)
        
        # 快速切换组
        switch_group = QGroupBox("快速功能")
        switch_layout = QVBoxLayout(switch_group)
        
        self.batch_mode_btn = QPushButton("切换到批量处理")
        self.batch_mode_btn.clicked.connect(self.switch_to_batch_mode)
        switch_layout.addWidget(self.batch_mode_btn)
        
        control_layout.addWidget(switch_group)
        
        # 添加弹性空间
        control_layout.addStretch()
        
        parent.addWidget(control_widget)
        
    def create_image_area(self, parent):
        """创建图像显示区域（继承自父类）"""
        image_widget = QWidget()
        image_layout = QVBoxLayout(image_widget)
        
        # 创建标签页
        self.tab_widget = QTabWidget()
        
        # 图像显示标签页
        image_tab = QWidget()
        image_tab_layout = QVBoxLayout(image_tab)
        
        # 图像显示组件
        self.image_display = ImageDisplayWidget()
        scroll_area = QScrollArea()
        scroll_area.setWidget(self.image_display)
        scroll_area.setWidgetResizable(True)
        image_tab_layout.addWidget(scroll_area)
        
        self.tab_widget.addTab(image_tab, "检测结果")
        
        # 结果统计标签页
        results_tab = QWidget()
        results_layout = QVBoxLayout(results_tab)
        
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        results_layout.addWidget(self.results_text)
        
        self.tab_widget.addTab(results_tab, "结果统计")
        
        # 详细数据标签页
        details_tab = QWidget()
        details_layout = QVBoxLayout(details_tab)
        
        self.details_table = QTableWidget()
        details_layout.addWidget(self.details_table)
        
        self.tab_widget.addTab(details_tab, "详细数据")
        
        image_layout.addWidget(self.tab_widget)
        
        parent.addWidget(image_widget)
        
    def switch_to_batch_mode(self):
        """切换到批量处理模式"""
        self.main_tab_widget.setCurrentIndex(1)  # 切换到批量处理标签页
        self.statusBar().showMessage("已切换到批量处理模式")
        
    def apply_dark_theme(self):
        """应用增强版暗色主题"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #505050;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 5px;
                color: #ffffff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QPushButton {
                background-color: #3c3c3c;
                color: #ffffff;
                border: 1px solid #505050;
                padding: 8px;
                border-radius: 4px;
                font-size: 12px;
                min-height: 20px;
            }
            QPushButton:hover {
                background-color: #505050;
            }
            QPushButton:pressed {
                background-color: #404040;
            }
            QPushButton:disabled {
                background-color: #2d2d2d;
                color: #808080;
            }
            QLabel {
                color: #ffffff;
                font-size: 12px;
            }
            QComboBox, QSpinBox, QDoubleSpinBox {
                background-color: #3c3c3c;
                color: #ffffff;
                border: 1px solid #505050;
                padding: 4px;
                border-radius: 2px;
            }
            QTabWidget::pane {
                border: 1px solid #505050;
                background-color: #2b2b2b;
            }
            QTabBar::tab {
                background-color: #3c3c3c;
                color: #ffffff;
                padding: 8px 16px;
                border: 1px solid #505050;
                border-bottom: none;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #505050;
            }
            QTextEdit, QTableWidget, QListWidget {
                background-color: #3c3c3c;
                color: #ffffff;
                border: 1px solid #505050;
                selection-background-color: #6d6d6d;
            }
            QHeaderView::section {
                background-color: #505050;
                color: #ffffff;
                padding: 4px;
                border: 1px solid #6d6d6d;
            }
            QProgressBar {
                border: 1px solid #505050;
                border-radius: 2px;
                text-align: center;
                color: #ffffff;
                background-color: #3c3c3c;
            }
            QProgressBar::chunk {
                background-color: #0078d4;
                border-radius: 1px;
            }
            QStatusBar {
                background-color: #1e1e1e;
                color: #ffffff;
                border-top: 1px solid #505050;
            }
            QCheckBox {
                color: #ffffff;
                spacing: 5px;
            }
            QCheckBox::indicator {
                width: 15px;
                height: 15px;
            }
            QCheckBox::indicator:unchecked {
                border: 1px solid #505050;
                background-color: #3c3c3c;
            }
            QCheckBox::indicator:checked {
                border: 1px solid #0078d4;
                background-color: #0078d4;
            }
        """)

def main():
    """主函数"""
    app = QApplication(sys.argv)
    app.setApplicationName("抑菌圈检测系统 - 完整版")
    
    # 设置日志
    logging.basicConfig(level=logging.INFO)
    
    window = EnhancedCircleDetectionGUI()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()