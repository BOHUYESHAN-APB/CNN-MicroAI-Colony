import os
import logging
from datetime import datetime
from pathlib import Path
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QToolBar, QMenuBar, QMenu, QMessageBox,
    QFileDialog, QStatusBar, QPushButton, QLabel,
    QGroupBox, QSlider, QDoubleSpinBox, QSpinBox,
    QProgressBar
)
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QIcon, QAction

from .image_list_widget import ImageBrowser
from .about_dialog import AboutDialog
from .settings_dialog import SettingsDialog
from .result_visualizer import ResultVisualizer
from ..utils.config import ConfigManager

logger = logging.getLogger(__name__)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        logger.info("Initializing MainWindow")
        
        # Window setup with style
        self.setWindowTitle("Colony Detection")
        self.resize(1200, 800)
        
        # Create status progress bar
        self.status_progress = QProgressBar()
        self.status_progress.setVisible(False)
        
        # Initialize components
        self._setup_central_widget()
        self._setup_menubar()
        self._setup_toolbar()
        self._setup_statusbar()
        
        # Initial state
        self.current_project = None
        self.config = ConfigManager()
        
        # Connect signals
        self.image_browser.images_changed.connect(self._update_status)
        
        logger.info("MainWindow initialization complete")
        
    def _setup_central_widget(self):
        """Setup the central widget with image browser and result area"""
        central_widget = QWidget()
        layout = QHBoxLayout()
        
        # Left side: Image Browser with title
        browser_group = QGroupBox(self.tr("Image Management"))
        browser_layout = QVBoxLayout()
        self.image_browser = ImageBrowser()
        browser_layout.addWidget(self.image_browser)
        browser_group.setLayout(browser_layout)
        layout.addWidget(browser_group, 40)
        
        # Right side: Analysis and Results
        right_panel = QVBoxLayout()
        
        # Analysis group
        analysis_group = QGroupBox(self.tr("Analysis Controls"))
        analysis_layout = QVBoxLayout()
        
        # Single/Batch mode selection
        mode_group = QGroupBox(self.tr("Analysis Mode"))
        mode_layout = QHBoxLayout()
        
        self.btn_single = QPushButton(self.tr("Single Image"))
        self.btn_single.setToolTip(self.tr("Analyze one image at a time"))
        self.btn_single.setCheckable(True)
        self.btn_single.setChecked(True)
        mode_layout.addWidget(self.btn_single)
        
        self.btn_batch = QPushButton(self.tr("Batch Analysis"))
        self.btn_batch.setToolTip(self.tr("Analyze multiple images at once"))
        self.btn_batch.setCheckable(True)
        mode_layout.addWidget(self.btn_batch)
        
        mode_group.setLayout(mode_layout)
        analysis_layout.addWidget(mode_group)
        
        # Analysis parameters
        params_group = QGroupBox(self.tr("Parameters"))
        params_layout = QVBoxLayout()
        
        # Detection settings
        detection_group = QGroupBox(self.tr("Detection Settings"))
        detection_layout = QHBoxLayout()
        
        confidence_label = QLabel(self.tr("Confidence Threshold:"))
        self.confidence_slider = QSlider(Qt.Horizontal)
        self.confidence_slider.setRange(0, 100)
        self.confidence_slider.setValue(50)
        self.confidence_spin = QDoubleSpinBox()
        self.confidence_spin.setRange(0.0, 1.0)
        self.confidence_spin.setSingleStep(0.05)
        self.confidence_spin.setValue(0.5)
        
        # Connect confidence controls
        self.confidence_slider.valueChanged.connect(
            lambda v: self.confidence_spin.setValue(v / 100.0))
        self.confidence_spin.valueChanged.connect(
            lambda v: self.confidence_slider.setValue(int(v * 100)))
        
        detection_layout.addWidget(confidence_label)
        detection_layout.addWidget(self.confidence_slider)
        detection_layout.addWidget(self.confidence_spin)
        detection_group.setLayout(detection_layout)
        params_layout.addWidget(detection_group)
        
        # Quantitative analysis settings
        quant_group = QGroupBox(self.tr("Quantitative Analysis"))
        quant_layout = QHBoxLayout()
        
        iterations_label = QLabel(self.tr("Iterations:"))
        self.iterations_spin = QSpinBox()
        self.iterations_spin.setRange(10, 10000)
        self.iterations_spin.setSingleStep(10)
        self.iterations_spin.setValue(100)
        self.iterations_spin.setToolTip(self.tr("Number of analysis iterations"))
        
        quant_layout.addWidget(iterations_label)
        quant_layout.addWidget(self.iterations_spin)
        quant_layout.addStretch()
        quant_group.setLayout(quant_layout)
        params_layout.addWidget(quant_group)
        
        # Progress section
        progress_group = QGroupBox(self.tr("Progress"))
        progress_layout = QVBoxLayout()
        
        self.progress_label = QLabel(self.tr("Analysis Progress:"))
        progress_layout.addWidget(self.progress_label)
        
        self.analysis_progress = QProgressBar()
        self.analysis_progress.setVisible(False)
        progress_layout.addWidget(self.analysis_progress)
        
        # Analysis action buttons
        action_layout = QHBoxLayout()
        
        self.btn_analyze = QPushButton(self.tr("Start Analysis"))
        self.btn_analyze.setToolTip(self.tr("Start colony detection analysis"))
        self.btn_analyze.clicked.connect(self._start_analysis)
        action_layout.addWidget(self.btn_analyze)
        
        self.btn_stop = QPushButton(self.tr("Stop"))
        self.btn_stop.setToolTip(self.tr("Stop current analysis"))
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self._stop_analysis)
        action_layout.addWidget(self.btn_stop)
        
        progress_layout.addLayout(action_layout)
        progress_group.setLayout(progress_layout)
        params_layout.addWidget(progress_group)
        
        params_group.setLayout(params_layout)
        analysis_layout.addWidget(params_group)
        
        analysis_group.setLayout(analysis_layout)
        right_panel.addWidget(analysis_group)
        
        # Results visualization
        results_group = QGroupBox(self.tr("Analysis Results"))
        results_layout = QVBoxLayout()
        self.result_visualizer = ResultVisualizer()
        results_layout.addWidget(self.result_visualizer)
        results_group.setLayout(results_layout)
        right_panel.addWidget(results_group)
        
        # Connect mode buttons
        self.btn_single.clicked.connect(lambda: self._switch_mode("single"))
        self.btn_batch.clicked.connect(lambda: self._switch_mode("batch"))
        
        layout.addLayout(right_panel, 60)
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)
        
    def _setup_menubar(self):
        """Setup application menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu(self.tr("&File"))
        
        new_project = QAction(self.tr("&New Project"), self)
        new_project.setShortcut("Ctrl+N")
        new_project.triggered.connect(self._new_project)
        file_menu.addAction(new_project)
        
        open_project = QAction(self.tr("&Open Project"), self)
        open_project.setShortcut("Ctrl+O")
        open_project.triggered.connect(self._open_project)
        file_menu.addAction(open_project)
        
        file_menu.addSeparator()
        
        import_images = QAction(self.tr("&Import Images"), self)
        import_images.setShortcut("Ctrl+I")
        import_images.triggered.connect(self.image_browser.import_images)
        file_menu.addAction(import_images)
        
        file_menu.addSeparator()
        
        exit_action = QAction(self.tr("E&xit"), self)
        exit_action.setShortcut("Alt+F4")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Settings menu
        settings_menu = menubar.addMenu(self.tr("&Settings"))
        
        preferences = QAction(self.tr("&Preferences"), self)
        preferences.triggered.connect(self._show_settings)
        settings_menu.addAction(preferences)
        
        # Help menu
        help_menu = menubar.addMenu(self.tr("&Help"))
        
        about = QAction(self.tr("&About"), self)
        about.triggered.connect(self._show_about)
        help_menu.addAction(about)
        
    def _setup_toolbar(self):
        """Setup main toolbar"""
        toolbar = QToolBar()
        self.addToolBar(toolbar)
        
        new_btn = QPushButton(self.tr("New Project"))
        new_btn.clicked.connect(self._new_project)
        new_btn.setToolTip(self.tr("Create a new project"))
        toolbar.addWidget(new_btn)
        
        open_btn = QPushButton(self.tr("Open Project"))
        open_btn.clicked.connect(self._open_project)
        open_btn.setToolTip(self.tr("Open an existing project"))
        toolbar.addWidget(open_btn)
        
        toolbar.addSeparator()
        
        import_btn = QPushButton(self.tr("Import Images"))
        import_btn.clicked.connect(self.image_browser.import_images)
        import_btn.setToolTip(self.tr("Import images to current project"))
        toolbar.addWidget(import_btn)
        
    def _setup_statusbar(self):
        """Setup status bar"""
        status_bar = QStatusBar()
        status_bar.addPermanentWidget(self.status_progress)
        self.setStatusBar(status_bar)
        status_bar.showMessage(self.tr("Ready"))
        
    @Slot()
    def _new_project(self):
        """Create new project"""
        dialog = QFileDialog()
        project_name, _ = dialog.getSaveFileName(
            self,
            self.tr("New Project"),
            os.path.expanduser("~/Desktop"),
            self.tr("Colony Detection Project (*.cdp)")
        )
        
        if project_name:
            if not project_name.endswith('.cdp'):
                project_name += '.cdp'
                
            project_dir = os.path.splitext(project_name)[0]
            os.makedirs(project_dir, exist_ok=True)
            
            # Create project metadata
            self.current_project = project_dir
            self.image_browser.set_project_directory(project_dir)
            self.statusBar().showMessage(
                self.tr("Created new project: {}").format(os.path.basename(project_dir))
            )
            
    @Slot()
    def _open_project(self):
        """Open existing project"""
        dialog = QFileDialog()
        project_path, _ = dialog.getOpenFileName(
            self,
            self.tr("Open Project"),
            os.path.expanduser("~/Desktop"),
            self.tr("Colony Detection Project (*.cdp)")
        )
        
        if project_path:
            project_dir = os.path.splitext(project_path)[0]
            if os.path.isdir(project_dir):
                self.current_project = project_dir
                self.image_browser.set_project_directory(project_dir)
                self.statusBar().showMessage(
                    self.tr("Opened project: {}").format(os.path.basename(project_dir))
                )
            else:
                QMessageBox.warning(
                    self,
                    self.tr("Error"),
                    self.tr("Project directory not found: {}").format(project_dir)
                )
                
    @Slot()
    def _show_settings(self):
        """Show settings dialog"""
        dialog = SettingsDialog(self)
        if dialog.exec():
            # Apply settings
            self.config.save()
            
    @Slot()
    def _show_about(self):
        """Show about dialog"""
        dialog = AboutDialog(self)
        dialog.exec()

    @Slot()
    def _switch_mode(self, mode):
        """Switch between single and batch analysis modes"""
        if mode == "single":
            self.btn_single.setChecked(True)
            self.btn_batch.setChecked(False)
            self.btn_analyze.setText(self.tr("Analyze Image"))
            self.iterations_spin.setEnabled(True)
        else:
            self.btn_single.setChecked(False)
            self.btn_batch.setChecked(True)
            self.btn_analyze.setText(self.tr("Start Batch Analysis"))
            self.iterations_spin.setEnabled(False)
    
    @Slot()
    def _start_analysis(self):
        """Start analysis based on current mode"""
        self.btn_analyze.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.analysis_progress.setVisible(True)
        self.progress_label.setText(self.tr("Analysis in progress..."))
        
        if self.btn_single.isChecked():
            self._start_single_analysis()
        else:
            self._start_batch_analysis()
            
    @Slot()
    def _stop_analysis(self):
        """Stop current analysis"""
        # TODO: Implement analysis stopping
        self.btn_analyze.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.analysis_progress.setVisible(False)
        self.progress_label.setText(self.tr("Analysis stopped"))
        
    def _start_single_analysis(self):
        """Start analysis of single image"""
        # TODO: Implement single image analysis
        pass
        
    def _start_batch_analysis(self):
        """Start batch analysis of multiple images"""
        # TODO: Implement batch analysis
        pass

    @Slot(list)
    def _update_status(self, image_list):
        """Update status bar with image count"""
        count = len(image_list)
        if count > 0:
            self.statusBar().showMessage(
                self.tr("Ready - {} images loaded").format(count)
            )
        else:
            self.statusBar().showMessage(self.tr("Ready"))
