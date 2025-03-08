import os
import logging
from pathlib import Path
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QFileDialog, QCheckBox, QSpinBox,
    QGroupBox, QPushButton, QDialogButtonBox, QComboBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from ..utils.config import ConfigManager
from ..utils.i18n import get_i18n

logger = logging.getLogger(__name__)

class SettingsDialog(QDialog):
    language_changed = Signal(str)  # 定义信号

    def __init__(self, parent=None):
        super().__init__(parent)
        logger.info("Initializing SettingsDialog")
        
        self.config = ConfigManager()
        self.i18n = get_i18n()
        
        self.setWindowTitle(self.tr("Settings"))
        self.resize(500, 400)
        
        self._setup_ui()
        self._load_settings()
        logger.info("SettingsDialog initialization complete")
        
    def _setup_ui(self):
        """Setup dialog UI"""
        layout = QVBoxLayout()
        
        # Project Settings
        project_group = QGroupBox(self.tr("Project Settings"))
        project_layout = QVBoxLayout()
        
        # Default project path
        path_layout = QHBoxLayout()
        path_label = QLabel(self.tr("Default Project Path:"))
        self.path_edit = QLineEdit()
        self.path_edit.setReadOnly(True)
        self.path_edit.setToolTip(self.tr("Default location for new projects"))
        browse_btn = QPushButton(self.tr("Browse"))
        browse_btn.setToolTip(self.tr("Select default project directory"))
        browse_btn.clicked.connect(self._browse_path)
        
        path_layout.addWidget(path_label)
        path_layout.addWidget(self.path_edit)
        path_layout.addWidget(browse_btn)
        project_layout.addLayout(path_layout)
        
        project_group.setLayout(project_layout)
        layout.addWidget(project_group)
        
        # Export Settings
        export_group = QGroupBox(self.tr("Export Settings"))
        export_layout = QVBoxLayout()
        
        # File formats
        formats_label = QLabel(self.tr("Export Formats:"))
        formats_label.setFont(QFont(self.font().family(), weight=QFont.Bold))
        export_layout.addWidget(formats_label)
        
        self.json_check = QCheckBox(self.tr("JSON"))
        self.json_check.setToolTip(self.tr("Export results in JSON format"))
        
        self.csv_check = QCheckBox(self.tr("CSV"))
        self.csv_check.setToolTip(self.tr("Export results in CSV format"))
        
        self.excel_check = QCheckBox(self.tr("Excel"))
        self.excel_check.setToolTip(self.tr("Export results in Excel format"))
        
        export_layout.addWidget(self.json_check)
        export_layout.addWidget(self.csv_check)
        export_layout.addWidget(self.excel_check)
        
        export_group.setLayout(export_layout)
        layout.addWidget(export_group)
        
        # Analysis Settings
        analysis_group = QGroupBox(self.tr("Analysis Settings"))
        analysis_layout = QVBoxLayout()
        
        # Iteration count
        iterations_layout = QHBoxLayout()
        iterations_label = QLabel(self.tr("Default Iterations:"))
        self.iterations_spin = QSpinBox()
        self.iterations_spin.setRange(10, 10000)
        self.iterations_spin.setSingleStep(10)
        self.iterations_spin.setToolTip(self.tr("Number of iterations for analysis"))
        
        iterations_layout.addWidget(iterations_label)
        iterations_layout.addWidget(self.iterations_spin)
        iterations_layout.addStretch()
        
        analysis_layout.addLayout(iterations_layout)
        analysis_group.setLayout(analysis_layout)
        layout.addWidget(analysis_group)
        
        # Interface Settings
        interface_group = QGroupBox(self.tr("Interface Settings"))
        interface_layout = QVBoxLayout()
        
        # Language selection
        language_layout = QHBoxLayout()
        language_label = QLabel(self.tr("Language:"))
        self.language_combo = QComboBox()
        self.language_combo.addItems(self.i18n.get_available_locales())
        language_layout.addWidget(language_label)
        language_layout.addWidget(self.language_combo)
        language_layout.addStretch()
        interface_layout.addLayout(language_layout)
        
        # Window state
        self.maximize_check = QCheckBox(self.tr("Start Maximized"))
        self.maximize_check.setToolTip(self.tr("Start application in maximized state"))
        interface_layout.addWidget(self.maximize_check)
        
        interface_group.setLayout(interface_layout)
        layout.addWidget(interface_group)
        
        # Dialog buttons
        button_box = QDialogButtonBox()
        ok_button = QPushButton(self.tr("OK"))
        ok_button.setDefault(True)
        ok_button.setToolTip(self.tr("Save changes and close"))
        
        cancel_button = QPushButton(self.tr("Cancel"))
        cancel_button.setToolTip(self.tr("Discard changes and close"))
        
        button_box.addButton(ok_button, QDialogButtonBox.AcceptRole)
        button_box.addButton(cancel_button, QDialogButtonBox.RejectRole)
        
        button_box.accepted.connect(self._save_settings)
        button_box.rejected.connect(self.reject)
        
        layout.addWidget(button_box)
        
        self.setLayout(layout)
        
    def _load_settings(self):
        """Load current settings"""
        # Project path
        default_path = self.config.get(
            "default_path",
            os.path.expanduser("~/Desktop/MicroAI_Detect")
        )
        self.path_edit.setText(default_path)
        
        # Export formats
        export_formats = self.config.get("export_formats", ["json", "csv", "xlsx"])
        self.json_check.setChecked("json" in export_formats)
        self.csv_check.setChecked("csv" in export_formats)
        self.excel_check.setChecked("xlsx" in export_formats)
        
        # Analysis settings
        self.iterations_spin.setValue(
            self.config.get("analysis_iterations", 100)
        )
        
        # Interface settings
        self.maximize_check.setChecked(
            self.config.get("window.maximized", False)
        )
        
        # Language setting
        current_locale = self.config.get("language", "en")
        index = self.language_combo.findText(current_locale)
        if index != -1:
            self.language_combo.setCurrentIndex(index)
        
    def _save_settings(self):
        """Save settings and close dialog"""
        # Project path
        self.config.set("default_path", self.path_edit.text())
        
        # Export formats
        formats = []
        if self.json_check.isChecked():
            formats.append("json")
        if self.csv_check.isChecked():
            formats.append("csv")
        if self.excel_check.isChecked():
            formats.append("xlsx")
        self.config.set("export_formats", formats)
        
        # Analysis settings
        self.config.set("analysis_iterations", self.iterations_spin.value())
        
        # Interface settings
        self.config.set("window.maximized", self.maximize_check.isChecked())
        
        # Language setting
        selected_language = self.language_combo.currentText()
        self.config.set("language", selected_language)
        self.config.save()
        self.language_changed.emit(selected_language)  # 发射信号
        self.accept()
        
    def _browse_path(self):
        """Open directory browser"""
        current_path = self.path_edit.text()
        new_path = QFileDialog.getExistingDirectory(
            self,
            self.tr("Select Default Project Directory"),
            current_path
        )
        
        if new_path:
            self.path_edit.setText(new_path)

    def retranslateUi(self):
        """Retranslate UI elements."""
        self.setWindowTitle(self.tr("Settings"))
        # Retranslate other elements as needed
