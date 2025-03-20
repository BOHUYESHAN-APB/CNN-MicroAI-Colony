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
from PyQt6.QtGui import QAction

from .project_dialog import ProjectDialog
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
from ..utils.image_preprocessing import load_image

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
        
        # Initialize UI
        self.setup_ui()
        self.setup_docks()
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
        
    def setup_menu(self):
        """Setup menu bar"""
        # View menu
        view_menu = self.menuBar().addMenu(self._("视图"))
        
        # Dock visibility actions
        view_menu.addAction(self.image_list.toggleViewAction())
        view_menu.addAction(self.result_image.toggleViewAction())
        view_menu.addAction(self.result_stats.toggleViewAction())
        view_menu.addAction(self.result_table.toggleViewAction())
        view_menu.addAction(self.main_toolbar.toggleViewAction())
        view_menu.addSeparator()
        
        # Layout management
        layout_menu = view_menu.addMenu(self._("布局"))
        layout_menu.addAction(self._("保存布局..."), 
                            lambda: self.dock_manager.save_layout())
        layout_menu.addAction(self._("加载布局..."), 
                            lambda: self.dock_manager.load_layout())
        layout_menu.addAction(self._("重置布局"), 
                            lambda: self.dock_manager.reset_layout())
        
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
        
    def open_project(self):
        """Open project dialog"""
        logger.debug(f"open_project: current_project={self.current_project}, current_path={self.current_path}")
        dialog = ProjectDialog(self)
        if dialog.exec():
            self.current_project = dialog.get_project_path()
            logger.info(self._("打开项目: ") + f"{self.current_project}")
            self.image_list.add_btn.setEnabled(True)
            
    def on_image_selected(self, path):
        """Handle image selection from list"""
        logger.debug(f"Attempting to load image: {path}")
        try:
            # Convert path to native format
            abs_path = QDir.toNativeSeparators(os.path.abspath(path))
            logger.debug(f"Normalized path: {abs_path}")
            
            if self.image_viewer.load_image(abs_path):
                self.current_path = abs_path
                self.analyze_btn.setEnabled(True)
                logger.info(f"Successfully loaded image: {abs_path}")
                if path in self.results_cache:
                    self.show_cached_results(path)
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
        self.result_image.display_image(cache['image'])
        self.result_stats.display_stats(cache['stats'])
        self.result_table.display_results(cache['detections'])
        
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
            
            # Load image using preprocessing utility
            image = load_image(self.current_path)
            if image is None:
                QMessageBox.critical(
                    self,
                    self._("错误"),
                    self._("图片加载失败: ") + self.current_path
                )
                return
                
            # Detect colonies
            detections = self.detector.detect_colonies(image)
            if detections is None:
                QMessageBox.critical(
                    self,
                    self._("错误"),
                    self._("菌落检测失败。")
                )
                return
                
            # Calculate statistics
            stats = self.detector.get_statistics(detections, image.shape[:2])
            
            # Cache results
            self.results_cache[self.current_path] = {
                'image': image,
                'detections': detections,
                'stats': stats
            }
            
            # Display results
            self.result_image.display_results(image, detections)
            self.result_stats.display_stats(stats)
            self.result_table.display_results(detections)
            
            # Enable save button
            self.save_btn.setEnabled(True)
            
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
