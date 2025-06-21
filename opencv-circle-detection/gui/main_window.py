import os
import numpy as np
import cv2
from pathlib import Path
from typing import Optional, Dict

from utils.logger import get_logger

from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                            QPushButton, QLabel, QFileDialog, QMessageBox,
                            QTreeView, QMenu, QInputDialog, QLineEdit,
                            QFileSystemModel)
from PySide6.QtCore import Qt, QSize, QDir
from PySide6.QtGui import QImage, QPixmap, QAction, QIcon

from .image_view import ImageViewer
from .report_view import ReportView
from core.detector import CircleDetector
# PetriDish and Colony are now primarily for data structure, not direct detector output handling
from core.models import PetriDish, Colony, SubstanceTypeEnum

# 获取日志记录器
logger = get_logger(__name__)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # 初始化变量
        self.detector = CircleDetector()
        self.original_image: Optional[np.ndarray] = None # Store the original loaded image
        self.processed_image: Optional[np.ndarray] = None # Store image with detection overlays
        self.detection_results: List[Dict] = [] # Store the list of dicts from process_image_pipeline
        self.detection_extra_info: Dict = {} # Store the extra_info dict

        self.file_system_model = QFileSystemModel()
        self.current_language = "zh_CN"
        self.save_directory = str(Path.home() / "MicroAI_Colony_Results" / "InhibitionZone")
        Path(self.save_directory).mkdir(parents=True, exist_ok=True)


        # 设置窗口属性
        self.setWindowTitle(self.tr("抑菌圈检测系统"))
        self.setMinimumSize(1200, 800)

        # 设置窗口图标
        # Assuming icons are in a subdirectory 'icons' relative to this script's location
        # A more robust way might be to use Qt's resource system (qrc)
        try:
            script_dir = Path(__file__).parent
            icon_path = script_dir / "icons" / "app_icon.png" # Placeholder name
            if icon_path.exists():
                self.setWindowIcon(QIcon(str(icon_path)))
            else:
                logger.warning(f"应用图标未找到: {icon_path}")
        except Exception as e:
            logger.error(f"加载应用图标失败: {e}")

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
        # Set initial root to a sensible default, e.g., user's Pictures or Documents directory
        initial_resource_path = str(Path.home() / "Pictures")
        if not Path(initial_resource_path).exists():
            initial_resource_path = str(Path.home())
        self.file_system_model.setRootPath(initial_resource_path)
        self.resource_explorer.setRootIndex(self.file_system_model.index(initial_resource_path))
        self.resource_explorer.setHeaderHidden(True) # Keep header hidden for cleaner look
        self.resource_explorer.setColumnHidden(1, True) # Hide size
        self.resource_explorer.setColumnHidden(2, True) # Hide type
        self.resource_explorer.setColumnHidden(3, True) # Hide date modified
        self.resource_explorer.setMaximumWidth(300) # Increased width slightly
        self.resource_explorer.clicked.connect(self.on_resource_clicked)

        # 中间部分（图像显示和控制按钮）
        middle_widget = QWidget()
        middle_layout = QVBoxLayout(middle_widget)

        # 控制按钮
        button_layout = QHBoxLayout()
        self.open_btn = QPushButton(self.tr("打开图像"))
        self.open_btn.setIcon(QIcon.fromTheme("document-open", QIcon(":/icons/open.png"))) # Example with theme icon
        self.open_btn.clicked.connect(self.open_image)

        self.detect_btn = QPushButton(self.tr("开始检测"))
        self.detect_btn.setIcon(QIcon.fromTheme("system-search", QIcon(":/icons/detect.png")))
        self.detect_btn.clicked.connect(self.start_detection)
        self.detect_btn.setEnabled(False)

        self.save_btn = QPushButton(self.tr("保存结果"))
        self.save_btn.setIcon(QIcon.fromTheme("document-save", QIcon(":/icons/save.png")))
        self.save_btn.clicked.connect(self.save_results)
        self.save_btn.setEnabled(False)

        button_layout.addWidget(self.open_btn)
        button_layout.addWidget(self.detect_btn)
        button_layout.addWidget(self.save_btn)
        button_layout.addStretch()

        # 图像查看器
        self.image_viewer = ImageViewer() # Assuming ImageViewer can handle QPixmap or QImage

        middle_layout.addLayout(button_layout)
        middle_layout.addWidget(self.image_viewer, stretch=1) # Allow image viewer to stretch

        # 右侧报告面板
        self.report_view = ReportView() # Assuming ReportView is appropriately defined
        self.report_view.setMinimumWidth(300) # Ensure report view has enough space
        self.report_view.setMaximumWidth(450)


        # 添加所有部件到主布局
        main_layout.addWidget(self.resource_explorer)
        main_layout.addWidget(middle_widget, stretch=2) # Give middle part more stretch factor
        main_layout.addWidget(self.report_view, stretch=1)

        # 设置菜单栏
        self.create_menus()

        # 设置状态栏
        self.statusBar().showMessage(self.tr("就绪"))

    def create_menus(self):
        """创建菜单栏"""
        # 文件菜单
        file_menu = self.menuBar().addMenu(self.tr("&文件")) # Added ampersand for mnemonic

        open_action = QAction(QIcon.fromTheme("document-open"), self.tr("打开图像 (&O)"), self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.open_image)
        file_menu.addAction(open_action)

        save_action = QAction(QIcon.fromTheme("document-save"), self.tr("保存结果 (&S)"), self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_results)
        save_action.setEnabled(False) # Initially disabled
        self.save_action_menu = save_action # Keep a reference to enable/disable
        file_menu.addAction(save_action)
        
        save_dir_action = QAction(self.tr("设置保存目录..."), self)
        save_dir_action.triggered.connect(self.set_save_directory)
        file_menu.addAction(save_dir_action)

        file_menu.addSeparator()

        exit_action = QAction(QIcon.fromTheme("application-exit"), self.tr("退出 (&X)"), self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # 编辑菜单 (Placeholder, can be expanded)
        edit_menu = self.menuBar().addMenu(self.tr("&编辑"))
        # Example: add_label_action = QAction(self.tr("添加标注..."), self)
        # add_label_action.triggered.connect(self.add_annotation) # self.add_annotation needs to be implemented
        # edit_menu.addAction(add_label_action)


        # 图像处理菜单 (Placeholder, can be expanded)
        # process_menu = self.menuBar().addMenu(self.tr("&图像处理"))
        # enhance_contrast_action = QAction(self.tr("增强对比度"), self)
        # enhance_contrast_action.triggered.connect(self.enhance_contrast) # self.enhance_contrast needs to be implemented
        # process_menu.addAction(enhance_contrast_action)

        # 帮助菜单
        help_menu = self.menuBar().addMenu(self.tr("&帮助"))
        about_action = QAction(self.tr("关于..."), self)
        about_action.triggered.connect(self.show_about_dialog)
        help_menu.addAction(about_action)


    def show_image(self, image_array: Optional[np.ndarray]):
        """显示OpenCV图像 (numpy array)"""
        if image_array is None:
            self.image_viewer.clear_image() # Assuming ImageViewer has a clear method
            self.statusBar().showMessage(self.tr("无图像显示"))
            return

        try:
            # BGR转RGB for display
            if len(image_array.shape) == 3 and image_array.shape[2] == 3:
                display_image = cv2.cvtColor(image_array, cv2.COLOR_BGR2RGB)
            elif len(image_array.shape) == 2: # Grayscale
                display_image = cv2.cvtColor(image_array, cv2.COLOR_GRAY2RGB)
            else:
                logger.error(f"不支持的图像格式进行显示: shape={image_array.shape}")
                self.image_viewer.clear_image()
                return

            h, w, ch = display_image.shape
            bytes_per_line = ch * w
            qt_image = QImage(display_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
            
            self.image_viewer.set_image(QPixmap.fromImage(qt_image)) # ImageViewer uses QPixmap
            self.statusBar().showMessage(self.tr("图像已加载并显示"))
        except Exception as e:
            logger.error(f"显示图像时出错: {e}", exc_info=True)
            QMessageBox.critical(self, self.tr("图像显示错误"), str(e))
            self.image_viewer.clear_image()


    def start_detection(self):
        """开始检测并分析"""
        if self.original_image is None:
            logger.error("没有加载图像用于检测")
            QMessageBox.warning(self, self.tr("警告"), self.tr("请先加载图像!"))
            return

        logger.info("开始执行抑菌圈检测流程...")
        self.statusBar().showMessage(self.tr("正在检测中，请稍候..."))
        QApplication.setOverrideCursor(Qt.WaitCursor) # Set busy cursor

        try:
            # 使用新的 pipeline 方法
            # The detector instance is self.detector
            processed_img_array, results_list, extra_info_dict = \
                self.detector.process_image_pipeline(self.original_image.copy())

            self.processed_image = processed_img_array
            self.detection_results = results_list
            self.detection_extra_info = extra_info_dict
            
            # 显示处理后的图像
            self.show_image(self.processed_image)

            # 更新报告视图 (假设 ReportView 有一个 update_report 方法)
            # You might need to adapt this call based on ReportView's actual interface
            if hasattr(self.report_view, 'update_report_data'):
                 self.report_view.update_report_data(self.detection_results, self.detection_extra_info)
            else:
                 logger.warning("ReportView 没有 update_report_data 方法。报告可能未更新。")


            self.save_btn.setEnabled(True)
            if hasattr(self, 'save_action_menu'): self.save_action_menu.setEnabled(True)


            # 构建并显示摘要信息
            num_dishes = extra_info_dict.get('petri_dishes_detected', 0)
            num_substances = extra_info_dict.get('substances_detected_total', 0)
            num_zones = extra_info_dict.get('inhibition_zones_detected_total', 0)
            px_per_mm = extra_info_dict.get('px_per_mm', 'N/A')
            if isinstance(px_per_mm, float): px_per_mm = f"{px_per_mm:.2f}"


            summary_msg = self.tr(
                "检测完成!\n\n"
                "检测到培养皿: {num_dishes}\n"
                "检测到抑菌物质点: {num_substances}\n"
                "检测到抑菌圈: {num_zones}\n"
                "像素/毫米 比例: {px_per_mm}"
            ).format(num_dishes=num_dishes, num_substances=num_substances, num_zones=num_zones, px_per_mm=px_per_mm)
            
            # 详细的培养皿信息 (如果存在)
            active_dish_details = extra_info_dict.get('active_dish_details', [])
            if active_dish_details:
                summary_msg += "\n\n" + self.tr("各培养皿详情:")
                for i, dish_detail in enumerate(active_dish_details):
                    dish_info = dish_detail.get('dish_info', {})
                    mode = dish_detail.get('detection_mode', 'N/A')
                    s_type = dish_detail.get('substance_type', 'N/A')
                    s_count = dish_detail.get('substances_count', 0)
                    z_results = dish_detail.get('zones_results', [])
                    zones_found_in_dish = sum(1 for zr in z_results if zr.get('primary_zone'))

                    summary_msg += self.tr(
                        "\n  培养皿 {idx}: 中心({cx},{cy}) R={r_px}px | 模式: {mode} | 类型: {s_type} | 物质点: {s_count} | 抑菌圈: {z_found}"
                    ).format(
                        idx=i+1,
                        cx=dish_info.get('center', ('?','?'))[0], cy=dish_info.get('center', ('?','?'))[1],
                        r_px=dish_info.get('radius', '?'),
                        mode=mode, s_type=s_type, s_count=s_count, z_found=zones_found_in_dish
                    )


            QMessageBox.information(self, self.tr("检测结果摘要"), summary_msg)
            self.statusBar().showMessage(self.tr("检测完成! 结果已显示。"))
            logger.info("抑菌圈检测流程成功完成。")

        except Exception as e:
            error_msg = str(e)
            logger.error(f"检测过程中发生严重错误: {error_msg}", exc_info=True)
            QMessageBox.critical(
                self,
                self.tr("检测错误"),
                self.tr("在检测过程中发生错误：\n{0}\n\n请查看日志获取详细信息。").format(error_msg)
            )
            self.statusBar().showMessage(self.tr("检测失败!"))
        finally:
            QApplication.restoreOverrideCursor() # Restore normal cursor


    def open_image(self):
        """打开图像文件"""
        # Use a more specific starting directory for the file dialog
        start_dir = self.save_directory # Default to current save directory
        if self.resource_explorer.currentIndex().isValid():
            current_explorer_path = self.file_system_model.filePath(self.resource_explorer.currentIndex())
            if Path(current_explorer_path).is_dir():
                start_dir = current_explorer_path
            else:
                start_dir = str(Path(current_explorer_path).parent)


        file_path, _ = QFileDialog.getOpenFileName(
            self,
            self.tr("选择一个图像文件"),
            start_dir, # Start in the directory of the currently selected item or its parent
            self.tr("图像文件 (*.png *.jpg *.jpeg *.bmp *.tif *.tiff);;所有文件 (*.*)")
        )

        if file_path:
            self.load_image_from_path(file_path)


    def load_image_from_path(self, file_path_str: str):
        """Loads an image from the given file path and updates the UI."""
        try:
            logger.info(f"尝试从路径加载图像: {file_path_str}")
            # 使用 OpenCV 读取图像，确保能处理中文路径
            # cv2.imdecode 可以从内存buffer读取，更可靠处理特殊字符路径
            img_bytes = np.fromfile(file_path_str, dtype=np.uint8)
            self.original_image = cv2.imdecode(img_bytes, cv2.IMREAD_COLOR)

            if self.original_image is None:
                raise ValueError(self.tr("无法使用OpenCV解码图像文件。文件可能已损坏或格式不受支持。"))

            self.processed_image = None # Clear previous processed image
            self.detection_results = []
            self.detection_extra_info = {}

            self.show_image(self.original_image.copy()) # Display a copy

            self.detect_btn.setEnabled(True)
            self.save_btn.setEnabled(False) # Disable save until detection is run
            if hasattr(self, 'save_action_menu'): self.save_action_menu.setEnabled(False)


            if hasattr(self.report_view, 'clear_report'):
                self.report_view.clear_report()
            else:
                logger.warning("ReportView 没有 clear_report 方法。")


            # Update resource explorer to show the directory of the opened file
            current_file_path = Path(file_path_str)
            parent_dir = str(current_file_path.parent)
            # self.file_system_model.setRootPath(parent_dir) # This might be too aggressive
            # Select the opened file in the tree view if it's visible
            self.resource_explorer.setCurrentIndex(self.file_system_model.index(file_path_str))
            # Ensure the selected item is visible
            self.resource_explorer.scrollTo(self.file_system_model.index(file_path_str), QTreeView.PositionAtCenter)


            self.setWindowTitle(f"{self.tr('抑菌圈检测系统')} - {current_file_path.name}")
            logger.info(f"图像 '{file_path_str}' 加载成功。")

        except Exception as e:
            logger.error(f"打开或加载图像失败 '{file_path_str}': {e}", exc_info=True)
            QMessageBox.critical(
                self,
                self.tr("打开图像错误"),
                self.tr("打开图像文件失败：\n{0}").format(str(e))
            )
            self.original_image = None
            self.show_image(None)
            self.detect_btn.setEnabled(False)
            self.setWindowTitle(self.tr("抑菌圈检测系统"))


    def on_resource_clicked(self, index):
        """处理资源管理器点击事件"""
        file_path_str = self.file_system_model.filePath(index)
        if self.file_system_model.isDir(index):
            # If it's a directory, maybe expand it or do nothing,
            # or set it as the root for the file dialog for "Open Image"
            pass
        elif Path(file_path_str).suffix.lower() in ['.png', '.jpg', '.jpeg', '.bmp', '.tif', '.tiff']:
            self.load_image_from_path(file_path_str)
        # else:
            # logger.debug(f"资源管理器点击了非图像文件: {file_path_str}")


    def set_save_directory(self):
        """设置默认保存目录"""
        directory = QFileDialog.getExistingDirectory(
            self,
            self.tr("选择默认保存目录"),
            self.save_directory, # Start from the current save directory
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
        )

        if directory:
            self.save_directory = directory
            Path(self.save_directory).mkdir(parents=True, exist_ok=True) # Ensure it exists
            self.statusBar().showMessage(self.tr("默认保存目录已更新为: {0}").format(directory))
            logger.info(f"用户设置保存目录为: {self.save_directory}")

    # Placeholder for add_annotation - requires more thought on how annotations are stored and displayed
    def add_annotation(self):
        if self.processed_image is None:
            QMessageBox.information(self, self.tr("提示"), self.tr("请先进行检测。"))
            return
        # Implementation would involve:
        # 1. Getting coordinates from ImageViewer (e.g., on click)
        # 2. Opening a dialog to input text
        # 3. Storing annotation (e.g., in self.detection_results or a separate list)
        # 4. Redrawing the image with the new annotation
        logger.warning("add_annotation 功能尚未完全实现。")
        QMessageBox.information(self, self.tr("功能提示"), self.tr("添加标注功能正在开发中。"))


    # Image processing functions (enhance_contrast, denoise_image, etc.)
    # should operate on self.original_image and update self.processed_image or a temporary display.
    # For now, these are placeholders.
    def _apply_image_processing(self, process_func, *args):
        if self.original_image is None:
            QMessageBox.warning(self, self.tr("警告"), self.tr("请先加载图像。"))
            return
        
        # It's better to apply processing on the original image if possible,
        # or allow chaining if that's the design.
        # For simplicity, let's assume we apply to original and show.
        # A more complex UI might have an "apply" button or non-destructive edits.
        
        target_image_for_processing = self.original_image.copy()
        # If a processed image exists, maybe ask user if they want to process original or current view
        # if self.processed_image is not None:
        #    reply = QMessageBox.question(self, "选择处理对象", "处理原始图像还是当前显示的图像？",
        #                                QMessageBox.Original | QMessageBox.CurrentView, QMessageBox.Original)
        #    if reply == QMessageBox.CurrentView:
        #        target_image_for_processing = self.processed_image.copy()


        logger.info(f"应用图像处理: {process_func.__name__}")
        self.statusBar().showMessage(self.tr("正在应用图像处理..."))
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            # Assuming processor functions take a BGR image and return a BGR image,
            # or take a gray image and return a gray image that we convert back.
            # This needs to align with ImageProcessor's methods.
            
            # Example: if processor expects gray and returns gray
            if len(target_image_for_processing.shape) == 3:
                 gray_image = cv2.cvtColor(target_image_for_processing, cv2.COLOR_BGR2GRAY)
            else:
                 gray_image = target_image_for_processing
            
            processed_gray = process_func(gray_image, *args)
            
            if len(processed_gray.shape) == 2: # If result is grayscale
                processed_bgr = cv2.cvtColor(processed_gray, cv2.COLOR_GRAY2BGR)
            else: # Assuming it's already BGR
                processed_bgr = processed_gray

            self.show_image(processed_bgr) # Show the processed image
            # Decide if self.original_image or self.processed_image should be updated
            # For now, just show, don't overwrite self.original_image
            # self.processed_image = processed_bgr # Or update this if it's for temporary view
            self.statusBar().showMessage(self.tr(f"{process_func.__name__} 应用完成。"))
            logger.info(f"{process_func.__name__} 应用成功。")
        except Exception as e:
            logger.error(f"应用图像处理 {process_func.__name__} 失败: {e}", exc_info=True)
            QMessageBox.critical(self, self.tr("处理错误"), str(e))
            self.statusBar().showMessage(self.tr("图像处理失败。"))
        finally:
            QApplication.restoreOverrideCursor()

    def enhance_contrast(self):
        self._apply_image_processing(self.detector.processor.enhance_contrast)

    def denoise_image(self):
        # Denoise might take a strength parameter, adjust if needed
        self._apply_image_processing(self.detector.processor.denoise, strength=1.0)

    def enhance_details(self):
        self._apply_image_processing(self.detector.processor.enhance_details)

    def remove_background(self):
        self._apply_image_processing(self.detector.processor.remove_background)


    def change_language(self, lang: str):
        """切换语言 (需要更完整的i18n集成)"""
        if lang == self.current_language:
            return
        
        logger.info(f"请求切换语言到: {lang} (当前: {self.current_language})")
        # This is a placeholder. Proper i18n requires a QTranslator.
        # For now, we just update some texts manually if we were to re-create menus.
        # A full solution involves loading .qm files and retranslating the UI.
        
        # self.current_language = lang
        # QMessageBox.information(self, self.tr("语言切换"),
        #                         self.tr("语言切换功能需要重启应用或更复杂的集成才能完全生效。部分文本可能不会立即更新。"))
        
        # # Example of manually updating some texts (not a complete solution)
        # self.setWindowTitle(self.tr("抑菌圈检测系统"))
        # self.open_btn.setText(self.tr("打开图像"))
        # self.detect_btn.setText(self.tr("开始检测"))
        # self.save_btn.setText(self.tr("保存结果"))
        # # ... and all menu actions, etc.
        # self.create_menus() # Recreate menus to apply tr() again (if tr is dynamic)
        
        # self.statusBar().showMessage(
        #     self.tr("语言已尝试切换到: {0}").format("中文" if lang == "zh_CN" else "English")
        # )
        QMessageBox.information(self, self.tr("提示"), self.tr("动态语言切换功能正在开发中。"))


    def save_results(self):
        """保存检测结果（图像和数据）"""
        if not self.detection_results and self.processed_image is None:
            QMessageBox.warning(self, self.tr("无结果"), self.tr("没有检测结果或处理后的图像可以保存。"))
            return

        # Suggest a filename based on the original image name
        original_filename = "untitled"
        if self.original_image is not None and hasattr(self, 'current_loaded_filepath'):
            original_filename = Path(self.current_loaded_filepath).stem

        default_savename_base = f"{original_filename}_analysis"
        
        # Use QFileDialog to get save path for the report and base name for images
        # We'll save multiple files (report.json, processed_image.png, original_image.png)
        
        # Let user choose a base name and directory
        file_dialog = QFileDialog(self, self.tr("保存分析结果"), self.save_directory)
        file_dialog.setAcceptMode(QFileDialog.AcceptSave)
        file_dialog.setDefaultSuffix("json") # For the report file
        file_dialog.setNameFilter(self.tr("JSON 报告 (*.json)"))
        file_dialog.selectFile(f"{default_savename_base}_report.json")

        if not file_dialog.exec():
            return # User cancelled

        report_save_path_str = file_dialog.selectedFiles()[0]
        report_save_path = Path(report_save_path_str)
        chosen_base_name = report_save_path.stem.replace("_report", "") # Get base name from user's choice
        chosen_dir = report_save_path.parent


        logger.info(f"准备保存结果到目录: {chosen_dir}，基础名称: {chosen_base_name}")
        self.statusBar().showMessage(self.tr("正在保存结果..."))
        QApplication.setOverrideCursor(Qt.WaitCursor)

        try:
            # 1. Save the processed image (if it exists)
            if self.processed_image is not None:
                processed_image_path = chosen_dir / f"{chosen_base_name}_processed.png"
                # Use imencode to handle potential path issues, then write bytes
                retval, buf = cv2.imencode(".png", self.processed_image)
                if retval:
                    with open(processed_image_path, 'wb') as f:
                        f.write(buf)
                    logger.info(f"处理后图像已保存到: {processed_image_path}")
                else:
                    logger.error(f"无法编码处理后的图像为PNG格式。")


            # 2. Save the original image (if it exists and is different from processed)
            if self.original_image is not None:
                original_image_path = chosen_dir / f"{chosen_base_name}_original.png"
                retval, buf = cv2.imencode(".png", self.original_image)
                if retval:
                     with open(original_image_path, 'wb') as f:
                        f.write(buf)
                     logger.info(f"原始图像已保存到: {original_image_path}")
                else:
                    logger.error(f"无法编码原始图像为PNG格式。")


            # 3. Save the detection data (JSON report)
            report_data_to_save = {
                "analysis_timestamp": datetime.datetime.now().isoformat(),
                "original_image_filename": Path(self.current_loaded_filepath).name if hasattr(self, 'current_loaded_filepath') else "N/A",
                "detector_settings": { # Placeholder for actual settings if configurable
                    "plate_diameter_mm": self.detector.plate_diameter_mm,
                    "filter_paper_diameter_mm": self.detector.filter_paper_diameter_mm,
                    "hole_diameter_mm": self.detector.hole_diameter_mm,
                },
                "detection_summary": self.detection_extra_info, # Contains counts, px_per_mm etc.
                "detailed_results": self.detection_results # List of dicts for each substance and its zone
            }

            with open(report_save_path, 'w', encoding='utf-8') as f:
                json.dump(report_data_to_save, f, indent=4, ensure_ascii=False, default=lambda o: str(o)) # Basic default for non-serializable
            logger.info(f"检测报告已保存到: {report_save_path}")

            QMessageBox.information(
                self,
                self.tr("保存成功"),
                self.tr("结果已成功保存到以下位置:\n目录: {0}\n报告: {1}").format(str(chosen_dir), report_save_path.name)
            )
            self.statusBar().showMessage(self.tr("结果保存成功!"))

        except Exception as e:
            logger.error(f"保存结果失败: {e}", exc_info=True)
            QMessageBox.critical(self, self.tr("保存失败"), str(e))
            self.statusBar().showMessage(self.tr("保存结果失败!"))
        finally:
            QApplication.restoreOverrideCursor()

    def show_about_dialog(self):
        """显示关于对话框"""
        QMessageBox.about(
            self,
            self.tr("关于抑菌圈检测系统"),
            self.tr(
                "<h3>抑菌圈自动检测与分析系统</h3>"
                "<p>版本: 0.2.0 (Alpha)</p>"
                "<p>基于 OpenCV 和 PySide6 开发。</p>"
                "<p>该软件用于辅助研究人员进行抑菌圈图像的自动识别和测量。</p>"
                "<p>&copy; 2024-2025 版权所有</p>" # Replace with actual copyright if any
            )
        )

    def closeEvent(self, event):
        """处理窗口关闭事件"""
        # Can add logic here to ask user to save unsaved changes, etc.
        # For now, just accept the event.
        logger.info("主窗口关闭。")
        event.accept()
# End of MainWindow class