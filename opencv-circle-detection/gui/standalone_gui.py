"""
独立的抑菌圈检测GUI界面
不依赖复杂的检测器模块，直接使用基础OpenCV功能
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

logger = logging.getLogger(__name__)

class SimpleDetector:
    """简化的检测器，直接使用OpenCV"""
    
    def __init__(self, plate_diameter_mm=90.0):
        self.plate_diameter_mm = plate_diameter_mm
        self.px_per_mm = None
        
    def detect_petri_dish(self, image):
        """检测培养皿"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (9, 9), 2)
        
        circles = cv2.HoughCircles(
            blurred,
            cv2.HOUGH_GRADIENT,
            dp=1,
            minDist=400,
            param1=50,
            param2=35,
            minRadius=int(image.shape[0]/3),
            maxRadius=int(image.shape[0]/1.8)
        )
        
        if circles is not None:
            circles = np.uint16(np.around(circles))
            x, y, r = circles[0, 0]
            self.px_per_mm = r * 2 / self.plate_diameter_mm
            return {'center': (int(x), int(y)), 'radius': int(r)}
        return None
        
    def detect_substances(self, image, dish, substance_type='auto'):
        """检测抑菌物质"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # 创建培养皿掩码
        mask = np.zeros(gray.shape[:2], dtype=np.uint8)
        cv2.circle(mask, dish['center'], int(dish['radius'] * 0.9), 255, -1)
        masked = cv2.bitwise_and(gray, gray, mask=mask)
        
        substances = []
        
        if substance_type in ['auto', 'filter_paper']:
            # 检测滤纸片（亮区域）
            _, thresh = cv2.threshold(masked, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                area = cv2.contourArea(contour)
                if 50 < area < 5000:  # 合理的面积范围
                    (x, y), radius = cv2.minEnclosingCircle(contour)
                    center = (int(x), int(y))
                    radius = int(radius)
                    
                    # 检查是否在培养皿内
                    dist = np.sqrt((center[0] - dish['center'][0])**2 + (center[1] - dish['center'][1])**2)
                    if dist + radius < dish['radius'] * 0.8:
                        substances.append({
                            'center': center,
                            'radius': radius,
                            'type': 'filter_paper'
                        })
        
        if substance_type in ['auto', 'hole'] and len(substances) == 0:
            # 检测挖孔（暗区域）
            _, thresh = cv2.threshold(masked, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                area = cv2.contourArea(contour)
                if 30 < area < 3000:  # 合理的面积范围
                    (x, y), radius = cv2.minEnclosingCircle(contour)
                    center = (int(x), int(y))
                    radius = int(radius)
                    
                    # 检查是否在培养皿内
                    dist = np.sqrt((center[0] - dish['center'][0])**2 + (center[1] - dish['center'][1])**2)
                    if dist + radius < dish['radius'] * 0.8:
                        substances.append({
                            'center': center,
                            'radius': radius,
                            'type': 'hole'
                        })
        
        return substances
        
    def detect_zones(self, image, substances):
        """简单的抑菌圈检测"""
        zones = []
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        for substance in substances:
            # 在物质周围搜索抑菌圈
            x, y = substance['center']
            search_radius = substance['radius'] * 4
            
            # 提取ROI
            x1 = max(0, x - search_radius)
            y1 = max(0, y - search_radius)
            x2 = min(gray.shape[1], x + search_radius)
            y2 = min(gray.shape[0], y + search_radius)
            
            roi = gray[y1:y2, x1:x2]
            if roi.size == 0:
                continue
                
            # 二值化
            _, binary = cv2.threshold(roi, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # 形态学操作
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
            binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
            
            # 查找轮廓
            contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                area = cv2.contourArea(contour)
                if area > substance['radius'] * substance['radius'] * 3:  # 比物质大
                    (cx, cy), radius = cv2.minEnclosingCircle(contour)
                    
                    # 转换回原图坐标
                    abs_center = (int(cx + x1), int(cy + y1))
                    abs_radius = int(radius)
                    
                    # 计算直径
                    diameter_mm = 0
                    if self.px_per_mm:
                        diameter_mm = (abs_radius * 2) / self.px_per_mm
                    
                    zones.append({
                        'center': abs_center,
                        'radius': abs_radius,
                        'diameter_mm': diameter_mm,
                        'substance': substance
                    })
                    break  # 只取第一个找到的抑菌圈
        
        return zones

class SimpleDetectionWorker(QThread):
    """简化的检测工作线程"""
    progress_updated = pyqtSignal(int)
    detection_finished = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, image_path, params):
        super().__init__()
        self.image_path = image_path
        self.params = params
        
    def run(self):
        try:
            self.progress_updated.emit(10)
            
            # 读取图像
            image = cv2.imread(self.image_path)
            if image is None:
                self.error_occurred.emit("无法读取图像文件")
                return
                
            self.progress_updated.emit(30)
            
            # 创建检测器
            detector = SimpleDetector(self.params['plate_diameter'])
            
            # 检测培养皿
            dish = detector.detect_petri_dish(image)
            if not dish:
                self.error_occurred.emit("未检测到培养皿")
                return
                
            self.progress_updated.emit(60)
            
            # 检测抑菌物质
            substances = detector.detect_substances(image, dish, self.params['substance_type'])
            
            self.progress_updated.emit(80)
            
            # 检测抑菌圈
            zones = detector.detect_zones(image, substances)
            
            self.progress_updated.emit(100)
            
            # 返回结果
            result = {
                'image': image,
                'dish': dish,
                'substances': substances,
                'zones': zones,
                'px_per_mm': detector.px_per_mm
            }
            
            self.detection_finished.emit(result)
            
        except Exception as e:
            self.error_occurred.emit(f"检测过程出错: {str(e)}")

class ImageDisplayWidget(QLabel):
    """图像显示组件"""
    
    def __init__(self):
        super().__init__()
        self.setMinimumSize(400, 400)
        self.setStyleSheet("border: 1px solid #505050; background-color: #1e1e1e;")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setText("点击打开图像")
        self.setScaledContents(False)
        
        self.original_image = None
        self.display_image = None
        self.results = None
        
    def load_image(self, image_path):
        """加载图像"""
        self.original_image = cv2.imread(image_path)
        if self.original_image is not None:
            self.display_image = self.original_image.copy()
            self.update_display()
            return True
        return False
        
    def set_results(self, results):
        """设置检测结果"""
        self.results = results
        if self.original_image is not None:
            self.display_image = self.original_image.copy()
            self.draw_results()
            self.update_display()
            
    def draw_results(self):
        """绘制检测结果"""
        if not self.results:
            return
            
        # 绘制培养皿
        dish = self.results.get('dish')
        if dish:
            cv2.circle(self.display_image, dish['center'], dish['radius'], (0, 255, 0), 3)
            cv2.putText(self.display_image, f"Petri Dish R={dish['radius']}px", 
                       (dish['center'][0]-80, dish['center'][1]-dish['radius']-10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        # 绘制抑菌物质
        substances = self.results.get('substances', [])
        colors = [(255, 0, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255), (0, 255, 255)]
        
        for i, substance in enumerate(substances):
            color = colors[i % len(colors)]
            center = substance['center']
            radius = substance['radius']
            
            cv2.circle(self.display_image, center, radius, color, 2)
            cv2.circle(self.display_image, center, 3, color, -1)
            
            # 添加标签
            label = f"#{i+1} {substance['type']}"
            cv2.putText(self.display_image, label,
                       (center[0]+radius+5, center[1]),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        
        # 绘制抑菌圈
        zones = self.results.get('zones', [])
        for i, zone in enumerate(zones):
            cv2.circle(self.display_image, zone['center'], zone['radius'], (0, 255, 255), 2)
            cv2.putText(self.display_image, f"Zone {zone['diameter_mm']:.1f}mm",
                       (zone['center'][0]-40, zone['center'][1]+zone['radius']+20),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)
    
    def update_display(self):
        """更新显示"""
        if self.display_image is not None:
            # 转换为RGB
            rgb_image = cv2.cvtColor(self.display_image, cv2.COLOR_BGR2RGB)
            
            # 缩放以适应显示区域
            h, w, ch = rgb_image.shape
            widget_size = self.size()
            
            # 计算缩放比例
            scale_w = widget_size.width() / w
            scale_h = widget_size.height() / h
            scale = min(scale_w, scale_h, 1.0)  # 不放大
            
            new_w = int(w * scale)
            new_h = int(h * scale)
            
            resized = cv2.resize(rgb_image, (new_w, new_h))
            
            # 转换为QImage
            bytes_per_line = 3 * new_w
            q_image = QImage(resized.data, new_w, new_h, bytes_per_line, QImage.Format.Format_RGB888)
            
            # 设置为QLabel
            pixmap = QPixmap.fromImage(q_image)
            self.setPixmap(pixmap)

class StandaloneCircleDetectionGUI(QMainWindow):
    """独立的抑菌圈检测GUI界面"""
    
    def __init__(self):
        super().__init__()
        self.current_image_path = None
        self.detection_worker = None
        self.current_results = None
        
        self.init_ui()
        self.apply_dark_theme()
        
    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("抑菌圈检测系统 - 简化版")
        self.setMinimumSize(1000, 700)
        
        # 创建中央组件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QHBoxLayout(central_widget)
        
        # 创建分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)
        
        # 左侧控制面板
        self.create_control_panel(splitter)
        
        # 右侧图像显示区域
        self.create_image_area(splitter)
        
        # 设置分割器比例
        splitter.setSizes([300, 700])
        
        # 创建状态栏
        self.statusBar().showMessage("就绪")
        
        # 创建进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.hide()
        self.statusBar().addPermanentWidget(self.progress_bar)
        
    def create_control_panel(self, parent):
        """创建控制面板"""
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
        
        # 添加弹性空间
        control_layout.addStretch()
        
        parent.addWidget(control_widget)
        
    def create_image_area(self, parent):
        """创建图像显示区域"""
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
        
        image_layout.addWidget(self.tab_widget)
        
        parent.addWidget(image_widget)
        
    def apply_dark_theme(self):
        """应用暗色主题"""
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
            }
            QTabBar::tab:selected {
                background-color: #505050;
            }
            QTextEdit {
                background-color: #3c3c3c;
                color: #ffffff;
                border: 1px solid #505050;
            }
            QProgressBar {
                border: 1px solid #505050;
                border-radius: 2px;
                text-align: center;
                color: #ffffff;
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
        """)
        
    def open_image(self):
        """打开图像文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择图像文件", "", 
            "图像文件 (*.jpg *.jpeg *.png *.bmp *.tiff);;所有文件 (*)"
        )
        
        if file_path:
            if self.image_display.load_image(file_path):
                self.current_image_path = file_path
                self.detect_btn.setEnabled(True)
                self.statusBar().showMessage(f"已加载图像: {os.path.basename(file_path)}")
                self.clear_results()
            else:
                QMessageBox.critical(self, "错误", "无法加载图像文件")
                
    def start_detection(self):
        """开始检测"""
        if not self.current_image_path:
            QMessageBox.warning(self, "警告", "请先打开图像文件")
            return
            
        # 准备参数
        params = {
            'plate_diameter': self.plate_diameter_spin.value(),
            'substance_type': self.substance_combo.currentText()
        }
        
        # 禁用按钮
        self.detect_btn.setEnabled(False)
        self.open_btn.setEnabled(False)
        
        # 显示进度条
        self.progress_bar.show()
        self.progress_bar.setValue(0)
        
        # 创建工作线程
        self.detection_worker = SimpleDetectionWorker(self.current_image_path, params)
        self.detection_worker.progress_updated.connect(self.progress_bar.setValue)
        self.detection_worker.detection_finished.connect(self.on_detection_finished)
        self.detection_worker.error_occurred.connect(self.on_detection_error)
        self.detection_worker.start()
        
        self.statusBar().showMessage("正在检测...")
        
    def on_detection_finished(self, results):
        """检测完成回调"""
        self.current_results = results
        
        # 显示结果
        self.image_display.set_results(results)
        self.update_results_text(results)
        
        # 恢复按钮状态
        self.detect_btn.setEnabled(True)
        self.open_btn.setEnabled(True)
        self.save_btn.setEnabled(True)
        self.clear_btn.setEnabled(True)
        
        # 隐藏进度条
        self.progress_bar.hide()
        
        # 更新状态栏
        substances = results.get('substances', [])
        zones = results.get('zones', [])
        self.statusBar().showMessage(f"检测完成 - {len(substances)} 个抑菌物质，{len(zones)} 个抑菌圈")
        
    def on_detection_error(self, error_msg):
        """检测错误回调"""
        QMessageBox.critical(self, "检测错误", error_msg)
        
        # 恢复按钮状态
        self.detect_btn.setEnabled(True)
        self.open_btn.setEnabled(True)
        
        # 隐藏进度条
        self.progress_bar.hide()
        
        self.statusBar().showMessage("检测失败")
        
    def update_results_text(self, results):
        """更新结果文本"""
        text = "=== 检测结果统计 ===\n\n"
        
        # 培养皿信息
        dish = results.get('dish')
        if dish:
            text += f"培养皿信息:\n"
            text += f"  中心坐标: {dish['center']}\n"
            text += f"  半径: {dish['radius']} px\n\n"
        
        # 标定信息
        px_per_mm = results.get('px_per_mm')
        if px_per_mm:
            text += f"标定比例: {px_per_mm:.2f} px/mm\n\n"
        
        # 抑菌物质信息
        substances = results.get('substances', [])
        text += f"抑菌物质 ({len(substances)} 个):\n"
        for i, substance in enumerate(substances):
            text += f"  #{i+1}: 中心{substance['center']}, 半径{substance['radius']}px, 类型{substance['type']}\n"
        
        text += "\n"
        
        # 抑菌圈信息
        zones = results.get('zones', [])
        text += f"抑菌圈 ({len(zones)} 个):\n"
        for i, zone in enumerate(zones):
            text += f"  #{i+1}: 中心{zone['center']}, 半径{zone['radius']}px, 直径{zone['diameter_mm']:.2f}mm\n"
        
        self.results_text.setText(text)
        
    def clear_results(self):
        """清除结果"""
        self.current_results = None
        if hasattr(self.image_display, 'results'):
            self.image_display.results = None
            if self.image_display.original_image is not None:
                self.image_display.display_image = self.image_display.original_image.copy()
                self.image_display.update_display()
        
        self.results_text.clear()
        self.save_btn.setEnabled(False)
        self.clear_btn.setEnabled(False)
        
        self.statusBar().showMessage("已清除检测结果")
        
    def save_results(self):
        """保存结果"""
        if not self.current_results:
            QMessageBox.warning(self, "警告", "没有可保存的结果")
            return
            
        # 选择保存目录
        save_dir = QFileDialog.getExistingDirectory(self, "选择保存目录")
        if not save_dir:
            return
            
        try:
            base_name = os.path.splitext(os.path.basename(self.current_image_path))[0]
            
            # 保存结果图像
            result_image_path = os.path.join(save_dir, f"{base_name}_result.jpg")
            cv2.imwrite(result_image_path, self.image_display.display_image)
            
            # 保存结果数据
            result_text_path = os.path.join(save_dir, f"{base_name}_data.txt")
            with open(result_text_path, 'w', encoding='utf-8') as f:
                f.write(self.results_text.toPlainText())
            
            QMessageBox.information(self, "保存成功", f"结果已保存到:\n{save_dir}")
            self.statusBar().showMessage("结果保存成功")
            
        except Exception as e:
            QMessageBox.critical(self, "保存失败", f"保存过程中出错:\n{str(e)}")

def main():
    """主函数"""
    app = QApplication(sys.argv)
    app.setApplicationName("抑菌圈检测系统 - 简化版")
    
    # 设置日志
    logging.basicConfig(level=logging.INFO)
    
    window = StandaloneCircleDetectionGUI()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()