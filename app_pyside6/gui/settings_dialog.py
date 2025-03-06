import logging
from pathlib import Path
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                           QPushButton, QTabWidget, QWidget, QCheckBox,
                           QComboBox, QGroupBox, QFormLayout, QSpinBox,
                           QDialogButtonBox, QFileDialog, QLineEdit,
                           QMessageBox)
from PySide6.QtCore import Qt

from app_pyside6.utils.i18n import i18n

logger = logging.getLogger(__name__)

class SettingsDialog(QDialog):
    """Settings dialog for the application"""
    
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self.setWindowTitle(i18n.get('dialogs.settings'))
        self.setup_ui()
        self.load_settings()
        
    def setup_ui(self):
        """Initialize user interface"""
        layout = QVBoxLayout(self)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Add tabs
        self.add_general_tab()
        self.add_analysis_tab()
        self.add_export_tab()
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel | QDialogButtonBox.Apply
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        button_box.button(QDialogButtonBox.Apply).clicked.connect(self.apply_settings)
        layout.addWidget(button_box)
        
        self.resize(500, 400)
        
    def add_general_tab(self):
        """Add general settings tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Language selection
        lang_group = QGroupBox(i18n.get('settings.language'))
        lang_layout = QFormLayout()
        self.lang_combo = QComboBox()
        self.lang_combo.addItems(['en', 'zh'])
        lang_layout.addRow(i18n.get('settings.language_label'), self.lang_combo)
        lang_group.setLayout(lang_layout)
        layout.addWidget(lang_group)
        
        # Output directory
        dir_group = QGroupBox(i18n.get('settings.output_dir'))
        dir_layout = QHBoxLayout()
        self.dir_edit = QLineEdit()
        self.dir_edit.setReadOnly(True)
        dir_layout.addWidget(self.dir_edit)
        browse_btn = QPushButton(i18n.get('buttons.browse'))
        browse_btn.clicked.connect(self.browse_output_dir)
        dir_layout.addWidget(browse_btn)
        dir_group.setLayout(dir_layout)
        layout.addWidget(dir_group)
        
        # Project settings
        proj_group = QGroupBox(i18n.get('settings.project'))
        proj_layout = QVBoxLayout()
        self.autosave_check = QCheckBox(i18n.get('settings.autosave'))
        proj_layout.addWidget(self.autosave_check)
        proj_group.setLayout(proj_layout)
        layout.addWidget(proj_group)
        
        layout.addStretch()
        self.tab_widget.addTab(tab, i18n.get('settings.general'))
        
    def add_analysis_tab(self):
        """Add analysis settings tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Batch analysis settings
        batch_group = QGroupBox(i18n.get('settings.batch_analysis'))
        batch_layout = QFormLayout()
        
        # Runs range
        self.min_runs_spin = QSpinBox()
        self.min_runs_spin.setRange(10, 10000)
        self.max_runs_spin = QSpinBox()
        self.max_runs_spin.setRange(10, 10000)
        self.default_runs_spin = QSpinBox()
        self.default_runs_spin.setRange(10, 10000)
        
        batch_layout.addRow("Min Runs", self.min_runs_spin)
        batch_layout.addRow("Max Runs", self.max_runs_spin)
        batch_layout.addRow(i18n.get('settings.default_runs'), self.default_runs_spin)
        
        # Create plots
        self.plots_check = QCheckBox(i18n.get('settings.create_plots'))
        batch_layout.addRow("", self.plots_check)
        
        batch_group.setLayout(batch_layout)
        layout.addWidget(batch_group)
        
        layout.addStretch()
        self.tab_widget.addTab(tab, i18n.get('settings.analysis'))
        
    def add_export_tab(self):
        """Add auto-export settings tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Auto-export settings
        export_group = QGroupBox(i18n.get('settings.auto_export'))
        export_layout = QVBoxLayout()
        
        self.export_enable = QCheckBox(i18n.get('settings.enable_auto_export'))
        export_layout.addWidget(self.export_enable)
        
        # Export formats
        formats_group = QGroupBox(i18n.get('settings.export_formats'))
        formats_layout = QVBoxLayout()
        
        self.format_checks = {}
        for fmt in ['csv', 'excel', 'json']:
            check = QCheckBox(fmt.upper())
            self.format_checks[fmt] = check
            formats_layout.addWidget(check)
            
        formats_group.setLayout(formats_layout)
        export_layout.addWidget(formats_group)
        export_group.setLayout(export_layout)
        layout.addWidget(export_group)
        
        layout.addStretch()
        self.tab_widget.addTab(tab, i18n.get('settings.export'))
        
    def load_settings(self):
        """Load current settings"""
        try:
            # General settings
            self.lang_combo.setCurrentText(self.config.get('app.language', 'en'))
            self.dir_edit.setText(str(self.config.get('paths.base_dir', '')))
            self.autosave_check.setChecked(self.config.get('project.auto_save', True))
            
            # Analysis settings
            self.min_runs_spin.setValue(self.config.get('analysis.batch.min_runs', 10))
            self.max_runs_spin.setValue(self.config.get('analysis.batch.max_runs', 10000))
            self.default_runs_spin.setValue(self.config.get('analysis.batch.default_runs', 100))
            self.plots_check.setChecked(self.config.get('analysis.batch.create_plots', True))
            
            # Export settings
            self.export_enable.setChecked(self.config.get('analysis.auto_export.enabled', True))
            formats = self.config.get('analysis.auto_export.formats', ['excel'])
            for fmt, check in self.format_checks.items():
                check.setChecked(fmt in formats)
                
        except Exception as e:
            logger.error(f"Failed to load settings: {e}")
            QMessageBox.critical(
                self,
                i18n.get('errors.settings_save_failed'),
                str(e)
            )
            
    def apply_settings(self):
        """Apply current settings"""
        try:
            # General settings
            new_lang = self.lang_combo.currentText()
            if new_lang != self.config.get('app.language'):
                self.config.set('app.language', new_lang)
                i18n.set_language(new_lang)
                
            self.config.set('project.auto_save', self.autosave_check.isChecked())
            
            # Analysis settings
            self.config.set('analysis.batch.min_runs', self.min_runs_spin.value())
            self.config.set('analysis.batch.max_runs', self.max_runs_spin.value())
            self.config.set('analysis.batch.default_runs', self.default_runs_spin.value())
            self.config.set('analysis.batch.create_plots', self.plots_check.isChecked())
            
            # Export settings
            self.config.set('analysis.auto_export.enabled', self.export_enable.isChecked())
            formats = [fmt for fmt, check in self.format_checks.items() if check.isChecked()]
            self.config.set('analysis.auto_export.formats', formats)
            
            self.config.save()
            
            # Trigger UI update if language changed
            new_lang = self.lang_combo.currentText()
            if new_lang != self.config.get('app.language'):
                # Notify parent window to update UI
                if self.parent():
                    self.parent().retranslate_ui()
                # Update this dialog's UI
                self.retranslate_ui()

            # Show success message
            QMessageBox.information(
                self,
                i18n.get('settings.save_success'),
                i18n.get('info.settings_applied')
            )
            
        except Exception as e:
            logger.error(f"Failed to apply settings: {e}")
            QMessageBox.critical(
                self,
                i18n.get('errors.settings_apply_failed'),
                str(e)
            )
            
    def browse_output_dir(self):
        """Browse for output directory"""
        try:
            current_dir = self.dir_edit.text()
            dir_path = QFileDialog.getExistingDirectory(
                self,
                i18n.get('dialogs.select_output_dir'),
                current_dir
            )
            
            if dir_path:
                self.dir_edit.setText(dir_path)
                # 修改这里：直接更新字典而不是使用set方法
                self.config['paths']['base_dir'] = dir_path
                
        except Exception as e:
            logger.error(f"Failed to browse output directory: {e}")
            QMessageBox.warning(
                self,
                i18n.get('errors.error'),
                i18n.get('errors.browse_dir_failed')
            )
            
    def retranslate_ui(self):
        """Update interface language"""
        self.setWindowTitle(i18n.get('dialogs.settings'))
        
        # Update tab names
        self.tab_widget.setTabText(0, i18n.get('settings.general'))
        self.tab_widget.setTabText(1, i18n.get('settings.analysis'))
        self.tab_widget.setTabText(2, i18n.get('settings.export'))
        
        # Update general tab
        for group in self.findChildren(QGroupBox):
            if group.title() == i18n.get('settings.language', lang='en'):
                group.setTitle(i18n.get('settings.language'))
            elif group.title() == i18n.get('settings.output_dir', lang='en'):
                group.setTitle(i18n.get('settings.output_dir'))
            elif group.title() == i18n.get('settings.project', lang='en'):
                group.setTitle(i18n.get('settings.project'))
                
        # Update buttons and checkboxes
        for button in self.findChildren(QPushButton):
            if button.text() == i18n.get('buttons.browse', lang='en'):
                button.setText(i18n.get('buttons.browse'))
                
        self.autosave_check.setText(i18n.get('settings.autosave'))
        self.plots_check.setText(i18n.get('settings.create_plots'))
        self.export_enable.setText(i18n.get('settings.enable_auto_export'))
        
        # Update batch group
        batch_group = None
        for group in self.findChildren(QGroupBox):
            if group.title() == i18n.get('settings.batch_analysis', lang='en'):
                group.setTitle(i18n.get('settings.batch_analysis'))
                break
    
    def accept(self):
        """Handle dialog acceptance"""
        try:
            self.apply_settings()
            super().accept()
        except Exception as e:
            logger.error(f"Failed to save settings: {e}")
            super().reject()
