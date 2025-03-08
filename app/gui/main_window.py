import os
import logging
from datetime import datetime
from pathlib import Path
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QToolBar, QMenuBar, QMenu, QMessageBox,
    QFileDialog, QStatusBar, QPushButton, QLabel,
    QGroupBox, QSlider, QDoubleSpinBox, QSpinBox,
    QProgressBar, QDialog, QLineEdit, QDialogButtonBox
)
from PySide6.QtCore import Qt, Slot, QTranslator
from PySide6.QtGui import QIcon, QAction
from PySide6.QtWidgets import QApplication

from .image_list_widget import ImageBrowser
from .about_dialog import AboutDialog
from .settings_dialog import SettingsDialog
from .result_visualizer import ResultVisualizer
from ..utils.config import ConfigManager
from ..utils.i18n import get_i18n

logger = logging.getLogger(__name__)

class NewProjectDialog(QDialog):
    """Dialog for creating new project"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.i18n = get_i18n()
        self.setWindowTitle(self.i18n.get_string("new_project.title", "New Project"))
        self.setup_ui()
        
    def setup_ui(self):
        """Initialize user interface"""
        layout = QVBoxLayout(self)
        
        # Project name input
        form_layout = QVBoxLayout()
        form_layout.addWidget(QLabel(self.i18n.get_string("new_project.project_name", "Project Name:")))
        self.name_edit = QLineEdit()
        form_layout.addWidget(self.name_edit)
        layout.addLayout(form_layout)
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self.resize(300, 120)
        
    def get_project_name(self) -> str:
        """Get entered project name"""
        return self.name_edit.text().strip()
        
    def retranslateUi(self):
        self.setWindowTitle(self.i18n.get_string("new_project.title", "New Project"))
        

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        logger.info("Initializing MainWindow")
        self.i18n = get_i18n()
        
        # Window setup with style
        self.setWindowTitle(self.i18n.get_string("main_window.title", "MicroAI-Colony"))
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

        # Initialize translator
        # self.translator = QTranslator()
        self.current_locale = 'en'  # Default to English

        # Load initial translation
        # self._load_translation(self.current_locale)
        self.retranslateUi()

        # Connect signals
        self.image_browser.images_changed.connect(self._update_status)

        logger.info("MainWindow initialization complete")

    # def _load_translation(self, locale):
    #     """Loads the translation file for the given locale."""

    #     translation_map = {
    #         'en': "app/resources/i18n/en.qm",
    #         'zh_CN': "app/resources/i18n/zh_CN.qm"
    #     }

    #     if locale in translation_map:
    #         qm_file = translation_map[locale]
    #         if self.translator.load(qm_file):
    #             QApplication.instance().installTranslator(self.translator)
    #             self.retranslateUi()
    #             logger.info(f"Loaded translation for {locale}")
    #         else:
    #             logger.error(f"Failed to load translation for {locale}")

    @Slot(str)
    def _switch_language(self, locale):
        """Switches the application language."""
        # self._load_translation(locale)
        self.i18n.set_locale(locale)
        self.retranslateUi()


    def retranslateUi(self):
        """Retranslate UI elements."""
        self.setWindowTitle(self.i18n.get_string("main_window.title", "MicroAI-Colony"))
        self.image_browser.retranslateUi()
        if hasattr(self, 'settings_dialog'):
            self.settings_dialog.retranslateUi()
        if hasattr(self, 'about_dialog'):
            self.about_dialog.retranslateUi()
        self.result_visualizer.retranslateUi()
        
        # Retranslate menu bar
        self.file_menu.setTitle(self.i18n.get_string("main_window.file_menu", "&File"))
        self.new_project.setText(self.i18n.get_string("main_window.new_project", "&New Project"))
        self.open_project.setText(self.i18n.get_string("main_window.open_project", "&Open Project"))
        self.import_images.setText(self.i18n.get_string("main_window.import_images", "&Import Images"))
        self.exit_action.setText(self.i18n.get_string("main_window.exit", "E&xit"))
        self.settings_menu.setTitle(self.i18n.get_string("main_window.settings_menu", "&Settings"))
        self.preferences.setText(self.i18n.get_string("main_window.preferences", "&Preferences"))
        self.help_menu.setTitle(self.i18n.get_string("main_window.help_menu", "&Help"))
        self.about.setText(self.i18n.get_string("main_window.about", "&About"))

        # Retranslate toolbar buttons
        self.new_btn.setText(self.i18n.get_string("main_window.new_project", "New Project"))
        self.new_btn.setToolTip(self.i18n.get_string("main_window.new_project_tooltip", "Create a new project"))
        self.open_btn.setText(self.i18n.get_string("main_window.open_project", "Open Project"))
        self.open_btn.setToolTip(self.i18n.get_string("main_window.open_project_tooltip", "Open an existing project"))
        self.import_btn.setText(self.i18n.get_string("main_window.import_images", "Import Images"))
        self.import_btn.setToolTip(self.i18n.get_string("main_window.import_images_tooltip", "Import images to current project"))
        
        # Retranslate status bar
        self._update_status(self.image_browser._get_image_list())
        
        # Retranslate central widget elements
        self.browser_group.setTitle(self.i18n.get_string("main_window.image_management", "Image Management"))
        self.analysis_group.setTitle(self.i18n.get_string("main_window.analysis_controls", "Analysis Controls"))
        self.mode_group.setTitle(self.i18n.get_string("main_window.analysis_mode", "Analysis Mode"))
        self.btn_single.setText(self.i18n.get_string("main_window.single_image", "Single Image"))
        self.btn_single.setToolTip(self.i18n.get_string("main_window.single_image_tooltip", "Analyze one image at a time"))
        self.btn_batch.setText(self.i18n.get_string("main_window.batch_analysis", "Batch Analysis"))
        self.btn_batch.setToolTip(self.i18n.get_string("main_window.batch_analysis_tooltip", "Analyze multiple images at once"))
        self.params_group.setTitle(self.i18n.get_string("main_window.parameters", "Parameters"))
        self.detection_group.setTitle(self.i18n.get_string("main_window.detection_settings", "Detection Settings"))
        self.confidence_label.setText(self.i18n.get_string("main_window.confidence_threshold", "Confidence Threshold:"))
        self.quant_group.setTitle(self.i18n.get_string("main_window.quantitative_analysis", "Quantitative Analysis"))
        self.iterations_label.setText(self.i18n.get_string("main_window.iterations", "Iterations:"))
        self.progress_group.setTitle(self.i18n.get_string("main_window.progress", "Progress"))
        self.progress_label.setText(self.i18n.get_string("main_window.analysis_progress", "Analysis Progress:"))
        self.btn_analyze.setText(self.i18n.get_string("main_window.start_analysis", "Start Analysis"))
        self.btn_analyze.setToolTip(self.i18n.get_string("main_window.start_analysis_tooltip", "Start colony detection analysis"))
        self.btn_stop.setText(self.i18n.get_string("main_window.stop", "Stop"))
        self.btn_stop.setToolTip(self.i18n.get_string("main_window.stop_tooltip", "Stop current analysis"))
        self.results_group.setTitle(self.i18n.get_string("main_window.analysis_results", "Analysis Results"))
        self.language_group.setTitle(self.i18n.get_string("main_window.language", "Language"))
        self.btn_en.setText("English")
        self.btn_zh.setText("中文")

    def _setup_central_widget(self):
        """Setup the central widget with image browser and result area"""
        central_widget = QWidget()
        layout = QHBoxLayout()
        
        # Left side: Image Browser with title
        self.browser_group = QGroupBox(self.i18n.get_string("main_window.image_management", "Image Management"))
        browser_layout = QVBoxLayout()
        self.image_browser = ImageBrowser()
        browser_layout.addWidget(self.image_browser)
        self.browser_group.setLayout(browser_layout)
        layout.addWidget(self.browser_group, 40)
        
        # Right side: Analysis and Results
        right_panel = QVBoxLayout()
        
        # Analysis group
        self.analysis_group = QGroupBox(self.i18n.get_string("main_window.analysis_controls", "Analysis Controls"))
        analysis_layout = QVBoxLayout()
        
        # Single/Batch mode selection
        self.mode_group = QGroupBox(self.i18n.get_string("main_window.analysis_mode", "Analysis Mode"))
        mode_layout = QHBoxLayout()
        
        self.btn_single = QPushButton(self.i18n.get_string("main_window.single_image", "Single Image"))
        self.btn_single.setToolTip(self.i18n.get_string("main_window.single_image_tooltip", "Analyze one image at a time"))
        self.btn_single.setCheckable(True)
        self.btn_single.setChecked(True)
        mode_layout.addWidget(self.btn_single)
        
        self.btn_batch = QPushButton(self.i18n.get_string("main_window.batch_analysis", "Batch Analysis"))
        self.btn_batch.setToolTip(self.i18n.get_string("main_window.batch_analysis_tooltip", "Analyze multiple images at once"))
        self.btn_batch.setCheckable(True)
        mode_layout.addWidget(self.btn_batch)
        
        self.mode_group.setLayout(mode_layout)
        analysis_layout.addWidget(self.mode_group)
        
        # Analysis parameters
        self.params_group = QGroupBox(self.i18n.get_string("main_window.parameters", "Parameters"))
        params_layout = QVBoxLayout()
        
        # Detection settings
        self.detection_group = QGroupBox(self.i18n.get_string("main_window.detection_settings", "Detection Settings"))
        detection_layout = QHBoxLayout()
        
        self.confidence_label = QLabel(self.i18n.get_string("main_window.confidence_threshold", "Confidence Threshold:"))
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
        
        detection_layout.addWidget(self.confidence_label)
        detection_layout.addWidget(self.confidence_slider)
        detection_layout.addWidget(self.confidence_spin)
        self.detection_group.setLayout(detection_layout)
        params_layout.addWidget(self.detection_group)
        
        # Quantitative analysis settings
        self.quant_group = QGroupBox(self.i18n.get_string("main_window.quantitative_analysis", "Quantitative Analysis"))
        quant_layout = QHBoxLayout()
        
        self.iterations_label = QLabel(self.i18n.get_string("main_window.iterations", "Iterations:"))
        self.iterations_spin = QSpinBox()
        self.iterations_spin.setRange(10, 10000)
        self.iterations_spin.setSingleStep(10)
        self.iterations_spin.setValue(100)
        self.iterations_spin.setToolTip(self.i18n.get_string("main_window.iterations_tooltip", "Number of analysis iterations"))
        
        quant_layout.addWidget(self.iterations_label)
        quant_layout.addWidget(self.iterations_spin)
        quant_layout.addStretch()
        self.quant_group.setLayout(quant_layout)
        params_layout.addWidget(self.quant_group)
        
        # Progress section
        self.progress_group = QGroupBox(self.i18n.get_string("main_window.progress", "Progress"))
        progress_layout = QVBoxLayout()
        
        self.progress_label = QLabel(self.i18n.get_string("main_window.analysis_progress", "Analysis Progress:"))
        progress_layout.addWidget(self.progress_label)
        
        self.analysis_progress = QProgressBar()
        self.analysis_progress.setVisible(False)
        progress_layout.addWidget(self.analysis_progress)
        
        # Analysis action buttons
        action_layout = QHBoxLayout()
        
        self.btn_analyze = QPushButton(self.i18n.get_string("main_window.start_analysis", "Start Analysis"))
        self.btn_analyze.setToolTip(self.i18n.get_string("main_window.start_analysis_tooltip", "Start colony detection analysis"))
        self.btn_analyze.clicked.connect(self._start_analysis)
        action_layout.addWidget(self.btn_analyze)
        
        self.btn_stop = QPushButton(self.i18n.get_string("main_window.stop", "Stop"))
        self.btn_stop.setToolTip(self.i18n.get_string("main_window.stop_tooltip", "Stop current analysis"))
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self._stop_analysis)
        action_layout.addWidget(self.btn_stop)
        
        progress_layout.addLayout(action_layout)
        self.progress_group.setLayout(progress_layout)
        params_layout.addWidget(self.progress_group)
        
        self.params_group.setLayout(params_layout)
        analysis_layout.addWidget(self.params_group)
        
        self.analysis_group.setLayout(analysis_layout)
        right_panel.addWidget(self.analysis_group)

        # Language selection
        self.language_group = QGroupBox(self.i18n.get_string("main_window.language", "Language"))
        language_layout = QHBoxLayout()

        self.btn_en = QPushButton("English")
        self.btn_en.clicked.connect(lambda: self._switch_language('en'))
        language_layout.addWidget(self.btn_en)

        self.btn_zh = QPushButton("中文")
        self.btn_zh.clicked.connect(lambda: self._switch_language('zh_CN'))
        language_layout.addWidget(self.btn_zh)

        self.language_group.setLayout(language_layout)
        right_panel.addWidget(self.language_group)

        # Results visualization
        self.results_group = QGroupBox(self.i18n.get_string("main_window.analysis_results", "Analysis Results"))
        results_layout = QVBoxLayout()
        self.result_visualizer = ResultVisualizer()
        results_layout.addWidget(self.result_visualizer)
        self.results_group.setLayout(results_layout)
        right_panel.addWidget(self.results_group)
        
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
        self.file_menu = menubar.addMenu(self.i18n.get_string("main_window.file_menu", "&File"))
        
        self.new_project = QAction(self.i18n.get_string("main_window.new_project", "&New Project"), self)
        self.new_project.setShortcut("Ctrl+N")
        self.new_project.triggered.connect(self._new_project)
        self.file_menu.addAction(self.new_project)
        
        self.open_project = QAction(self.i18n.get_string("main_window.open_project", "&Open Project"), self)
        self.open_project.setShortcut("Ctrl+O")
        self.open_project.triggered.connect(self._open_project)
        self.file_menu.addAction(self.open_project)
        
        self.file_menu.addSeparator()
        
        self.import_images = QAction(self.i18n.get_string("main_window.import_images", "&Import Images"), self)
        self.import_images.setShortcut("Ctrl+I")
        self.import_images.triggered.connect(self.image_browser.import_images)
        self.file_menu.addAction(self.import_images)
        
        self.file_menu.addSeparator()
        
        self.exit_action = QAction(self.i18n.get_string("main_window.exit", "E&xit"), self)
        self.exit_action.setShortcut("Alt+F4")
        self.exit_action.triggered.connect(self.close)
        self.file_menu.addAction(self.exit_action)
        
        # Settings menu
        self.settings_menu = menubar.addMenu(self.i18n.get_string("main_window.settings_menu", "&Settings"))
        
        self.preferences = QAction(self.i18n.get_string("main_window.preferences", "&Preferences"), self)
        self.preferences.triggered.connect(self._show_settings)
        self.settings_menu.addAction(self.preferences)
        
        # Help menu
        self.help_menu = menubar.addMenu(self.i18n.get_string("main_window.help_menu", "&Help"))
        
        self.about = QAction(self.i18n.get_string("main_window.about", "&About"), self)
        self.about.triggered.connect(self._show_about)
        self.help_menu.addAction(self.about)
        
    def _setup_toolbar(self):
        """Setup main toolbar"""
        toolbar = QToolBar()
        self.addToolBar(toolbar)
        
        self.new_btn = QPushButton(self.i18n.get_string("main_window.new_project", "New Project"))
        self.new_btn.clicked.connect(self._new_project)
        self.new_btn.setToolTip(self.i18n.get_string("main_window.new_project_tooltip", "Create a new project"))
        toolbar.addWidget(self.new_btn)
        
        self.open_btn = QPushButton(self.i18n.get_string("main_window.open_project", "Open Project"))
        self.open_btn.clicked.connect(self._open_project)
        self.open_btn.setToolTip(self.i18n.get_string("main_window.open_project_tooltip", "Open an existing project"))
        toolbar.addWidget(self.open_btn)
        
        toolbar.addSeparator()
        
        self.import_btn = QPushButton(self.i18n.get_string("main_window.import_images", "Import Images"))
        self.import_btn.clicked.connect(self.image_browser.import_images)
        self.import_btn.setToolTip(self.i18n.get_string("main_window.import_images_tooltip", "Import images to current project"))
        toolbar.addWidget(self.import_btn)
        
    def _setup_statusbar(self):
        """Setup status bar"""
        status_bar = QStatusBar()
        status_bar.addPermanentWidget(self.status_progress)
        self.setStatusBar(status_bar)
        status_bar.showMessage(self.i18n.get_string("main_window.ready", "Ready"))
        
    @Slot()
    def _new_project(self):
        """Create new project"""
        dialog = NewProjectDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            project_name = dialog.get_project_name()
            if project_name:
                project_dir = self.path_manager.create_project_dir(project_name)
                self.current_project = project_dir
                self.image_browser.set_project_directory(project_dir)
                self.statusBar().showMessage(
                    self.i18n.get_string("main_window.project_created", "Created new project: {}").format(os.path.basename(project_dir))
                )

    @Slot()
    def _open_project(self):
        """Open existing project"""
        dialog = QFileDialog()
        project_path, _ = dialog.getOpenFileName(
            self,
            self.i18n.get_string("main_window.open_project", "Open Project"),
            os.path.expanduser("~/Desktop"),
            self.i18n.get_string("main_window.project_file", "MicroAI-Colony Project (*.maip)")
        )
        
        if project_path:
            project_dir = os.path.splitext(project_path)[0]
            if os.path.isdir(project_dir):
                self.current_project = project_dir
                self.image_browser.set_project_directory(project_dir)
                self.statusBar().showMessage(
                    self.i18n.get_string("main_window.project_opened", "Opened project: {}").format(os.path.basename(project_dir))
                )
            else:
                QMessageBox.warning(
                    self,
                    self.i18n.get_string("main_window.error", "Error"),
                    self.i18n.get_string("main_window.project_not_found", "Project directory not found: {}").format(project_dir)
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
            self.btn_analyze.setText(self.i18n.get_string("main_window.analyze_image", "Analyze Image"))
            self.iterations_spin.setEnabled(True)
        else:
            self.btn_single.setChecked(False)
            self.btn_batch.setChecked(True)
            self.btn_analyze.setText(self.i18n.get_string("main_window.start_batch_analysis", "Start Batch Analysis"))
            self.iterations_spin.setEnabled(False)
    
    @Slot()
    def _start_analysis(self):
        """Start analysis based on current mode"""
        self.btn_analyze.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.analysis_progress.setVisible(True)
        self.progress_label.setText(self.i18n.get_string("main_window.analysis_in_progress", "Analysis in progress..."))
        
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
        self.progress_label.setText(self.i18n.get_string("main_window.analysis_stopped", "Analysis stopped"))
        
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
                self.i18n.get_string("main_window.images_loaded", "Ready - {} images loaded").format(count)
            )
        else:
            self.statusBar().showMessage(self.i18n.get_string("main_window.ready", "Ready"))
