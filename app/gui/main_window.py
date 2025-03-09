"""
Main Window
"""
import os
import logging
from typing import Optional

from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QPushButton,
                            QMessageBox, QFileDialog, QLabel, QDialog)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QIcon

from ..utils.i18n import tr
from ..utils.project_manager import ProjectManager
from ..utils.theme_manager import ThemeManager
from ..utils.path_manager import get_resources_dir
from .project_dialog import NewProjectDialog, OpenProjectDialog
from .image_list_widget import ImageListWidget
from .result_visualizer import ResultVisualizer
from .settings_dialog import SettingsDialog
from .about_dialog import AboutDialog

logger = logging.getLogger(__name__)

class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.project_manager = ProjectManager()
        self.theme_manager = ThemeManager()
        self.setup_ui()
        
    def setup_ui(self):
        """Setup user interface"""
        self.setWindowTitle(tr("main.title"))
        self.resize(1200, 800)
        
        # Set window icon
        icon_path = os.path.join(get_resources_dir(), "icons", "app.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        
        layout = QVBoxLayout()
        central.setLayout(layout)
        
        # Image browser
        self.image_browser = ImageListWidget()
        self.image_browser.image_selected.connect(self.on_image_selected)
        layout.addWidget(self.image_browser)
        
        # Result viewer
        self.result_viewer = ResultVisualizer()
        layout.addWidget(self.result_viewer)
        
        # Setup menus
        self.setup_menus()
        
        # Update UI state
        self.update_ui_for_project()
        
    def setup_menus(self):
        """Setup application menus"""
        # Create and save the menubar for access
        self.menu_bar = self.menuBar()
        
        # File menu
        file_menu = self.menu_bar.addMenu(tr("menu.file"))
        
        new_project = QAction(tr("menu.file.new_project"), self)
        new_project.triggered.connect(self.new_project)
        file_menu.addAction(new_project)
        
        open_project = QAction(tr("menu.file.open_project"), self)
        open_project.triggered.connect(self.open_project)
        file_menu.addAction(open_project)
        
        self.close_project_action = QAction(tr("menu.file.close_project"), self)
        self.close_project_action.triggered.connect(self.close_project)
        file_menu.addAction(self.close_project_action)
        
        file_menu.addSeparator()
        
        settings = QAction(tr("menu.file.settings"), self)
        settings.triggered.connect(self.show_settings)
        file_menu.addAction(settings)
        
        file_menu.addSeparator()
        
        quit_action = QAction(tr("menu.file.quit"), self)
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)
        
        # Image menu
        self.image_menu = self.menu_bar.addMenu(tr("menu.image"))
        
        add_images = QAction(tr("menu.image.add"), self)
        add_images.triggered.connect(self.add_images)
        self.image_menu.addAction(add_images)
        
        clear_images = QAction(tr("menu.image.clear"), self)
        clear_images.triggered.connect(self.clear_images)
        self.image_menu.addAction(clear_images)
        
        # Analysis menu
        self.analysis_menu = self.menu_bar.addMenu(tr("menu.analysis"))
        
        start_analysis = QAction(tr("menu.analysis.start"), self)
        start_analysis.triggered.connect(self.start_analysis)
        self.analysis_menu.addAction(start_analysis)
        
        export_results = QAction(tr("menu.analysis.export"), self)
        export_results.triggered.connect(self.export_results)
        self.analysis_menu.addAction(export_results)
        
        # Help menu
        help_menu = self.menu_bar.addMenu(tr("menu.help"))
        
        about = QAction(tr("menu.help.about"), self)
        about.triggered.connect(self.show_about)
        help_menu.addAction(about)

        # Language menu
        language_menu = self.menu_bar.addMenu(tr("menu.language"))

        locale_texts = {
            "en": "English",
            "zh_CN": "中文 (简体)",
            "zh_TW": "中文 (繁體)"
        }
        for locale, text in locale_texts.items():
            action = QAction(text, self)
            action.triggered.connect(lambda checked, loc=locale: self.on_language_changed(loc))
            language_menu.addAction(action)

    def on_language_changed(self, locale: str):
        """Change application language"""
        self.change_language(locale)

    def change_language(self, locale: str):
        """Change application language"""
        from ..utils.i18n import set_locale
        if not set_locale(locale):
            QMessageBox.critical(
                self,
                tr("dialog.error"),
                tr("error.language_change_failed", locale=locale)
            )
            return

        # Store current menu visibility states
        menu_states = {
            'close_project': self.close_project_action.isEnabled(),
            'image_menu': self.image_menu.isEnabled(),
            'analysis_menu': self.analysis_menu.isEnabled()
        }

        # Close and recreate any open dialogs
        open_dialogs = self.findChildren(QDialog)
        dialog_positions = {}  # Not used currently, but could be used to restore dialog positions
        for dialog in open_dialogs:
            dialog_positions[dialog.__class__.__name__] = dialog.pos()
            dialog.close()

        # Clear and recreate all menus with new translations
        self.menu_bar.clear()
        self.setup_menus()

        # Restore menu states
        self.close_project_action.setEnabled(menu_states['close_project'])
        self.image_menu.setEnabled(menu_states['image_menu'])
        self.analysis_menu.setEnabled(menu_states['analysis_menu'])

        # Update window title
        if self.project_manager.get_project_path():  # Removed has_project assignment
            info = self.project_manager.get_project_info()
            self.setWindowTitle(f"{tr('main.title')} - {info.get('name', '')}")
        else:
            self.setWindowTitle(tr("main.title"))

        self.show_status_message(tr("status.language_changed", locale=locale))
        self.retranslate_ui()

    def retranslate_ui(self):
        """Retranslate UI elements"""
        # Update window title
        if self.project_manager.get_project_path():
            info = self.project_manager.get_project_info()
            self.setWindowTitle(f"{tr('main.title')} - {info.get('name', '')}")
        else:
            self.setWindowTitle(tr("main.title"))

        # The menu is already updated in change_language
        # Add calls to child widgets' retranslateUi methods here
        self.image_browser.retranslateUi()
        self.result_viewer.retranslateUi()

    def new_project(self):
        """Create new project"""
        dialog = NewProjectDialog(self)
        if dialog.exec():
            name, path = dialog.get_project_info()
            if self.project_manager.create_project(name, path):
                self.update_ui_for_project()
                self.show_status_message(tr("status.project_created"))
            else:
                QMessageBox.critical(
                    self,
                    tr("dialog.error"),
                    tr("error.create_project")
                )
                
    def open_project(self):
        """Open existing project"""
        dialog = OpenProjectDialog(self)
        if dialog.exec():
            path = dialog.get_project_path()
            if self.project_manager.open_project(path):
                self.update_ui_for_project()
                self.show_status_message(tr("status.project_opened"))
            else:
                QMessageBox.critical(
                    self,
                    tr("dialog.error"),
                    tr("error.open_project")
                )
                
    def close_project(self):
        """Close current project"""
        if self.project_manager.close_project():
            self.update_ui_for_project()
            self.show_status_message(tr("status.project_closed"))
        else:
            QMessageBox.critical(
                self,
                tr("dialog.error"),
                tr("error.close_project")
            )
            
    def add_images(self):
        """Add images to project"""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            tr("dialog.select_images"),
            "",
            tr("dialog.image_filter")
        )
        
        if files:
            added = 0
            for file in files:
                if self.project_manager.add_image(file):
                    added += 1
                    
            if added > 0:
                self.update_ui_for_project()
                self.show_status_message(
                    tr("status.images_added").format(count=added)
                )
                
    def clear_images(self):
        """Clear all images"""
        reply = QMessageBox.question(
            self,
            tr("dialog.warning"),
            tr("dialog.clear_images_confirm"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.image_browser.clear()
            self.show_status_message(tr("status.images_cleared"))
            
    def start_analysis(self):
        """Start image analysis"""
        if image := self.image_browser.get_selected_image():
            self.result_viewer.load_image(image)
            self.result_viewer.start_analysis()
            
    def export_results(self):
        """Export analysis results"""
        self.result_viewer.export_results()
        
    def show_settings(self):
        """Show settings dialog"""
        dialog = SettingsDialog(self)
        dialog.exec()
        
    def show_about(self):
        """Show about dialog"""
        dialog = AboutDialog(self)
        dialog.exec()
        
    def update_ui_for_project(self):
        """Update UI based on project state"""
        has_project = self.project_manager.get_project_path() is not None
        
        # Update window title
        if has_project:
            info = self.project_manager.get_project_info()
            self.setWindowTitle(f"{tr('main.title')} - {info.get('name', '')}")
        else:
            self.setWindowTitle(tr("main.title"))
            
        # Update menu states
        self.close_project_action.setEnabled(has_project)
        self.image_menu.setEnabled(has_project)
        self.analysis_menu.setEnabled(has_project)
        
        # Update image browser
        self.image_browser.clear()
        if has_project:
            for image in self.project_manager.get_images():
                self.image_browser.add_image(image["path"])
                
    def on_image_selected(self, path: str):
        """Handle image selection"""
        self.result_viewer.load_image(path)
        
    def show_status_message(self, message: str):
        """Show status bar message"""
        self.statusBar().showMessage(message, 3000)
        
    def closeEvent(self, event):
        """Handle window close event"""
        if self.project_manager.get_project_path():
            reply = QMessageBox.question(
                self,
                tr("dialog.warning"),
                tr("dialog.close_project_confirm"),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.No:
                event.ignore()
                return
                
            self.project_manager.close_project()
            
        event.accept()
