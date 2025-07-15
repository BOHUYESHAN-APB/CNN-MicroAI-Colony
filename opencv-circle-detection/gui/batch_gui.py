"""
独立的批量处理GUI界面
支持多张图像的批量抑菌圈检测
"""
import os
import sys
import cv2
import numpy as np
import logging
from pathlib import Path
from datetime import datetime
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QFileDialog, QMessageBox, 
                             QSplitter, QGroupBox, QComboBox, QSpinBox,
                             QDoubleSpinBox, QCheckBox, QProgressBar, QTextEdit,
                             QTabWidget, QTableWidget, QTableWidgetItem,
                             QListWidget, QListWidgetItem, QApplication)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QPixmap, QImage, QPainter, QPen, QColor, QFont

logger = logging.getLogger(__name__)

# 简化检测器类（直接内嵌）
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

class BatchDetectionWorker(QThread):
    """批量检测工作线程"""
    progress_updated = pyqtSignal(int, str)  # 进度, 当前文件
    single_finished = pyqtSignal(str, dict)  # 文件名, 结果
    batch_finished = pyqtSignal(list)  # 所有结果
    error_occurred = pyqtSignal(str, str)  # 文件名, 错误信息
    
    def __init__(self, image_paths, params):
        super().__init__()
        self.image_paths = image_paths
        self.params = params
        self.should_stop = False
        
    def stop(self):
        """停止处理"""
        self.should_stop = True
        
    def run(self):
        """执行批量检测"""
        try:
            results = []
            total_files = len(self.image_paths)
            
            for i, image_path in enumerate(self.image_paths):
                if self.should_stop:
                    break
                    
                # 更新进度
                progress = int((i / total_files) * 100)
                filename = os.path.basename(image_path)
                self.progress_updated.emit(progress, filename)
                
                try:
                    # 检测单张图像
                    result = self.process_single_image(image_path)
                    if result:
                        results.append(result)
                        self.single_finished.emit(filename, result)
                    
                except Exception as e:
                    self.error_occurred.emit(filename, str(e))
                    logger.error(f"处理 {filename} 时出错: {e}")
                    continue
            
            # 完成所有处理
            self.progress_updated.emit(100, "批量处理完成")
            self.batch_finished.emit(results)
            
        except Exception as e:
            self.error_occurred.emit("批量处理", f"批量处理过程出错: {str(e)}")
    
    def process_single_image(self, image_path):
        """处理单张图像"""
        # 读取图像
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError("无法读取图像文件")
        
        # 创建检测器
        detector = SimpleDetector(self.params['plate_diameter'])
        
        # 检测培养皿
        dish = detector.detect_petri_dish(image)
        if not dish:
            raise ValueError("未检测到培养皿")
        
        # 检测抑菌物质
        substances = detector.detect_substances(image, dish, self.params['substance_type'])
        
        # 检测抑菌圈
        zones = detector.detect_zones(image, substances)
        
        # 返回结果
        return {
            'image_path': image_path,
            'filename': os.path.basename(image_path),
            'image': image,
            'dish': dish,
            'substances': substances,
            'zones': zones,
            'px_per_mm': detector.px_per_mm,
            'substance_count': len(substances),
            'zone_count': len(zones)
        }

class BatchProcessingGUI(QMainWindow):
    """批量处理GUI主界面"""
    
    def __init__(self):
        super().__init__()
        self.image_paths = []
        self.batch_worker = None
        self.batch_results = []
        self.output_directory = None
        
        self.init_ui()
        self.apply_dark_theme()
        
    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("抑菌圈检测系统 - 批量处理")
        self.setMinimumSize(1000, 700)
        
        # 创建中央组件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QVBoxLayout(central_widget)
        
        # 创建分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)
        
        # 左侧控制面板
        self.create_control_panel(splitter)
        
        # 右侧结果显示
        self.create_results_panel(splitter)
        
        # 设置分割器比例
        splitter.setSizes([400, 600])
        
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
        
        # 文件选择区域
        file_group = QGroupBox("文件选择")
        file_layout = QVBoxLayout(file_group)
        
        # 按钮行
        btn_layout = QHBoxLayout()
        
        self.add_files_btn = QPushButton("添加图像文件")
        self.add_files_btn.clicked.connect(self.add_files)
        btn_layout.addWidget(self.add_files_btn)
        
        self.add_folder_btn = QPushButton("添加文件夹")
        self.add_folder_btn.clicked.connect(self.add_folder)
        btn_layout.addWidget(self.add_folder_btn)
        
        file_layout.addLayout(btn_layout)
        
        btn_layout2 = QHBoxLayout()
        
        self.clear_files_btn = QPushButton("清空列表")
        self.clear_files_btn.clicked.connect(self.clear_files)
        btn_layout2.addWidget(self.clear_files_btn)
        
        self.remove_selected_btn = QPushButton("移除选中")
        self.remove_selected_btn.clicked.connect(self.remove_selected)
        btn_layout2.addWidget(self.remove_selected_btn)
        
        file_layout.addLayout(btn_layout2)
        
        # 文件列表
        self.file_list = QListWidget()
        self.file_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        file_layout.addWidget(self.file_list)
        
        self.file_count_label = QLabel("待处理文件: 0 个")
        file_layout.addWidget(self.file_count_label)
        
        control_layout.addWidget(file_group)
        
        # 参数设置区域
        params_group = QGroupBox("批量处理参数")
        params_layout = QVBoxLayout(params_group)
        
        # 参数设置
        param_row1 = QHBoxLayout()
        param_row1.addWidget(QLabel("培养皿直径(mm):"))
        self.plate_diameter_spin = QSpinBox()
        self.plate_diameter_spin.setRange(50, 150)
        self.plate_diameter_spin.setValue(90)
        param_row1.addWidget(self.plate_diameter_spin)
        params_layout.addLayout(param_row1)
        
        param_row2 = QHBoxLayout()
        param_row2.addWidget(QLabel("物质类型:"))
        self.substance_combo = QComboBox()
        self.substance_combo.addItems(["auto", "filter_paper", "hole"])
        param_row2.addWidget(self.substance_combo)
        params_layout.addLayout(param_row2)
        
        # 输出设置
        output_layout = QHBoxLayout()
        output_layout.addWidget(QLabel("输出目录:"))
        
        self.output_path_label = QLabel("未选择")
        self.output_path_label.setStyleSheet("border: 1px solid #505050; padding: 4px;")
        output_layout.addWidget(self.output_path_label)
        
        self.select_output_btn = QPushButton("选择")
        self.select_output_btn.clicked.connect(self.select_output_directory)
        output_layout.addWidget(self.select_output_btn)
        
        params_layout.addLayout(output_layout)
        
        # 处理选项
        options_layout = QVBoxLayout()
        
        self.save_images_cb = QCheckBox("保存标注图像")
        self.save_images_cb.setChecked(True)
        options_layout.addWidget(self.save_images_cb)
        
        self.save_data_cb = QCheckBox("保存检测数据")
        self.save_data_cb.setChecked(True)
        options_layout.addWidget(self.save_data_cb)
        
        self.generate_report_cb = QCheckBox("生成汇总报告")
        self.generate_report_cb.setChecked(True)
        options_layout.addWidget(self.generate_report_cb)
        
        params_layout.addLayout(options_layout)
        
        control_layout.addWidget(params_group)
        
        # 控制按钮区域
        control_group = QGroupBox("批量处理控制")
        control_btn_layout = QVBoxLayout(control_group)
        
        btn_control_layout = QHBoxLayout()
        
        self.start_batch_btn = QPushButton("开始批量处理")
        self.start_batch_btn.clicked.connect(self.start_batch_processing)
        self.start_batch_btn.setEnabled(False)
        btn_control_layout.addWidget(self.start_batch_btn)
        
        self.stop_batch_btn = QPushButton("停止处理")
        self.stop_batch_btn.clicked.connect(self.stop_batch_processing)
        self.stop_batch_btn.setEnabled(False)
        btn_control_layout.addWidget(self.stop_batch_btn)
        
        control_btn_layout.addLayout(btn_control_layout)
        
        # 进度显示
        self.progress_label = QLabel("就绪")
        control_btn_layout.addWidget(self.progress_label)
        
        control_layout.addWidget(control_group)
        
        parent.addWidget(control_widget)
        
    def create_results_panel(self, parent):
        """创建结果显示面板"""
        results_widget = QWidget()
        results_layout = QVBoxLayout(results_widget)
        
        # 结果表格
        self.results_table = QTableWidget()
        self.setup_results_table()
        results_layout.addWidget(self.results_table)
        
        # 统计信息
        self.stats_label = QLabel("处理统计: 等待开始...")
        results_layout.addWidget(self.stats_label)
        
        parent.addWidget(results_widget)
        
    def setup_results_table(self):
        """设置结果表格"""
        headers = ["文件名", "培养皿", "物质数量", "抑菌圈数量", "标定比例", "状态"]
        self.results_table.setColumnCount(len(headers))
        self.results_table.setHorizontalHeaderLabels(headers)
        
        # 设置列宽
        self.results_table.setColumnWidth(0, 200)  # 文件名
        self.results_table.setColumnWidth(1, 100)  # 培养皿
        self.results_table.setColumnWidth(2, 80)   # 物质数量
        self.results_table.setColumnWidth(3, 80)   # 抑菌圈数量
        self.results_table.setColumnWidth(4, 100)  # 标定比例
        self.results_table.setColumnWidth(5, 80)   # 状态
        
    def add_files(self):
        """添加图像文件"""
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, "选择图像文件", "",
            "图像文件 (*.jpg *.jpeg *.png *.bmp *.tiff);;所有文件 (*)"
        )
        
        if file_paths:
            for file_path in file_paths:
                if file_path not in self.image_paths:
                    self.image_paths.append(file_path)
                    item = QListWidgetItem(os.path.basename(file_path))
                    item.setToolTip(file_path)
                    self.file_list.addItem(item)
            
            self.update_file_count()
            
    def add_folder(self):
        """添加文件夹中的所有图像"""
        folder_path = QFileDialog.getExistingDirectory(self, "选择图像文件夹")
        
        if folder_path:
            image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif'}
            folder = Path(folder_path)
            
            added_count = 0
            for file_path in folder.iterdir():
                if file_path.is_file() and file_path.suffix.lower() in image_extensions:
                    file_path_str = str(file_path)
                    if file_path_str not in self.image_paths:
                        self.image_paths.append(file_path_str)
                        item = QListWidgetItem(file_path.name)
                        item.setToolTip(file_path_str)
                        self.file_list.addItem(item)
                        added_count += 1
            
            if added_count > 0:
                self.update_file_count()
                QMessageBox.information(self, "添加完成", f"成功添加 {added_count} 个图像文件")
            else:
                QMessageBox.warning(self, "未找到文件", "选择的文件夹中没有找到支持的图像文件")
                
    def clear_files(self):
        """清空文件列表"""
        self.image_paths.clear()
        self.file_list.clear()
        self.update_file_count()
        
    def remove_selected(self):
        """移除选中的文件"""
        selected_items = self.file_list.selectedItems()
        for item in selected_items:
            row = self.file_list.row(item)
            if 0 <= row < len(self.image_paths):
                self.image_paths.pop(row)
            self.file_list.takeItem(row)
        
        self.update_file_count()
        
    def update_file_count(self):
        """更新文件计数"""
        count = len(self.image_paths)
        self.file_count_label.setText(f"待处理文件: {count} 个")
        self.start_batch_btn.setEnabled(count > 0 and self.output_directory is not None)
        
    def select_output_directory(self):
        """选择输出目录"""
        directory = QFileDialog.getExistingDirectory(self, "选择输出目录")
        
        if directory:
            self.output_directory = directory
            self.output_path_label.setText(os.path.basename(directory))
            self.output_path_label.setToolTip(directory)
            self.start_batch_btn.setEnabled(len(self.image_paths) > 0)
            
    def start_batch_processing(self):
        """开始批量处理"""
        if not self.image_paths:
            QMessageBox.warning(self, "警告", "请先添加要处理的图像文件")
            return
            
        if not self.output_directory:
            QMessageBox.warning(self, "警告", "请先选择输出目录")
            return
        
        # 准备参数
        params = {
            'plate_diameter': self.plate_diameter_spin.value(),
            'substance_type': self.substance_combo.currentText()
        }
        
        # 清空之前的结果
        self.batch_results.clear()
        self.results_table.setRowCount(0)
        
        # 禁用控制按钮
        self.start_batch_btn.setEnabled(False)
        self.stop_batch_btn.setEnabled(True)
        
        # 重置进度
        self.progress_bar.show()
        self.progress_bar.setValue(0)
        self.progress_label.setText("开始批量处理...")
        
        # 创建工作线程
        self.batch_worker = BatchDetectionWorker(self.image_paths, params)
        self.batch_worker.progress_updated.connect(self.on_progress_updated)
        self.batch_worker.single_finished.connect(self.on_single_finished)
        self.batch_worker.batch_finished.connect(self.on_batch_finished)
        self.batch_worker.error_occurred.connect(self.on_error_occurred)
        self.batch_worker.start()
        
    def stop_batch_processing(self):
        """停止批量处理"""
        if self.batch_worker and self.batch_worker.isRunning():
            self.batch_worker.stop()
            self.batch_worker.wait(3000)  # 等待3秒
            
        self.start_batch_btn.setEnabled(True)
        self.stop_batch_btn.setEnabled(False)
        self.progress_bar.hide()
        self.progress_label.setText("处理已停止")
        
    def on_progress_updated(self, progress, filename):
        """进度更新回调"""
        self.progress_bar.setValue(progress)
        self.progress_label.setText(f"正在处理: {filename}")
        
    def on_single_finished(self, filename, result):
        """单个文件处理完成回调"""
        self.batch_results.append(result)
        
        # 添加到结果表格
        row = self.results_table.rowCount()
        self.results_table.insertRow(row)
        
        self.results_table.setItem(row, 0, QTableWidgetItem(filename))
        
        dish_info = f"R={result['dish']['radius']}px" if result['dish'] else "未检测到"
        self.results_table.setItem(row, 1, QTableWidgetItem(dish_info))
        
        self.results_table.setItem(row, 2, QTableWidgetItem(str(result['substance_count'])))
        self.results_table.setItem(row, 3, QTableWidgetItem(str(result['zone_count'])))
        
        px_per_mm = f"{result['px_per_mm']:.2f}" if result['px_per_mm'] else "未标定"
        self.results_table.setItem(row, 4, QTableWidgetItem(px_per_mm))
        
        self.results_table.setItem(row, 5, QTableWidgetItem("完成"))
        
        # 保存结果文件
        self.save_single_result(result)
        
    def on_error_occurred(self, filename, error_msg):
        """错误处理回调"""
        logger.error(f"处理 {filename} 出错: {error_msg}")
        
        # 添加错误记录到表格
        row = self.results_table.rowCount()
        self.results_table.insertRow(row)
        
        self.results_table.setItem(row, 0, QTableWidgetItem(filename))
        self.results_table.setItem(row, 1, QTableWidgetItem("错误"))
        self.results_table.setItem(row, 2, QTableWidgetItem("-"))
        self.results_table.setItem(row, 3, QTableWidgetItem("-"))
        self.results_table.setItem(row, 4, QTableWidgetItem("-"))
        self.results_table.setItem(row, 5, QTableWidgetItem(f"错误: {error_msg}"))
        
    def on_batch_finished(self, results):
        """批量处理完成回调"""
        self.start_batch_btn.setEnabled(True)
        self.stop_batch_btn.setEnabled(False)
        self.progress_bar.hide()
        
        # 更新统计信息
        total_files = len(self.image_paths)
        success_count = len(results)
        error_count = total_files - success_count
        
        stats_text = f"处理统计: 总计 {total_files} 个文件，成功 {success_count} 个，失败 {error_count} 个"
        self.stats_label.setText(stats_text)
        
        # 生成汇总报告
        if self.generate_report_cb.isChecked() and results:
            self.generate_summary_report(results)
        
        self.progress_label.setText("批量处理完成")
        QMessageBox.information(self, "处理完成", stats_text)
        
    def save_single_result(self, result):
        """保存单个结果"""
        try:
            base_name = os.path.splitext(result['filename'])[0]
            
            # 保存标注图像
            if self.save_images_cb.isChecked():
                # 绘制检测结果
                display_image = result['image'].copy()
                self.draw_detection_results(display_image, result)
                
                # 保存图像
                image_path = os.path.join(self.output_directory, f"{base_name}_result.jpg")
                cv2.imwrite(image_path, display_image)
            
            # 保存检测数据
            if self.save_data_cb.isChecked():
                data_path = os.path.join(self.output_directory, f"{base_name}_data.txt")
                self.save_detection_data(result, data_path)
                
        except Exception as e:
            logger.error(f"保存结果失败: {e}")
            
    def draw_detection_results(self, image, result):
        """在图像上绘制检测结果"""
        # 绘制培养皿
        dish = result['dish']
        if dish:
            cv2.circle(image, dish['center'], dish['radius'], (0, 255, 0), 3)
        
        # 绘制抑菌物质
        substances = result['substances']
        colors = [(255, 0, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255), (0, 255, 255)]
        
        for i, substance in enumerate(substances):
            color = colors[i % len(colors)]
            cv2.circle(image, substance['center'], substance['radius'], color, 2)
            cv2.circle(image, substance['center'], 3, color, -1)
        
        # 绘制抑菌圈
        zones = result['zones']
        for zone in zones:
            cv2.circle(image, zone['center'], zone['radius'], (0, 255, 255), 2)
            
    def save_detection_data(self, result, file_path):
        """保存检测数据到文件"""
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write("=== 检测结果数据 ===\n\n")
            f.write(f"文件名: {result['filename']}\n")
            f.write(f"图像路径: {result['image_path']}\n\n")
            
            # 培养皿信息
            dish = result['dish']
            if dish:
                f.write(f"培养皿:\n")
                f.write(f"  中心: {dish['center']}\n")
                f.write(f"  半径: {dish['radius']} px\n\n")
            
            # 标定信息
            if result['px_per_mm']:
                f.write(f"标定比例: {result['px_per_mm']:.2f} px/mm\n\n")
            
            # 抑菌物质
            substances = result['substances']
            f.write(f"抑菌物质 ({len(substances)} 个):\n")
            for i, substance in enumerate(substances):
                f.write(f"  #{i+1}: 中心{substance['center']}, 半径{substance['radius']}px, 类型{substance['type']}\n")
            
            # 抑菌圈
            zones = result['zones']
            f.write(f"\n抑菌圈 ({len(zones)} 个):\n")
            for i, zone in enumerate(zones):
                f.write(f"  #{i+1}: 中心{zone['center']}, 半径{zone['radius']}px, 直径{zone['diameter_mm']:.2f}mm\n")
                
    def generate_summary_report(self, results):
        """生成汇总报告"""
        try:
            report_path = os.path.join(self.output_directory, "batch_summary_report.txt")
            
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write("=== 批量处理汇总报告 ===\n\n")
                f.write(f"处理时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"总文件数: {len(results)}\n\n")
                
                # 统计信息
                total_substances = sum(r['substance_count'] for r in results)
                total_zones = sum(r['zone_count'] for r in results)
                
                f.write("统计汇总:\n")
                f.write(f"  检测到的抑菌物质总数: {total_substances}\n")
                f.write(f"  检测到的抑菌圈总数: {total_zones}\n")
                f.write(f"  平均每张图像的物质数: {total_substances/len(results):.1f}\n")
                f.write(f"  平均每张图像的抑菌圈数: {total_zones/len(results):.1f}\n\n")
                
                # 详细列表
                f.write("详细结果:\n")
                f.write("-" * 80 + "\n")
                for result in results:
                    f.write(f"文件: {result['filename']}\n")
                    f.write(f"  物质数量: {result['substance_count']}\n")
                    f.write(f"  抑菌圈数量: {result['zone_count']}\n")
                    if result['px_per_mm']:
                        f.write(f"  标定比例: {result['px_per_mm']:.2f} px/mm\n")
                    f.write("\n")
                
            logger.info(f"汇总报告已保存到: {report_path}")
            
        except Exception as e:
            logger.error(f"生成汇总报告失败: {e}")
            
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
            QTableWidget, QListWidget {
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
    app.setApplicationName("抑菌圈检测系统 - 批量处理")
    
    # 设置日志
    logging.basicConfig(level=logging.INFO)
    
    window = BatchProcessingGUI()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()