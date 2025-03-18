"""
Main Window implementation
主窗口实现
"""
import os
import logging
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                            QLabel, QTreeView, QFileDialog, QMessageBox,
                            QStatusBar, QMenu, QDockWidget, QPushButton)
from PyQt6.QtGui import QIcon, QAction, QImage, QPixmap
from PyQt6.QtCore import Qt

from ..utils.project_manager import ProjectManager
from ..models.colony_detector import create_model
from .project_dialog import NewProjectDialog, OpenProjectDialog
from .image_list_widget import ImageListWidget
from .image_viewer import ImageViewer
from .result_visualizer import ResultVisualizer
from .progress_dialog import ProgressDialog
from .preprocessing_dialog import PreprocessingDialog

logger = logging.getLogger(__name__)

DIALOG_STYLE = """
QPushButton {
    background-color: #3a3a3a;
    color: #e0e0e0;
    border: 1px solid #505050;
    border-radius: 4px;
    padding: 5px 15px;
    min-width: 80px;
}
QPushButton:hover {
    background-color: #454545;
}
QPushButton:pressed {
    background-color: #303030;
}
"""

class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.project_manager = ProjectManager()
        self.colony_detector = create_model("faster_rcnn")
        self.preprocess_config = self.config.get('preprocessing', {})
        self.setup_ui()
        
    def setup_ui(self):
        """Setup user interface"""
        self.setWindowTitle("菌落分析")
        self.resize(1200, 800)
        self.setStyleSheet(DIALOG_STYLE)
        
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        
        # Left panel - Image viewer
        viewer_panel = QWidget()
        viewer_layout = QVBoxLayout(viewer_panel)
        
        self.image_viewer = ImageViewer()
        viewer_layout.addWidget(self.image_viewer)
        
        # Analysis button
        analyze_btn = QPushButton("分析当前图像")
        analyze_btn.clicked.connect(self.start_analysis)
        analyze_btn.setToolTip("分析当前显示的图像")
        viewer_layout.addWidget(analyze_btn)
        
        layout.addWidget(viewer_panel, stretch=2)
        
        # Right panel
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # Image controls
        image_controls = QHBoxLayout()
        add_image_btn = QPushButton("添加图像")
        add_image_btn.clicked.connect(self.add_images)
        add_image_btn.setToolTip("将图像添加到当前项目")
        image_controls.addWidget(add_image_btn)
        right_layout.addLayout(image_controls)
        
        # Image list
        self.image_list = ImageListWidget()
        self.image_list.image_selected.connect(self.on_image_selected)
        right_layout.addWidget(self.image_list)
        
        # Results
        self.result_visualizer = ResultVisualizer()
        right_layout.addWidget(self.result_visualizer)
        
        layout.addWidget(right_panel, stretch=1)
        
        # Setup menus
        self.create_menus()
        
        # Status bar
        self.statusBar().showMessage("就绪")

    def create_menus(self):
        """Create menu bars"""
        # File menu
        file_menu = self.menuBar().addMenu("文件")
        
        new_project_action = file_menu.addAction("新建项目")
        new_project_action.triggered.connect(self.new_project)
        new_project_action.setToolTip("创建新的项目文件夹")
        
        open_project_action = file_menu.addAction("打开项目...")
        open_project_action.triggered.connect(self.open_project)
        open_project_action.setToolTip("打开已有的项目文件夹")
        
        file_menu.addSeparator()
        
        add_images_action = file_menu.addAction("添加图像...")
        add_images_action.triggered.connect(self.add_images)
        add_images_action.setToolTip("向当前项目添加图像文件")
        
        file_menu.addSeparator()
        
        exit_action = file_menu.addAction("退出")
        exit_action.triggered.connect(self.close)
        
        # Analysis menu
        analysis_menu = self.menuBar().addMenu("分析")
        
        preprocess_action = analysis_menu.addAction("预处理设置...")
        preprocess_action.triggered.connect(self.show_preprocessing_settings)
        preprocess_action.setToolTip("配置图像预处理参数")
        
        analysis_menu.addSeparator()
        
        analyze_action = analysis_menu.addAction("分析当前图像")
        analyze_action.triggered.connect(self.start_analysis)
        analyze_action.setToolTip("分析当前显示的图像")
        
        batch_action = analysis_menu.addAction("批量分析...")
        batch_action.triggered.connect(self.start_batch_analysis)
        batch_action.setToolTip("分析项目中的所有图像")

    def add_images(self):
        """Add images to project"""
        if not self.project_manager.current_project:
            QMessageBox.warning(self, "警告", "请先打开或创建项目")
            return
        
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "选择图像",
            os.path.expanduser("~"),
            "图像文件 (*.png *.jpg *.jpeg *.bmp)"
        )
        
        if files:
            progress = ProgressDialog(self)
            progress.setWindowTitle("添加图像")
            progress.show()
            
            total = len(files)
            added = 0
            
            for i, file in enumerate(files):
                percent = int((i + 1) / total * 100)
                progress.set_progress(percent, f"正在添加图像: {i+1}/{total}")
                
                if self.project_manager.add_image(file):
                    self.image_list.add_image(file)
                    added += 1
                    
                if progress.was_cancelled():
                    break
            
            progress.close()
            self.show_status_message(f"已添加 {added} 个图像")

    def show_preprocessing_settings(self):
        """Show preprocessing settings dialog"""
        dialog = PreprocessingDialog(self)
        if self.preprocess_config:
            dialog.load_config(self.preprocess_config)
            
        if dialog.exec():
            self.preprocess_config = dialog.get_config()
            if self.preprocess_config:
                self.config.set('preprocessing', self.preprocess_config)
                mode = "自动优化" if self.preprocess_config.get('auto_optimize') else "自定义参数"
                self.show_status_message(f"预处理设置已更新: {mode}")
            else:
                self.preprocess_config = None
                self.config.set('preprocessing', {})
                self.show_status_message("使用默认预处理参数")

    def start_analysis(self):
        """Start colony analysis"""
        current_image = self.image_viewer.get_current_path()
        if not current_image:
            QMessageBox.warning(self, "警告", "请先选择要分析的图像")
            return

        try:
            progress = ProgressDialog(self)
            progress.setWindowTitle("正在分析")
            progress.show()

            # Get preprocessing settings
            auto_optimize = self.preprocess_config.get('auto_optimize', False) if self.preprocess_config else False
            config = self.preprocess_config if self.preprocess_config and not auto_optimize else None
            
            # Analyze image
            progress.set_progress(30, "分析图像...")
            results = self.colony_detector.detect(
                current_image,
                preprocess_config=config,
                auto_optimize=auto_optimize
            )
            
            # Generate visualization
            progress.set_progress(70, "生成结果...")
            annotated = self.colony_detector.annotate_image(current_image, results)
            
            # Convert to QPixmap
            height, width, channel = annotated.shape
            qimg = QImage(annotated.data, width, height, width * channel, 
                         QImage.Format.Format_BGR888)
            pixmap = QPixmap.fromImage(qimg)
            
            # Show results
            self.image_viewer.set_pixmap(pixmap)
            self.result_visualizer.show_results(results)
            self.project_manager.save_results(current_image, results)
            
            # Done
            progress.close()
            total = len(results['boxes'])
            self.show_status_message(f"分析完成: 检测到 {total} 个菌落")
            
        except Exception as e:
            logger.error(f"分析失败: {e}")
            QMessageBox.critical(self, "错误", f"分析失败: {str(e)}")

    def start_batch_analysis(self):
        """Start batch analysis"""
        if not self.project_manager.current_project:
            QMessageBox.warning(self, "警告", "请先打开或创建项目")
            return
            
        images = self.project_manager.get_images()
        if not images:
            QMessageBox.warning(self, "警告", "项目中没有图像")
            return
            
        try:
            progress = ProgressDialog(self)
            progress.setWindowTitle("批量分析")
            progress.show()
            
            total = len(images)
            processed = 0
            
            # Get preprocessing settings
            auto_optimize = self.preprocess_config.get('auto_optimize', False) if self.preprocess_config else False
            config = self.preprocess_config if self.preprocess_config and not auto_optimize else None
            
            for i, image_path in enumerate(images):
                if progress.was_cancelled():
                    break
                    
                percent = int((i + 1) / total * 100)
                progress.set_progress(percent, f"正在分析: {i+1}/{total}")
                
                try:
                    # Analyze image
                    results = self.colony_detector.detect(
                        image_path,
                        preprocess_config=config,
                        auto_optimize=auto_optimize
                    )
                    
                    # Save results
                    self.project_manager.save_results(image_path, results)
                    processed += 1
                    
                except Exception as e:
                    logger.error(f"分析图像失败 {image_path}: {e}")
                    continue
            
            progress.close()
            self.show_status_message(f"批量分析完成: {processed}/{total} 个图像")
            
        except Exception as e:
            logger.error(f"批量分析失败: {e}")
            QMessageBox.critical(self, "错误", f"批量分析失败: {str(e)}")

    def show_status_message(self, message: str):
        """Show message in status bar"""
        self.statusBar().showMessage(message, 3000)

    def new_project(self):
        """Create new project"""
        dialog = NewProjectDialog(self)
        if dialog.exec():
            name, path = dialog.get_project_info()
            if self.project_manager.create_project(name, path):
                self.show_status_message(f"项目已创建：{name}")
                self.image_list.clear()
                self.update_ui()

    def open_project(self):
        """Open existing project"""
        dialog = OpenProjectDialog(self)
        if dialog.exec():
            path = dialog.get_project_path()
            if self.project_manager.open_project(path):
                self.show_status_message("项目已打开")
                self.image_list.clear()
                self.update_ui()
                for image in self.project_manager.get_images():
                    self.image_list.add_image(image)

    def update_ui(self):
        """Update UI state"""
        has_project = self.project_manager.current_project is not None
        self.image_list.setEnabled(has_project)
        self.result_visualizer.setEnabled(has_project)

    def on_image_selected(self, image_path):
        """Handle image selection from image list"""
        try:
            if self.image_viewer.load_image(image_path):
                logger.debug(f"Loading image: {image_path}")
                self.show_status_message(f"已加载图像: {os.path.basename(image_path)}")
                
                self.result_visualizer.set_image_path(image_path)
                
                results = self.project_manager.get_results(image_path)
                if results:
                    logger.debug(f"Found existing results for {image_path}")
                    self.result_visualizer.show_results(results)
                    
                    # Show annotated image
                    annotated = self.colony_detector.annotate_image(image_path, results)
                    height, width, channel = annotated.shape
                    qimg = QImage(annotated.data, width, height, width * channel,
                                QImage.Format.Format_BGR888)
                    pixmap = QPixmap.fromImage(qimg)
                    self.image_viewer.set_pixmap(pixmap)
                else:
                    self.result_visualizer.clear_results()
            else:
                self.show_status_message("加载图像失败")
                
        except Exception as e:
            logger.error(f"Error loading image: {e}")
            self.show_status_message("加载图像时出错")
