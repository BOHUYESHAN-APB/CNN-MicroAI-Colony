"""
Settings Dialog for application preferences
"""
import logging
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
                            QPushButton, QWidget, QFormLayout, QLabel,
                            QComboBox, QSpinBox, QDoubleSpinBox, QCheckBox,
                            QLineEdit, QFileDialog, QMessageBox)
from PyQt6.QtCore import Qt

from ..utils.i18n import tr, get_locales, set_locale
from ..utils.config import ConfigManager
from ..utils.path_manager import get_default_project_path
from ..utils.theme_manager import ThemeManager

logger = logging.getLogger(__name__)

class SettingsDialog(QDialog):
    """Application settings dialog"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.config = ConfigManager()
        self.theme = ThemeManager()
        self.tabs = None  # Store reference to tabs
        self.language_combo = None
        self.path_edit = None
        self.autosave_check = None
        self.theme_combo = None
        self.maximized_check = None
        self.statusbar_check = None
        self.confidence_spin = None
        self.min_size_spin = None
        self.max_size_spin = None
        self.gpu_check = None
        
        self.setup_ui()
        self.load_settings()

    def rebuild_ui(self):
        """Rebuild UI with new translations"""
        # Store current values
        current_values = self.get_current_values()
        
        # Clear layout
        self.layout().removeWidget(self.tabs)
        self.tabs.deleteLater()
        self.tabs = None
        
        # Rebuild UI
        self.setup_ui()
        
        # Restore values
        self.set_values(current_values)

    def get_current_values(self):
        """Get current values from UI elements"""
        return {
            'language': self.language_combo.currentData(),
            'path': self.path_edit.text(),
            'auto_save': self.autosave_check.isChecked(),
            'theme': self.theme_combo.currentData(),
            'maximized': self.maximized_check.isChecked(),
            'status_bar': self.statusbar_check.isChecked(),
            'confidence': self.confidence_spin.value(),
            'min_size': self.min_size_spin.value(),
            'max_size': self.max_size_spin.value(),
            'use_gpu': self.gpu_check.isChecked()
        }
        
    def set_values(self, values):
        """Set values to UI elements"""
        # General settings
        index = self.language_combo.findData(values['language'])
        if index >= 0:
            self.language_combo.setCurrentIndex(index)
        self.path_edit.setText(values['path'])
        self.autosave_check.setChecked(values['auto_save'])
        
        # Display settings
        index = self.theme_combo.findData(values['theme'])
        if index >= 0:
            self.theme_combo.setCurrentIndex(index)
        self.maximized_check.setChecked(values['maximized'])
        self.statusbar_check.setChecked(values['status_bar'])
        
        # Analysis settings
        self.confidence_spin.setValue(values['confidence'])
        self.min_size_spin.setValue(values['min_size'])
        self.max_size_spin.setValue(values['max_size'])
        self.gpu_check.setChecked(values['use_gpu'])
        
    def setup_ui(self):
        """Setup user interface"""
        self.setWindowTitle(tr("settings.title"))
        self.resize(500, 400)
        
        if not self.layout():
            layout = QVBoxLayout()
            self.setLayout(layout)
            
        # Create tab widget
        self.tabs = QTabWidget()
        
        # Add tabs
        self.tabs.addTab(self.create_general_tab(), tr("settings.tab.general"))
        self.tabs.addTab(self.create_display_tab(), tr("settings.tab.display"))
        self.tabs.addTab(self.create_analysis_tab(), tr("settings.tab.analysis"))
        
        self.layout().addWidget(self.tabs)
        
        # Dialog buttons
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton(tr("dialog.ok"))
        ok_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton(tr("dialog.cancel"))
        cancel_btn.clicked.connect(self.reject)
        apply_btn = QPushButton(tr("dialog.apply"))
        apply_btn.clicked.connect(self.apply_settings)
        btn_layout.addStretch()
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(apply_btn)
        layout.addLayout(btn_layout)
        
    def create_general_tab(self) -> QWidget:
        """Create general settings tab"""
        tab = QWidget()
        layout = QFormLayout()
        
        # Language
        self.language_combo = QComboBox()
        locales = get_locales()
        for locale in locales:
            locale_text = {"en": "English", "zh_CN": "中文 (简体)", "zh_TW": "中文 (繁體)"}.get(locale, locale)
            self.language_combo.addItem(locale_text, locale)
        layout.addRow(tr("settings.language"), self.language_combo)
        
        # Project path
        path_layout = QHBoxLayout()
        self.path_edit = QLineEdit()
        browse_btn = QPushButton(tr("settings.browse"))
        browse_btn.clicked.connect(self.browse_path)
        path_layout.addWidget(self.path_edit)
        path_layout.addWidget(browse_btn)
        layout.addRow(tr("settings.default_path"), path_layout)
        
        # Auto-save
        self.autosave_check = QCheckBox(tr("settings.auto_save"))
        layout.addRow("", self.autosave_check)
        
        tab.setLayout(layout)
        return tab
        
    def create_display_tab(self) -> QWidget:
        """Create display settings tab"""
        tab = QWidget()
        layout = QFormLayout()
        
        # Theme
        self.theme_combo = QComboBox()
        for theme in self.theme.get_available_themes():
            self.theme_combo.addItem(theme, theme)
        layout.addRow(tr("settings.theme"), self.theme_combo)
        
        # Start maximized
        self.maximized_check = QCheckBox(tr("settings.start_maximized"))
        layout.addRow("", self.maximized_check)
        
        # Show status bar
        self.statusbar_check = QCheckBox(tr("settings.show_status_bar"))
        layout.addRow("", self.statusbar_check)
        
        tab.setLayout(layout)
        return tab
        
    def create_analysis_tab(self) -> QWidget:
        """Create analysis settings tab"""
        tab = QWidget()
        layout = QFormLayout()
        
        # Confidence threshold
        self.confidence_spin = QDoubleSpinBox()
        self.confidence_spin.setRange(0.1, 1.0)
        self.confidence_spin.setSingleStep(0.1)
        layout.addRow(tr("settings.confidence_threshold"), self.confidence_spin)
        
        # Size limits
        self.min_size_spin = QSpinBox()
        self.min_size_spin.setRange(1, 100)
        layout.addRow(tr("settings.min_size"), self.min_size_spin)
        
        self.max_size_spin = QSpinBox()
        self.max_size_spin.setRange(10, 1000)
        layout.addRow(tr("settings.max_size"), self.max_size_spin)
        
        # GPU acceleration
        self.gpu_check = QCheckBox(tr("settings.use_gpu"))
        layout.addRow("", self.gpu_check)
        
        tab.setLayout(layout)
        return tab
        
    def load_settings(self):
        """Load current settings"""
        # General settings
        locale = self.config.get("locale", "en")
        index = self.language_combo.findData(locale)
        if index >= 0:
            self.language_combo.setCurrentIndex(index)
            
        self.path_edit.setText(self.config.get("project.default_path", get_default_project_path()))
        self.autosave_check.setChecked(self.config.get("project.auto_save", True))
        
        # Display settings
        theme = self.config.get("theme.default", "siui_dark")
        index = self.theme_combo.findData(theme)
        if index >= 0:
            self.theme_combo.setCurrentIndex(index)
            
        self.maximized_check.setChecked(self.config.get("interface.start_maximized", False))
        self.statusbar_check.setChecked(self.config.get("interface.status_bar", True))
        
        # Analysis settings
        self.confidence_spin.setValue(self.config.get("analysis.confidence_threshold", 0.5))
        self.min_size_spin.setValue(self.config.get("analysis.min_size", 5))
        self.max_size_spin.setValue(self.config.get("analysis.max_size", 100))
        self.gpu_check.setChecked(self.config.get("analysis.use_gpu", True))
        
    def apply_settings(self):
        """Apply current settings"""
        # General settings
        new_locale = self.language_combo.currentData()
        if new_locale != self.config.get("locale"):
            self.config.set("locale", new_locale)
            # Let the main window handle language switching
            self.parent().change_language(new_locale)
            
        self.config.set("project.default_path", self.path_edit.text())
        self.config.set("project.auto_save", self.autosave_check.isChecked())
        
        # Display settings
        new_theme = self.theme_combo.currentData()
        if new_theme != self.config.get("theme.default"):
            self.config.set("theme.default", new_theme)
            self.theme.apply_theme(new_theme)
            
        self.config.set("interface.start_maximized", self.maximized_check.isChecked())
        self.config.set("interface.status_bar", self.statusbar_check.isChecked())
        
        # Analysis settings
        self.config.set("analysis.confidence_threshold", self.confidence_spin.value())
        self.config.set("analysis.min_size", self.min_size_spin.value())
        self.config.set("analysis.max_size", self.max_size_spin.value())
        self.config.set("analysis.use_gpu", self.gpu_check.isChecked())
        
        # Save changes
        self.config.save()
        
    def browse_path(self):
        """Open directory browser"""
        path = QFileDialog.getExistingDirectory(
            self,
            tr("settings.select_project_dir"),
            self.path_edit.text()
        )
        if path:
            self.path_edit.setText(path)
            
    def accept(self):
        """Handle dialog accept"""
        self.apply_settings()
        super().accept()
