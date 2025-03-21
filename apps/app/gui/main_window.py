"""
Main window implementation
主窗口实现
"""
import os
import cv2
import numpy as np
import logging
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                            QPushButton, QMessageBox, QFileDialog, QDockWidget,
                            QToolBar, QStatusBar, QMenu)
from PyQt6.QtCore import Qt, QSize, QTimer, QDir
from PyQt6.QtGui import QAction, QActionGroup

from .project_dialog import ProjectDialog
from .preprocessing_dialog import PreprocessingDialog
from .image_list_dock import ImageListDock
from .image_viewer_dock import ImageViewerDock
from .result_image_dock import ResultImageDock
from .result_stats_dock import ResultStatsDock
from .result_table_dock import ResultTableDock
from .dock_manager import DockManager
from .toolbar_constants import MEDIUM_ICON_SIZE, TOOLBAR_STYLE
from ..models.colony_detector import ColonyDetector
from ..utils.project_manager import ProjectManager
from ..utils.i18n import translate
from ..utils.image_preprocessing import load_image, preprocess_image, PreprocessingConfig

logger = logging.getLogger(__name__)

class MainWindow(QMainWindow):
    """Main window of the application"""
    
    # Class-level translation function
    _ = staticmethod(translate)
    
    def __init__(self):
        super().__init__()
        
        # Initialize core components
        self.detector = ColonyDetector()
        self.project_manager = ProjectManager()
        
        # Setup UI components
        self.setup_docks()  # Must be called before setup_menu
        self.setup_ui()
        self.setup_menu()
        
        # Setup dock manager
        self.dock_manager = DockManager(self)
        self.register_docks()
        self.dock_manager.setup_docks()
        
        # State
        self.current_image = None
        self.current_path = None
        self.current_project = None
        self.results_cache = {}  # Cache detection results
        self.preprocessing_config = None  # Current preprocessing configuration
        
        # Timer for auto-save
        self.save_timer = QTimer()
        self.save_timer.timeout.connect(self.auto_save)
        self.save_timer.start(60000)  # Auto-save every minute
        
    def setup_ui(self):
        """Setup user interface"""
        self.setWindowTitle(self._("菌落计数系统"))
        self.setMinimumSize(1200, 800)
        
        # Create main toolbar
        self.main_toolbar = QToolBar(self._("主工具栏"))
        self.main_toolbar.setObjectName("main_toolbar")
        self.main_toolbar.setIconSize(MEDIUM_ICON_SIZE)
        self.main_toolbar.setStyleSheet(TOOLBAR_STYLE)
        self.addToolBar(self.main_toolbar)
        
        # Add toolbar buttons
        self.open_btn = QPushButton(self._("打开项目"))
        self.open_btn.clicked.connect(self.open_project)
        self.main_toolbar.addWidget(self.open_btn)
        
        self.preprocess_btn = QPushButton(self._("预处理设置"))
        self.preprocess_btn.clicked.connect(self.show_preprocessing_dialog)
        self.preprocess_btn.setEnabled(False)
        self.main_toolbar.addWidget(self.preprocess_btn)
        
        self.analyze_btn = QPushButton(self._("分析"))
        self.analyze_btn.clicked.connect(self.start_analysis)
        self.analyze_btn.setEnabled(False)
        self.main_toolbar.addWidget(self.analyze_btn)
        
        self.save_btn = QPushButton(self._("保存结果"))
        self.save_btn.clicked.connect(self.save_results)
        self.save_btn.setEnabled(False)
        self.main_toolbar.addWidget(self.save_btn)
        
        # Create status bar
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage(self._("就绪"))
        
        # Apply dark theme
        self.apply_theme()
        
    def setup_menu(self):
        """Setup menu bar"""
        # File menu
        file_menu = self.menuBar().addMenu(self._("文件"))
        file_menu.addAction(self._("打开项目"), self.open_project)
        file_menu.addAction(self._("保存结果"), self.save_results)
        file_menu.addSeparator()
        file_menu.addAction(self._("退出"), self.close)
        
        # Processing menu
        processing_menu = self.menuBar().addMenu(self._("处理"))
        
        # Image preprocessing submenu
        preprocess_menu = processing_menu.addMenu(self._("预处理"))
        
        # Preprocessing mode selection
        mode_menu = preprocess_menu.addMenu(self._("预处理模式"))
        self.preprocess_mode_group = QActionGroup(self)
        
        mode_default = QAction(self._("默认模式"), self)
        mode_default.setCheckable(True)
        mode_default.setChecked(True)
        self.preprocess_mode_group.addAction(mode_default)
        mode_menu.addAction(mode_default)
        
        mode_custom = QAction(self._("自定义参数"), self)
        mode_custom.setCheckable(True)
        self.preprocess_mode_group.addAction(mode_custom)
        mode_menu.addAction(mode_custom)
        
        mode_auto = QAction(self._("自动优化"), self)
        mode_auto.setCheckable(True)
        self.preprocess_mode_group.addAction(mode_auto)
        mode_menu.addAction(mode_auto)
        
        # Connect mode actions
        mode_default.triggered.connect(lambda: self.set_preprocess_mode(0))
        mode_custom.triggered.connect(lambda: self.set_preprocess_mode(1))
        mode_auto.triggered.connect(lambda: self.set_preprocess_mode(2))
        
        preprocess_menu.addSeparator()
        
        # Enable/disable preprocessing
        self.enable_preprocess_action = QAction(self._("启用预处理"), self)
        self.enable_preprocess_action.setCheckable(True)
        self.enable_preprocess_action.setChecked(True)
        preprocess_menu.addAction(self.enable_preprocess_action)
        
        preprocess_menu.addAction(self._("预处理设置..."), self.show_preprocessing_dialog)
        
        processing_menu.addAction(self._("开始分析"), self.start_analysis)
        
        # View menu
        view_menu = self.menuBar().addMenu(self._("视图"))
        
        # Dock visibility submenu
        docks_menu = view_menu.addMenu(self._("停靠窗口"))
        docks_menu.addAction(self.image_list.toggleViewAction())
        docks_menu.addAction(self.result_image.toggleViewAction())
        docks_menu.addAction(self.result_stats.toggleViewAction())
        docks_menu.addAction(self.result_table.toggleViewAction())
        docks_menu.addAction(self.main_toolbar.toggleViewAction())
        
        view_menu.addSeparator()
        
        # Layout management
        layout_menu = view_menu.addMenu(self._("布局"))
        layout_menu.addAction(self._("保存布局..."), 
                            lambda: self.dock_manager.save_layout())
        layout_menu.addAction(self._("加载布局..."), 
                            lambda: self.dock_manager.load_layout())
        layout_menu.addAction(self._("重置布局"), 
                            lambda: self.dock_manager.reset_layout())
                            
        # Help menu
        help_menu = self.menuBar().addMenu(self._("帮助"))
        help_menu.addAction(self._("使用说明"), self.show_help)
        help_menu.addAction(self._("关于"), self.show_about)
        
    def setup_docks(self):
        """Create dock widgets"""
        # Create docks
        self.image_list = ImageListDock(self)
        self.image_list.image_selected.connect(self.on_image_selected)
        
        self.image_viewer = ImageViewerDock(self)
        self.setCentralWidget(self.image_viewer)
        
        self.result_image = ResultImageDock(self)
        self.result_stats = ResultStatsDock(self)
        self.result_table = ResultTableDock(self)
        
    def register_docks(self):
        """Register docks with dock manager"""
        self.dock_manager.register_dock("image_list_dock", self.image_list)
        self.dock_manager.register_dock("image_viewer_dock", self.image_viewer)
        self.dock_manager.register_dock("result_image_dock", self.result_image)
        self.dock_manager.register_dock("result_stats_dock", self.result_stats)
        self.dock_manager.register_dock("result_table_dock", self.result_table)
        
    def apply_theme(self):
        """Apply dark theme to window"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e1e;
            }
            QMenuBar {
                background-color: #2d2d2d;
                color: #e0e0e0;
            }
            QMenuBar::item:selected {
                background-color: #505050;
            }
            QMenu {
                background-color: #2d2d2d;
                color: #e0e0e0;
                border: 1px solid #505050;
            }
            QMenu::item:selected {
                background-color: #505050;
            }
            QPushButton {
                background-color: #424242;
                color: #e0e0e0;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 14px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #505050;
            }
            QPushButton:pressed {
                background-color: #616161;
            }
            QPushButton:disabled {
                background-color: #2d2d2d;
                color: #808080;
            }
            QStatusBar {
                background-color: #2d2d2d;
                color: #e0e0e0;
            }
        """)
        
    def show_preprocessing_dialog(self):
        """Show preprocessing settings dialog"""
        if self.current_image is None or not isinstance(self.current_image, np.ndarray):
            QMessageBox.warning(
                self,
                self._("警告"),
                self._("请先打开一张图片")
            )
            return
            
        dialog = PreprocessingDialog(self, self.current_image)
        
        # Load current config if exists
        if self.preprocessing_config:
            dialog.load_config(self.preprocessing_config)
            
        if dialog.exec():
            self.preprocessing_config = dialog.get_config()
            logger.info("Updated preprocessing configuration")
            self.statusBar.showMessage(self._("已更新预处理配置"))
            
    def set_preprocess_mode(self, mode):
        """Set preprocessing mode
        
        Args:
            mode (int): 0=default, 1=custom, 2=auto
        """
        if mode == 0:
            self.preprocessing_config = None
            self.statusBar.showMessage(self._("使用默认预处理参数"))
        elif mode == 1:
            # Show dialog if no custom config exists
            if not self.preprocessing_config:
                self.show_preprocessing_dialog()
            self.statusBar.showMessage(self._("使用自定义预处理参数"))
        else:  # mode == 2
            self.preprocessing_config = {'auto_optimize': True}
            self.statusBar.showMessage(self._("使用自动优化预处理"))
            
    def clear_results(self):
        """Clear current results"""
        if self.current_path in self.results_cache:
            del self.results_cache[self.current_path]
            
        if hasattr(self, 'result_image'):
            self.result_image.clear()
        if hasattr(self, 'result_stats'):
            self.result_stats.clear()
        if hasattr(self, 'result_table'):
            self.result_table.clear()
            
        self.save_btn.setEnabled(False)
        self.statusBar.showMessage(self._("已清除分析结果"))
            
    def show_help(self):
        """Show help dialog"""
        QMessageBox.information(
            self,
            self._("使用说明"),
            self._("1. 打开项目文件夹\n"
                   "2. 添加图片\n"
                   "3. 选择预处理模式\n"
                   "4. 开始分析\n"
                   "5. 查看结果\n"
                   "6. 保存结果")
        )
        
    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(
            self,
            self._("关于"),
            self._("菌落计数系统 v1.0\n\n"
                   "基于深度学习的菌落自动检测与计数系统")
        )
        
    def open_project(self):
        """Open project dialog"""
        logger.debug(f"open_project: current_project={self.current_project}, current_path={self.current_path}")
        dialog = ProjectDialog(self)
        if dialog.exec():
            self.current_project = dialog.get_project_path()
            logger.info(self._("打开项目: ") + f"{self.current_project}")
            self.image_list.add_btn.setEnabled(True)
            self.statusBar.showMessage(self._("已打开项目: ") + self.current_project)
            
    def on_image_selected(self, path):
        """Handle image selection from list"""
        logger.debug(f"Attempting to load image: {path}")
        try:
            # Convert path to native format
            abs_path = QDir.toNativeSeparators(os.path.abspath(path))
            logger.debug(f"Normalized path: {abs_path}")
            
            if self.image_viewer.load_image(abs_path):
                self.current_path = abs_path
                self.current_image = load_image(abs_path)
                self.preprocess_btn.setEnabled(True)
                self.analyze_btn.setEnabled(True)
                logger.info(f"Successfully loaded image: {abs_path}")
                if path in self.results_cache:
                    self.show_cached_results(path)
                self.statusBar.showMessage(self._("已加载图片: ") + os.path.basename(abs_path))
            else:
                logger.error(f"Failed to load image: {abs_path}")
                QMessageBox.critical(
                    self,
                    self._("错误"),
                    self._("加载图片失败: {}").format(abs_path)
                )
                
        except Exception as e:
            logger.error(f"Image load error: {str(e)}")
            QMessageBox.critical(
                self,
                self._("错误"),
                self._("加载图片时发生错误: {}").format(str(e))
            )
            
    def show_cached_results(self, path):
        """Show cached detection results"""
        cache = self.results_cache[path]
        
        # Convert back to RGB for display if needed
        image = cache['image']
        if len(image.shape) == 2:
            display_image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
        else:
            display_image = image.copy()
            
        # Show results
        self.result_image.display_results(display_image, cache['detections'])
        self.result_stats.display_stats(cache['stats'])
        self.result_table.display_results(cache['detections'])
        self.statusBar.showMessage(self._("已加载缓存结果"))
        
    def start_analysis(self):
        """Start colony detection"""
        logger.debug(f"start_analysis: current_project={self.current_project}, current_path={self.current_path}")
        try:
            # Check current image
            if not self.current_path:
                QMessageBox.warning(
                    self,
                    self._("警告"),
                    self._("请先打开一张图片进行分析。")
                )
                return
            
            # Initialize detector if needed
            if not self.detector.initialized:
                if not self.detector.initialize():
                    QMessageBox.critical(
                        self,
                        self._("错误"),
                        self._("模型初始化失败，请检查模型文件是否存在。")
                    )
                    return
                    
            # Load and preprocess image
            logger.debug(self._("加载图像: ") + f"{self.current_path}")
            
            image = load_image(self.current_path)
            if image is None:
                QMessageBox.critical(
                    self,
                    self._("错误"),
                    self._("图片加载失败: ") + self.current_path
                )
                return
                
            # Make a copy for display
            display_image = image.copy()
                
            # Apply preprocessing if configured and enabled
            if self.preprocessing_config and self.enable_preprocess_action.isChecked():
                # Convert config to dict if it's a PreprocessingConfig object
                config_dict = vars(self.preprocessing_config) if isinstance(self.preprocessing_config, PreprocessingConfig) else self.preprocessing_config
                config = PreprocessingConfig.from_dict(config_dict)
                processed = preprocess_image(image, config)
                if processed is None:
                    QMessageBox.critical(
                        self,
                        self._("错误"),
                        self._("图像预处理失败。")
                    )
                    return
                image = processed

            # Convert to grayscale for detection if needed
            if len(image.shape) == 3:
                detect_image = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            else:
                detect_image = image
                
            # Detect colonies
            detections = self.detector.detect_colonies(detect_image)
            if detections is None:
                QMessageBox.critical(
                    self,
                    self._("错误"),
                    self._("菌落检测失败。")
                )
                return
                
            # Calculate statistics
            stats = self.detector.get_statistics(detections, detect_image.shape[:2])
            
            # Cache results
            self.results_cache[self.current_path] = {
                'image': display_image,  # Store original RGB image
                'detections': detections,
                'stats': stats
            }
            
            # Display results
            self.result_image.display_results(display_image, detections)
            self.result_stats.display_stats(stats)
            self.result_table.display_results(detections)
            
            # Enable save button
            self.save_btn.setEnabled(True)
            self.statusBar.showMessage(self._("分析完成"))
            
        except Exception as e:
            logger.error(self._("分析失败: ") + f"{e}")
            QMessageBox.critical(
                self,
                self._("错误"),
                self._("分析过程中出现错误: ") + str(e)
            )
            
    def save_results(self):
        """Save detection results"""
        if not self.current_project or not self.current_path:
            return
            
        try:
            cache = self.results_cache.get(self.current_path)
            if cache:
                # Save results using project manager
                self.project_manager.save_results(
                    self.current_project,
                    self.current_path,
                    cache['detections'],
                    cache['stats']
                )
                logger.info(self._("保存项目结果: ") + f"{self.current_project}")
                self.statusBar.showMessage(self._("已保存分析结果"))
                
        except Exception as e:
            logger.error(self._("保存结果失败: ") + f"{e}")
            QMessageBox.critical(
                self,
                self._("错误"),
                self._("保存结果失败: ") + str(e)
            )
            
    def auto_save(self):
        """Auto save current results"""
        if self.current_project and self.current_path:
            self.save_results()
            
    def closeEvent(self, event):
        """Handle window close event"""
        # Save layout before closing
        self.dock_manager.save_layout()
        super().closeEvent(event)
