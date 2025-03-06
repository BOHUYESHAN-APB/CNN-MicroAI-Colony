import logging
from pathlib import Path
import cv2
import pandas as pd
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                            QPushButton, QLabel, QFileDialog, QMessageBox,
                            QProgressBar, QSpinBox, QCheckBox, QMenu,
                            QDialog, QLineEdit, QDialogButtonBox)
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QPixmap, QAction

from app_pyside6.gui.base_window import BaseWindow
from app_pyside6.gui.image_list_widget import ImageListWidget
from app_pyside6.gui.result_viewer import ResultViewer
from app_pyside6.gui.settings_dialog import SettingsDialog
from app_pyside6.utils.i18n import i18n
from app_pyside6.models.inference import ModelInference
from app_pyside6.utils.batch_analyzer import BatchAnalyzer

logger = logging.getLogger(__name__)

class NewProjectDialog(QDialog):
    """Dialog for creating new project"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(i18n.get('dialogs.new_project'))
        self.setup_ui()
        
    def setup_ui(self):
        """Initialize user interface"""
        layout = QVBoxLayout(self)
        
        # Project name input
        form_layout = QVBoxLayout()
        form_layout.addWidget(QLabel(i18n.get('labels.project_name')))
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

class BatchAnalysisThread(QThread):
    """Thread for batch analysis"""
    progress = Signal(int)
    finished = Signal(dict)
    error = Signal(str)

    def __init__(self, model, image_paths, num_runs, analyzer):
        super().__init__()
        self.model = model
        self.image_paths = image_paths
        self.num_runs = num_runs
        self.analyzer = analyzer

    def run(self):
        try:
            results = self.analyzer.run_analysis(
                self.model,
                self.image_paths,
                self.num_runs,
                self.progress.emit
            )
            # Check result format
            if not results or not all('dataframe' in v for v in results.values()):
                raise ValueError("Invalid result format")
            self.finished.emit(results)
        except Exception as e:
            logger.error(f"Batch analysis error: {e}")
            self.error.emit(str(e))

class MainWindow(BaseWindow):
    """Main application window"""
    
    def __init__(self, config):
        super().__init__(config)
        self.model = None
        self.current_results = None
        self.analyzer = BatchAnalyzer(config, self.path_manager)
        self.batch_thread = None
        self.setup_ui()
        self.init_model()

        # Schedule load_last_project to run after event loop starts
        QTimer.singleShot(0, self.load_last_project)

    def setup_ui(self):
        """Initialize user interface"""
        # Main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Menu bar
        self.setup_menu()

        # Project controls
        project_layout = QHBoxLayout()
        self.new_project_btn = QPushButton(i18n.get('buttons.new_project'))
        self.new_project_btn.clicked.connect(self.new_project)
        project_layout.addWidget(self.new_project_btn)
        
        self.open_project_btn = QPushButton(i18n.get('buttons.open_project'))
        self.open_project_btn.clicked.connect(self.open_project)
        project_layout.addWidget(self.open_project_btn)
        
        self.project_label = QLabel(i18n.get('labels.no_project'))
        project_layout.addWidget(self.project_label)
        project_layout.addStretch()
        
        layout.addLayout(project_layout)

        # Main area split into preview and list
        main_layout = QHBoxLayout()
        
        # Left side: Image preview
        preview_layout = QVBoxLayout()
        self.preview_label = QLabel()
        self.preview_label.setMinimumSize(400, 300)
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setText(i18n.get('labels.no_preview'))
        preview_layout.addWidget(self.preview_label)
        main_layout.addLayout(preview_layout)
        
        # Right side: Image list and controls
        list_layout = QVBoxLayout()
        
        # Image list controls
        list_controls = QHBoxLayout()
        self.add_image_btn = QPushButton(i18n.get('buttons.add'))
        self.add_image_btn.clicked.connect(self.add_images)
        self.add_image_btn.setEnabled(False)
        list_controls.addWidget(self.add_image_btn)
        
        self.clear_btn = QPushButton(i18n.get('buttons.clear'))
        self.clear_btn.clicked.connect(self.clear_images)
        self.clear_btn.setEnabled(False)
        list_controls.addWidget(self.clear_btn)
        
        list_layout.addLayout(list_controls)
        
        # Image list
        self.image_list = ImageListWidget()
        self.image_list.image_selected.connect(self.on_image_selected)
        self.setup_context_menu()  # Add context menu
        list_layout.addWidget(self.image_list)
        main_layout.addLayout(list_layout)
        
        layout.addLayout(main_layout)

        # Control panel
        control_layout = QHBoxLayout()
        
        # Batch analysis controls
        batch_layout = QHBoxLayout()
        self.batch_checkbox = QCheckBox(i18n.get('labels.batch_analysis'))
        self.batch_checkbox.stateChanged.connect(self.toggle_batch_controls)
        batch_layout.addWidget(self.batch_checkbox)

        self.runs_spinbox = QSpinBox()
        self.runs_spinbox.setRange(10, 10000)
        self.runs_spinbox.setValue(100)
        self.runs_spinbox.setEnabled(False)
        
        self.runs_label = QLabel(i18n.get('labels.runs'))
        batch_layout.addWidget(self.runs_label)
        batch_layout.addWidget(self.runs_spinbox)
        control_layout.addLayout(batch_layout)

        # Process button
        self.process_button = QPushButton(i18n.get('buttons.process'))
        self.process_button.clicked.connect(self.process_images)
        self.process_button.setEnabled(False)
        control_layout.addWidget(self.process_button)

        # View results button
        self.view_results_button = QPushButton(i18n.get('buttons.view'))
        self.view_results_button.clicked.connect(self.show_results)
        self.view_results_button.setEnabled(False)
        control_layout.addWidget(self.view_results_button)

        layout.addLayout(control_layout)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # Status label
        self.status_label = QLabel(i18n.get('status.ready'))
        layout.addWidget(self.status_label)

        # Load settings
        self.load_settings()

        # Set window title
        self.update_window_title()

    def setup_context_menu(self):
        """Setup context menu for image list"""
        self.image_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.image_list.customContextMenuRequested.connect(self.show_context_menu)

    def show_context_menu(self, position):
        """Show context menu for image list"""
        selected_items = self.image_list.selectedItems()
        if not selected_items:
            return
            
        menu = QMenu()
        
        remove_action = menu.addAction(i18n.get('menu.remove_image'))
        remove_action.triggered.connect(self.remove_selected_image)
        
        if self.current_results:
            view_action = menu.addAction(i18n.get('menu.view_results'))
            view_action.triggered.connect(lambda: self.show_single_result(
                selected_items[0].data(Qt.UserRole)
            ))
        
        menu.exec_(self.image_list.mapToGlobal(position))

    def remove_selected_image(self):
        """Remove selected image from list"""
        selected_items = self.image_list.selectedItems()
        if not selected_items:
            return
            
        for item in selected_items:
            row = self.image_list.row(item)
            self.image_list.takeItem(row)
        
        # Reset UI if no images left
        if self.image_list.count() == 0:
            self.clear_btn.setEnabled(False)
            self.process_button.setEnabled(False)
            self.view_results_button.setEnabled(False)
            self.preview_label.setText(i18n.get('labels.no_preview'))
            self.preview_label.setPixmap(QPixmap())

    def show_single_result(self, image_path: str):
        """Show results for single image"""
        if not self.current_results or image_path not in self.current_results:
            return
            
        result = self.current_results[image_path]
        if 'error' in result:
            QMessageBox.warning(
                self,
                i18n.get('errors.view_failed'),
                result['error']
            )
            return
            
        try:
            dialog = ResultViewer(
                {image_path: result},
                self.batch_checkbox.isChecked(),
                parent=self
            )
            dialog.exec_()
        except Exception as e:
            logger.error(f"Failed to show results: {e}")
            QMessageBox.critical(
                self,
                i18n.get('errors.view_failed'),
                str(e)
            )

    def new_project(self):
        """Create new project"""
        dialog = NewProjectDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            project_name = dialog.get_project_name()
            if project_name:
                try:
                    project_dir = self.path_manager.create_project(project_name)
                    self._reset_workspace()
                    self.project_label.setText(i18n.get('labels.current_project', name=project_name))
                    self.update_window_title()
                    QMessageBox.information(
                        self,
                        i18n.get('dialogs.project_created'),
                        i18n.get('dialogs.project_created_message', path=str(project_dir))
                    )
                except Exception as e:
                    logger.error(f"Failed to create project: {e}")
                    QMessageBox.critical(
                        self,
                        i18n.get('errors.project_creation_failed'),
                        str(e)
                    )

    def _reset_workspace(self):
        """Reset workspace for new/opened project"""
        self.image_list.clear()
        self.preview_label.setText(i18n.get('labels.no_preview'))
        self.preview_label.setPixmap(QPixmap())  # Use empty QPixmap instead of None
        self.add_image_btn.setEnabled(True)
        self.clear_btn.setEnabled(False)
        self.process_button.setEnabled(False)
        self.view_results_button.setEnabled(False)
        self.current_results = None
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        self.status_label.setText(i18n.get('status.ready'))

    def open_project(self):
        """Open existing project"""
        dir_path = QFileDialog.getExistingDirectory(
            self,
            i18n.get('dialogs.open_project'),
            str(self.path_manager.base_dir)
        )
        if dir_path:
            try:
                project_dir = self.path_manager.load_project(dir_path)
                self._reset_workspace()
                project_name = self.config.get('project.name', Path(dir_path).name)
                self.project_label.setText(i18n.get('labels.current_project', name=project_name))
                self.update_window_title()
                
                # Load existing images
                pic_dir = project_dir / "PIC"
                if pic_dir.exists():
                    images = [str(p) for p in pic_dir.glob("*") if p.suffix.lower() in ['.jpg', '.jpeg', '.png']]
                    if images:
                        self.image_list.add_images(images)
                        
            except Exception as e:
                logger.error(f"Failed to open project: {e}")
                QMessageBox.critical(
                    self,
                    i18n.get('errors.project_open_failed'),
                    str(e)
                )

    def load_last_project(self):
        """Load last active project if any"""
        last_project = self.config.get('project.current')
        if last_project:
            try:
                self.path_manager.load_project(last_project)
                project_name = self.config.get('project.name', Path(last_project).name)
                self.project_label.setText(i18n.get('labels.current_project', name=project_name))
                self.add_image_btn.setEnabled(True)
                self.update_window_title()
                
                # Load existing images
                pic_dir = Path(last_project) / "PIC"
                if pic_dir.exists():
                    images = [str(p) for p in pic_dir.glob("*") if p.suffix.lower() in ['.jpg', '.jpeg', '.png']]
                    if images:
                        self.image_list.add_images(images)
                        
            except Exception as e:
                logger.warning(f"Failed to load last project: {e}")

    def setup_menu(self):
        """Setup menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu(i18n.get('menu.file'))
        
        new_project_action = QAction(i18n.get('menu.new_project'), self)
        new_project_action.triggered.connect(self.new_project)
        file_menu.addAction(new_project_action)
        
        open_project_action = QAction(i18n.get('menu.open_project'), self)
        open_project_action.triggered.connect(self.open_project)
        file_menu.addAction(open_project_action)
        
        file_menu.addSeparator()
        
        settings_action = QAction(i18n.get('menu.settings'), self)
        settings_action.triggered.connect(self.show_settings)
        file_menu.addAction(settings_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction(i18n.get('menu.exit'), self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

    def show_settings(self):
        """Show settings dialog"""
        dialog = SettingsDialog(self.config, self)
        if dialog.exec_():
            self.load_settings()
            self.retranslate_ui()

    def add_images(self):
        """Add images to project"""
        if not self.path_manager.has_active_project:
            QMessageBox.warning(
                self,
                i18n.get('errors.no_project'),
                i18n.get('errors.no_project_message')
            )
            return
            
        files, _ = QFileDialog.getOpenFileNames(
            self,
            i18n.get('dialogs.select_images'),
            str(Path.home()),
            "Images (*.jpg *.jpeg *.png);;All Files (*.*)"
        )
        
        if files:
            try:
                # Import images to project
                imported = self.path_manager.import_images(files)
                if imported:
                    self.image_list.add_images([str(p) for p in imported])
                    self.clear_btn.setEnabled(True)
            except Exception as e:
                logger.error(f"Failed to add images: {e}")
                QMessageBox.critical(
                    self,
                    i18n.get('errors.import_failed'),
                    str(e)
                )

    def clear_images(self):
        """Clear image list"""
        if QMessageBox.question(
            self,
            i18n.get('dialogs.confirm'),
            i18n.get('dialogs.clear_images_confirm'),
            QMessageBox.Yes | QMessageBox.No
        ) == QMessageBox.Yes:
            self._reset_workspace()

    def init_model(self):
        """Initialize model"""
        try:
            if self.config.get('model.demo_mode', False):
                logger.info("Starting in demo mode")
                self.model = ModelInference(self.config)
            else:
                self.model = ModelInference(self.config)
            logger.info("Model initialized successfully")
        except Exception as e:
            logger.error(f"Model initialization failed: {e}")
            QMessageBox.critical(
                self,
                i18n.get('errors.model_init_failed'),
                str(e)
            )
            self.config.set('model.demo_mode', True)
            self.config.save()
            try:
                self.model = ModelInference(self.config)
                logger.info("Fallback to demo mode successful")
                QMessageBox.information(
                    self,
                    i18n.get('info.demo_mode'),
                    i18n.get('info.demo_mode_message')
                )
            except Exception as retry_error:
                logger.critical(f"Demo mode fallback failed: {retry_error}")
                raise

    def process_images(self):
        """Process selected images"""
        if not self.path_manager.has_active_project:
            QMessageBox.warning(
                self,
                i18n.get('errors.no_project'),
                i18n.get('errors.no_project_message')
            )
            return
            
        images = self.image_list.get_images()
        if not images:
            QMessageBox.warning(
                self,
                i18n.get('errors.no_images_selected'),
                i18n.get('errors.no_images_selected')
            )
            return

        self.disable_controls()

        if self.batch_checkbox.isChecked():
            self.run_batch_analysis(images)
        else:
            self.run_single_analysis(images)

    def run_batch_analysis(self, images):
        """Run batch analysis on images"""
        num_runs = self.runs_spinbox.value()
        if num_runs < 10 or num_runs > 10000:
            self.handle_error(i18n.get('errors.invalid_batch'))
            return

        # Create and start analysis thread
        self.batch_thread = BatchAnalysisThread(
            self.model,
            images,
            num_runs,
            self.analyzer
        )
        self.batch_thread.progress.connect(self.update_progress)
        self.batch_thread.finished.connect(self.batch_analysis_finished)
        self.batch_thread.error.connect(self.handle_error)
        self.batch_thread.start()

    def run_single_analysis(self, images):
        """Run single analysis on images"""
        try:
            results = {}
            total = len(images)
            
            for i, path in enumerate(images, 1):
                self.status_label.setText(
                    i18n.get('status.processing_image', name=Path(path).name)
                )
                self.update_progress(int(100 * i / total))

                image = cv2.imread(path)
                if image is None:
                    raise ValueError(f"Failed to load image: {path}")
                
                result = self.model.predict(image)
                results[path] = {
                    'dataframe': pd.DataFrame([result]),
                    'output_dir': self.path_manager.get_image_output_dir(path)
                }

            self.current_results = results
            self.processing_finished()

        except Exception as e:
            self.handle_error(str(e))

    def show_results(self):
        """Show results viewer"""
        if not self.current_results:
            QMessageBox.warning(
                self,
                i18n.get('errors.no_results'),
                i18n.get('errors.no_results_message')
            )
            return

        try:
            # For multiple images
            if len(self.current_results) > 1:
                dialog = ResultViewer(
                    self.current_results,
                    True,  # Always use batch mode for multiple images
                    parent=self
                )
            else:
                # For single image
                dialog = ResultViewer(
                    self.current_results,
                    self.batch_checkbox.isChecked(),
                    parent=self
                )
            dialog.exec_()
            
        except Exception as e:
            logger.error(f"Failed to show results: {e}")
            QMessageBox.critical(
                self,
                i18n.get('errors.view_failed'),
                str(e)
            )

    def batch_analysis_finished(self, results):
        """Handle batch analysis completion"""
        self.current_results = results
        self.processing_finished()
        
        # Clean up thread
        if self.batch_thread:
            self.batch_thread.quit()
            self.batch_thread.wait()
            self.batch_thread.deleteLater()
            self.batch_thread = None

        QMessageBox.information(
            self,
            i18n.get('dialogs.analysis_complete'),
            i18n.get('dialogs.analysis_complete_message')
        )

    def update_progress(self, value):
        """Update progress bar"""
        self.progress_bar.setValue(value)
        if value > 0:
            self.progress_bar.setFormat(f"{value}%")

    def processing_finished(self):
        """Handle processing completion"""
        self.enable_controls()
        if self.current_results:
            for path, result in self.current_results.items():
                self.image_list.mark_processed(
                    path,
                    'error' not in result
                )
            self.view_results_button.setEnabled(True)

    def disable_controls(self):
        """Disable all controls during processing"""
        self.process_button.setEnabled(False)
        self.batch_checkbox.setEnabled(False)
        self.runs_spinbox.setEnabled(False)
        self.view_results_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_label.setText(i18n.get('status.processing'))

    def enable_controls(self):
        """Enable controls after processing"""
        self.process_button.setEnabled(True)
        self.batch_checkbox.setEnabled(True)
        self.runs_spinbox.setEnabled(self.batch_checkbox.isChecked())
        self.progress_bar.setVisible(False)
        self.status_label.setText(i18n.get('status.complete'))

    def handle_error(self, error_message: str):
        """Handle processing errors"""
        self.enable_controls()
        QMessageBox.critical(
            self,
            i18n.get('errors.process_failed'),
            error_message
        )
        self.status_label.setText(i18n.get('status.error'))

    def toggle_batch_controls(self, state):
        """Enable/disable batch analysis controls"""
        is_batch = state == Qt.Checked
        self.runs_spinbox.setEnabled(is_batch)
        self.process_button.setText(
            i18n.get('buttons.start_batch') if is_batch 
            else i18n.get('buttons.process')
        )
        
    def on_image_selected(self, path: str):
        """Handle image selection"""
        try:
            pixmap = QPixmap(path)
            if not pixmap.isNull():
                preview_size = self.preview_label.size()
                scaled_pixmap = pixmap.scaled(
                    preview_size,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                self.preview_label.setPixmap(scaled_pixmap)
                self.process_button.setEnabled(True)
                self.status_label.setText(
                    i18n.get('status.loading', name=Path(path).name)
                )
        except Exception as e:
            logger.error(f"Failed to load image: {e}")
            self.status_label.setText(i18n.get('errors.load_failed'))

    def closeEvent(self, event):
        """Handle window close"""
        # Clean up batch thread if running
        if self.batch_thread:
            self.batch_thread.quit()
            self.batch_thread.wait()
            self.batch_thread.deleteLater()
            
        # Save application state
        self.config.save()
        
        super().closeEvent(event)
        
    def update_window_title(self):
        """Update window title with project name"""
        title = i18n.get('app.name')
        if self.path_manager.has_active_project:
            project_name = self.config.get('project.name', '')
            if project_name:
                title += f" - {project_name}"
        self.setWindowTitle(title)
        
    def load_settings(self):
        """Load settings from config"""
        # Update runs spinbox range and value
        min_runs = max(10, min(self.config.get('analysis.batch.min_runs', 10), 10000))
        max_runs = min(10000, max(self.config.get('analysis.batch.max_runs', 10000), min_runs))
        self.runs_spinbox.setRange(min_runs, max_runs)
        default_runs = min(max(
            self.config.get('analysis.batch.default_runs', 100),
            min_runs
        ), max_runs)
        self.runs_spinbox.setValue(default_runs)
        self.runs_spinbox.setEnabled(self.batch_checkbox.isChecked())

    def retranslate_ui(self):
        """Update interface language"""
        super().retranslate_ui()
        # Update all text elements
        self.preview_label.setText(i18n.get('labels.no_preview'))
        self.batch_checkbox.setText(i18n.get('labels.batch_analysis'))
        self.runs_label.setText(i18n.get('labels.runs'))
        self.process_button.setText(
            i18n.get('buttons.start_batch')
            if self.batch_checkbox.isChecked()
            else i18n.get('buttons.process')
        )
        self.view_results_button.setText(i18n.get('buttons.view'))
        self.status_label.setText(i18n.get('status.ready'))
        self.new_project_btn.setText(i18n.get('buttons.new_project'))
        self.open_project_btn.setText(i18n.get('buttons.open_project'))
        self.add_image_btn.setText(i18n.get('buttons.add'))
        self.clear_btn.setText(i18n.get('buttons.clear'))
        self.image_list.retranslate_ui()
        self.update_window_title()
