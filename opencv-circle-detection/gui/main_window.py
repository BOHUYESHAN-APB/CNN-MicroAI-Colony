import os
import logging
import numpy as np
import cv2
from pathlib import Path
from typing import Optional, Dict

from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                            QPushButton, QLabel, QFileDialog, QMessageBox,
                            QTreeView, QMenu, QInputDialog, QLineEdit,
                            QFileSystemModel)
from PySide6.QtCore import Qt, QSize, QDir
from PySide6.QtGui import QImage, QPixmap, QAction, QIcon

from .image_view import ImageViewer
from .report_view import ReportView
from core.detector import CircleDetector
from core.models import PetriDish, Colony

# 设置日志
logger = logging.getLogger(__name__)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # 初始化变量
        self.detector = CircleDetector()
        self.current_image = None
        self.current_dishes = []
        self.file_system_model = QFileSystemModel()
        self.current_language = "zh_CN"
        self.save_directory = str(Path.home())
        
        # 设置窗口属性
        self.setWindowTitle(self.tr("抑菌圈检测系统"))
        self.setMinimumSize(1200, 800)
        
        # 设置窗口图标
        icon_path = os.path.join(os.path.dirname(__file__), "icons", "app.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
            
        # 初始化UI
        self.init_ui()
        
    def init_ui(self):
        """初始化用户界面"""
        # 创建中央部件和主布局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        
        # 左侧资源管理器
        self.resource_explorer = QTreeView()
        self.resource_explorer.setModel(self.file_system_model)
        self.resource_explorer.setRootIndex(self.file_system_model.index(str(Path.cwd())))
        self.resource_explorer.setHeaderHidden(True)
        self.resource_explorer.setMaximumWidth(250)
        self.resource_explorer.clicked.connect(self.on_resource_clicked)
        
        # 中间部分（图像显示和控制按钮）
        middle_widget = QWidget()
        middle_layout = QVBoxLayout(middle_widget)
        
        # 控制按钮
        button_layout = QHBoxLayout()
        self.open_btn = QPushButton(self.tr("打开图像"))
        self.open_btn.clicked.connect(self.open_image)
        
        self.detect_btn = QPushButton(self.tr("开始检测"))
        self.detect_btn.clicked.connect(self.start_detection)
        self.detect_btn.setEnabled(False)
        
        self.save_btn = QPushButton(self.tr("保存结果"))
        self.save_btn.clicked.connect(self.save_results)
        self.save_btn.setEnabled(False)
        
        button_layout.addWidget(self.open_btn)
        button_layout.addWidget(self.detect_btn)
        button_layout.addWidget(self.save_btn)
        button_layout.addStretch()
        
        # 图像查看器
        self.image_viewer = ImageViewer()
        
        middle_layout.addLayout(button_layout)
        middle_layout.addWidget(self.image_viewer)
        
        # 右侧报告面板
        self.report_view = ReportView()
        self.report_view.setMaximumWidth(350)
        
        # 添加所有部件到主布局
        main_layout.addWidget(self.resource_explorer)
        main_layout.addWidget(middle_widget, stretch=1)
        main_layout.addWidget(self.report_view)
        
        # 设置菜单栏
        self.create_menus()
        
        # 设置状态栏
        self.statusBar().showMessage(self.tr("就绪"))
        
    def create_menus(self):
        """创建菜单栏"""
        # 文件菜单
        file_menu = self.menuBar().addMenu(self.tr("文件"))
        
        open_action = QAction(self.tr("打开图像"), self)
        open_action.triggered.connect(self.open_image)
        file_menu.addAction(open_action)
        
        save_dir_action = QAction(self.tr("设置保存目录"), self)
        save_dir_action.triggered.connect(self.set_save_directory)
        file_menu.addAction(save_dir_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction(self.tr("退出"), self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 编辑菜单
        edit_menu = self.menuBar().addMenu(self.tr("编辑"))
        
        add_label_action = QAction(self.tr("添加标注"), self)
        add_label_action.triggered.connect(self.add_annotation)
        edit_menu.addAction(add_label_action)
        
        # 语言菜单
        language_menu = self.menuBar().addMenu(self.tr("语言"))
        
        chinese_action = QAction("中文", self)
        chinese_action.triggered.connect(lambda: self.change_language("zh_CN"))
        language_menu.addAction(chinese_action)
        
        english_action = QAction("English", self)
        english_action.triggered.connect(lambda: self.change_language("en"))
        language_menu.addAction(english_action)
    
    def show_image(self, image: np.ndarray):
        """显示OpenCV图像"""
        # BGR转RGB
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        
        # 创建QImage
        bytes_per_line = ch * w
        qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
        
        # 在查看器中显示
        self.image_viewer.set_image(qt_image)
        self.statusBar().showMessage(self.tr("图像已加载"))

    def start_detection(self):
        """开始检测并分析"""
        try:
            # 执行检测
            self.current_dishes = self.detector.detect_petri_dishes(self.current_image)
            
            # 存储分析报告
            all_reports = []
            
            for i, dish in enumerate(self.current_dishes, 1):
                # 检测菌落
                colonies = self.detector.detect_colonies_in_dish(self.current_image, dish)
                dish.colonies = colonies
                
                # 检测抑菌圈
                for colony in colonies:
                    gray = cv2.cvtColor(self.current_image, cv2.COLOR_BGR2GRAY)
                    self.detector.detect_inhibition_zone(gray, colony, dish)
                
                # 生成该培养皿的分析报告
                dish_report = f"\n===== {self.tr('培养皿')} {i} =====\n"
                dish_report += self.detector._generate_analysis_report(dish)
                all_reports.append(dish_report)
            
            # 显示结果图像
            result_image = self.detector.draw_results(self.current_image, self.current_dishes)
            self.show_image(result_image)
            
            # 更新分析报告
            full_report = "\n".join(all_reports)
            self.report_view.set_report(full_report)
            
            # 启用保存按钮
            self.save_btn.setEnabled(True)
            
            # 显示检测完成消息
            QMessageBox.information(
                self,
                self.tr("检测完成"),
                self.tr("检测到 {0} 个培养皿\n共 {1} 个菌落").format(
                    len(self.current_dishes),
                    sum(len(d.colonies) for d in self.current_dishes)
                )
            )
            
            self.statusBar().showMessage(self.tr("检测完成"))
            
        except Exception as e:
            QMessageBox.critical(
                self,
                self.tr("错误"),
                self.tr("检测失败：{0}").format(str(e))
            )
            
    def open_image(self):
        """打开图像文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            self.tr("选择图像"),
            self.save_directory,
            self.tr("图像文件 (*.png *.jpg *.jpeg *.bmp);;所有文件 (*.*)")
        )
        
        if file_path:
            try:
                # 读取图像
                self.current_image = cv2.imread(file_path)
                if self.current_image is None:
                    raise Exception(self.tr("无法读取图像文件"))
                
                # 显示图像
                self.show_image(self.current_image)
                
                # 更新按钮状态
                self.detect_btn.setEnabled(True)
                self.save_btn.setEnabled(False)
                
                # 清空报告
                self.report_view.clear()
                
                # 更新资源管理器位置
                file_path = Path(file_path)
                self.save_directory = str(file_path.parent)
                self.file_system_model.setRootPath(self.save_directory)
                self.resource_explorer.setRootIndex(
                    self.file_system_model.index(self.save_directory)
                )
                
            except Exception as e:
                QMessageBox.critical(
                    self,
                    self.tr("错误"),
                    self.tr("打开图像失败：{0}").format(str(e))
                )

    def on_resource_clicked(self, index):
        """处理资源管理器点击事件"""
        file_path = self.file_system_model.filePath(index)
        if Path(file_path).suffix.lower() in ['.png', '.jpg', '.jpeg', '.bmp']:
            try:
                self.current_image = cv2.imread(file_path)
                if self.current_image is None:
                    raise Exception(self.tr("无法读取图像文件"))
                    
                self.show_image(self.current_image)
                self.detect_btn.setEnabled(True)
                self.save_btn.setEnabled(False)
                self.report_view.clear()
                
            except Exception as e:
                QMessageBox.critical(
                    self,
                    self.tr("错误"),
                    self.tr("打开图像失败：{0}").format(str(e))
                )

    def set_save_directory(self):
        """设置保存目录"""
        directory = QFileDialog.getExistingDirectory(
            self,
            self.tr("选择保存目录"),
            self.save_directory,
            QFileDialog.ShowDirsOnly
        )
        
        if directory:
            self.save_directory = directory
            self.statusBar().showMessage(
                self.tr("已设置保存目录：{0}").format(directory)
            )

    def add_annotation(self):
        """添加标注"""
        if not self.current_image is None and not self.current_dishes is None:
            text, ok = QInputDialog.getText(
                self,
                self.tr("添加标注"),
                self.tr("请输入标注文本："),
                QLineEdit.Normal
            )
            
            if ok and text:
                self.image_viewer.add_annotation(text)
                self.statusBar().showMessage(self.tr("已添加标注"))

    def change_language(self, lang: str):
        """切换语言"""
        if lang == self.current_language:
            return
            
        self.current_language = lang
        
        # 更新界面文本
        self.setWindowTitle(self.tr("抑菌圈检测系统"))
        self.open_btn.setText(self.tr("打开图像"))
        self.detect_btn.setText(self.tr("开始检测"))
        self.save_btn.setText(self.tr("保存结果"))
        
        # 更新状态栏
        self.statusBar().showMessage(
            self.tr("已切换语言到：{0}").format(
                "中文" if lang == "zh_CN" else "English"
            )
        )

    def save_results(self):
        """保存检测结果和分析报告"""
        if not self.current_dishes:
            return
            
        try:
            filename_prefix, ok = QInputDialog.getText(
                self,
                self.tr("保存结果"),
                self.tr("请输入文件名前缀："),
                QLineEdit.Normal,
                "result"
            )
            
            if not ok or not filename_prefix:
                return
            
            save_dir = Path(self.save_directory)
            
            # 保存原始图像
            cv2.imwrite(str(save_dir / f"{filename_prefix}_original.png"), self.current_image)
            
            # 保存标注后的结果图像
            result_image = self.detector.draw_results(self.current_image, self.current_dishes)
            cv2.imwrite(str(save_dir / f"{filename_prefix}_result.png"), result_image)
            
            # 为每个培养皿生成单独的结果图像
            for i, dish in enumerate(self.current_dishes, 1):
                # 裁剪培养皿区域
                x, y = dish.center
                r = int(dish.radius * 1.2)  # 略大于培养皿半径
                x1, y1 = max(0, x-r), max(0, y-r)
                x2, y2 = min(result_image.shape[1], x+r), min(result_image.shape[0], y+r)
                dish_image = result_image[y1:y2, x1:x2]
                cv2.imwrite(str(save_dir / f"{filename_prefix}_dish_{i}.png"), dish_image)
            
            # 保存文本报告
            with open(save_dir / f"{filename_prefix}_report.txt", "w", encoding="utf-8") as f:
                for i, dish in enumerate(self.current_dishes, 1):
                    f.write(f"\n===== {self.tr('培养皿')} {i} =====\n")
                    f.write(self.detector._generate_analysis_report(dish))
            
            QMessageBox.information(
                self,
                self.tr("成功"),
                self.tr(
                    "已保存:\n"
                    "- 原始图像\n"
                    "- 分析结果图像\n"
                    "- {0}个培养皿的单独图像\n"
                    "- 详细分析报告"
                ).format(len(self.current_dishes))
            )
            
            self.statusBar().showMessage(self.tr("结果已保存"))
            
        except Exception as e:
            QMessageBox.critical(
                self,
                self.tr("错误"),
                self.tr("保存失败：{0}").format(str(e))
            )