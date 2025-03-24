"""
Main window implementation
主窗口实现
"""
import os
import shutil
import logging
from PyQt6.QtWidgets import (QMainWindow, QApplication, QToolBar, QMessageBox,
                            QLabel, QDockWidget, QFileDialog)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QAction

from .image_viewer_dock import ImageViewerDock
from .result_image_dock import ResultImageDock
from .result_table_dock import ResultTableDock 
from .result_stats_dock import ResultStatsDock
from .image_list_dock import ImageListDock
from .project_dialog import ProjectDialog
from .preprocessing_dialog import PreprocessingDialog
from .optimizationwidget import Optimizationwidget # 显式导入 Optimizationwidget (全部小写)
from .dock_manager import DockManager
from ..utils.config import load_config, save_config
from ..utils.project_manager import ProjectManager
from ..core.services.image_processor import ImageProcessor

logger = logging.getLogger(__name__)

class MainWindow(QMainWindow):
    """Main window class"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("微生物菌落计数分析")
        
        # Initialize window state
        self.current_image = None  # Currently displayed image
        self.project_dir = None
        self.project_manager = None
        
        self.setup_ui()
        self.setup_actions()
        self.setup_connections()
        
        # Create services
        self.image_processor = ImageProcessor()
        
        # Initialize from config
        config = load_config()
        if config:
            self.restore_state(config)
        
        # Show startup dialog
        self.show_startup_dialog()
        
    def setup_ui(self):
        """Setup user interface"""
        # Window settings
        self.resize(1200, 800)
        
        # Create status bar
        self.status_bar = self.statusBar()
        self.status_label = QLabel()
        self.status_bar.addWidget(self.status_label)
        
        # Create toolbars with object names
        self.file_toolbar = QToolBar("文件")
        self.file_toolbar.setObjectName("file_toolbar")
        self.file_toolbar.setMovable(False)
        self.addToolBar(self.file_toolbar)
        
        self.view_toolbar = QToolBar("视图")
        self.view_toolbar.setObjectName("view_toolbar")
        self.view_toolbar.setMovable(False)
        self.addToolBar(self.view_toolbar)
        
        self.tools_toolbar = QToolBar("工具")
        self.tools_toolbar.setObjectName("tools_toolbar")
        self.tools_toolbar.setMovable(False)
        self.addToolBar(self.tools_toolbar)
        
        # Create docks
        self.image_list_dock = ImageListDock(self)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea,
                          self.image_list_dock)
        
        self.image_viewer_dock = ImageViewerDock(self)
        self.addDockWidget(Qt.DockWidgetArea.TopDockWidgetArea,
                          self.image_viewer_dock)
        
        self.result_image_dock = ResultImageDock(self)
        self.addDockWidget(Qt.DockWidgetArea.TopDockWidgetArea,
                          self.result_image_dock)
        
        self.result_table_dock = ResultTableDock(self)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea,
                          self.result_table_dock)
                          
        self.result_stats_dock = ResultStatsDock(self)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea,
                          self.result_stats_dock)
        
        # Create dock manager
        self.dock_manager = DockManager(self)
        self.dock_manager.register_dock(self.image_list_dock)
        self.dock_manager.register_dock(self.image_viewer_dock)
        self.dock_manager.register_dock(self.result_image_dock)
        self.dock_manager.register_dock(self.result_table_dock)
        self.dock_manager.register_dock(self.result_stats_dock)
        
    def setup_actions(self):
        """Setup actions"""
        # File actions
        self.open_project_action = QAction("打开项目", self)
        self.open_project_action.setStatusTip("打开已有项目")
        self.file_toolbar.addAction(self.open_project_action)
        
        self.new_project_action = QAction("新建项目", self)
        self.new_project_action.setStatusTip("创建新项目")
        self.file_toolbar.addAction(self.new_project_action)
        
        self.import_images_action = QAction("导入图片", self)
        self.import_images_action.setStatusTip("导入图片到项目")
        self.import_images_action.setEnabled(False)
        self.file_toolbar.addAction(self.import_images_action)
        
        # Tool actions
        self.preprocess_action = QAction("预处理", self)
        self.preprocess_action.setStatusTip("图像预处理设置")
        self.tools_toolbar.addAction(self.preprocess_action)
        
        self.analyze_action = QAction("分析", self)
        self.analyze_action.setStatusTip("分析当前图像")
        self.tools_toolbar.addAction(self.analyze_action)
        
    def setup_connections(self):
        """Setup signal connections"""
        # File actions
        self.open_project_action.triggered.connect(self.show_open_project_dialog)
        self.new_project_action.triggered.connect(self.show_new_project_dialog)
        self.import_images_action.triggered.connect(self.import_images)
        
        # Tool actions
        self.preprocess_action.triggered.connect(self.show_preprocessing_dialog)
        self.analyze_action.triggered.connect(self.analyze_current_image)
        
        # Image list
        self.image_list_dock.image_selected.connect(self.load_image)
        
    def show_startup_dialog(self):
        """Show startup project dialog"""
        dialog = ProjectDialog(self)
        if dialog.exec():
            project_dir = dialog.get_project_dir()
            if project_dir:
                self.open_project(project_dir)
    
    def show_open_project_dialog(self):
        """Show open project dialog"""
        project_dir = QFileDialog.getExistingDirectory(
            self,
            "选择项目目录",
            ""
        )
        if project_dir:
            self.open_project(project_dir)
            
    def show_new_project_dialog(self):
        """Show new project dialog"""
        dialog = ProjectDialog(self, new_project=True)
        if dialog.exec():
            project_dir = dialog.get_project_dir()
            if project_dir:
                self.create_project(project_dir)
                
    def open_project(self, project_dir):
        """Open project from directory"""
        try:
            self.project_dir = project_dir
            logger.info(f"打开项目: {project_dir}")
            
            # Load project files
            self.project_manager = ProjectManager(project_dir)
            image_files = self.project_manager.get_image_files()
            
            # Update image list
            self.image_list_dock.clear()
            for image_file in image_files:
                self.image_list_dock.add_image(image_file)
                
            # Update status
            self.status_label.setText(f"项目: {os.path.basename(project_dir)}")
            
            # Enable import action
            self.import_images_action.setEnabled(True)
            
        except Exception as e:
            logger.error(f"打开项目失败: {str(e)}")
            QMessageBox.critical(self, "错误", f"打开项目失败:\n{str(e)}")
            
    def create_project(self, project_dir):
        """Create new project"""
        try:
            os.makedirs(project_dir, exist_ok=True)
            self.open_project(project_dir)
            
        except Exception as e:
            logger.error(f"创建项目失败: {str(e)}")
            QMessageBox.critical(self, "错误", f"创建项目失败:\n{str(e)}")
            
    def import_images(self):
        """Import images into project"""
        if not self.project_manager:
            return
            
        file_dialog = QFileDialog(self)
        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFiles)
        file_dialog.setNameFilter("Images (*.jpg *.jpeg *.png *.bmp)")
        
        if file_dialog.exec():
            files = file_dialog.selectedFiles()
            
            try:
                # Copy files to project images directory
                for src_path in files:
                    filename = os.path.basename(src_path)
                    dst_path = os.path.join(self.project_manager.config['images_dir'], 
                                          filename)
                    shutil.copy2(src_path, dst_path)
                    self.image_list_dock.add_image(dst_path)
                    
            except Exception as e:
                logger.error(f"导入图片失败: {str(e)}")
                QMessageBox.critical(self, "错误", f"导入图片失败:\n{str(e)}")
            
    def load_image(self, image_path):
        """Load image from path"""
        try:
            # Load image
            success = self.image_viewer_dock.load_image(image_path)
            if success:
                logger.info(f"Successfully loaded image: {image_path}")
                
                # Get and store current image
                self.current_image = self.image_viewer_dock.get_current_image()
            else:
                logger.error(f"Failed to load image: {image_path}")
                
        except Exception as e:
            logger.error(f"Error loading image: {str(e)}")
            QMessageBox.critical(self, "错误", f"加载图像失败:\n{str(e)}")
            
    def show_preprocessing_dialog(self):
        """Show preprocessing dialog"""
        if self.current_image is None:
            QMessageBox.warning(self, "警告", "请先加载图像")
            return
            
        try:
            dialog = PreprocessingDialog(parent=self, image=self.current_image)
            if dialog.exec():
                config = dialog.get_config()
                # Apply preprocessing config
                
        except Exception as e:
            logger.error(f"预处理设置失败: {str(e)}")
            QMessageBox.critical(self, "错误", f"预处理设置失败:\n{str(e)}")
            
    def analyze_current_image(self):
        """Analyze current image"""
        if self.current_image is None:
            QMessageBox.warning(self, "警告", "请先加载图像")
            return
            
        try:
            # Run detection
            results = self.image_processor.process_image(self.current_image)
            
            # Display results
            self.result_image_dock.display_results(self.current_image, results)
            self.result_table_dock.update_results(results)
            self.result_stats_dock.update_stats(results)
            
        except Exception as e:
            logger.error(f"分析失败: {str(e)}")
            QMessageBox.critical(self, "错误", f"分析失败:\n{str(e)}")
            
    def save_state(self):
        """Save window state to config"""
        config = {
            'window_geometry': bytes(self.saveGeometry()).hex(),
            'window_state': bytes(self.saveState()).hex(),
            'project_dir': self.project_dir
        }
        
        # Save dock layouts
        self.dock_manager.save_layouts()
        
        return config
        
    def restore_state(self, config):
        """Restore window state from config"""
        if config.get('window_geometry'):
            self.restoreGeometry(bytes.fromhex(config['window_geometry']))
        if config.get('window_state'):
            self.restoreState(bytes.fromhex(config['window_state']))
        if config.get('project_dir'):
            self.open_project(config['project_dir'])
            
    def closeEvent(self, event):
        """Handle window close event"""
        try:
            # Save config
            config = self.save_state()
            save_config(config)
            
            # Save dock layouts
            self.dock_manager.save_layouts()
            
        except Exception as e:
            logger.error(f"Error saving application state: {str(e)}")
            
        event.accept()
