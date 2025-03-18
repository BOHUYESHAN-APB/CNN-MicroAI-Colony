"""
Progress Dialog
进度对话框
"""
from PyQt6.QtWidgets import (QDialog, QProgressBar, QLabel, QPushButton,
                            QVBoxLayout, QHBoxLayout)
from PyQt6.QtCore import Qt, pyqtSignal

class ProgressDialog(QDialog):
    """Processing progress dialog"""
    
    cancelled = pyqtSignal()
    
    def __init__(self, parent=None, title="Processing", message="Please wait..."):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setWindowFlags(Qt.WindowType.WindowTitleHint | Qt.WindowType.CustomizeWindowHint)
        
        # Create widgets
        self.message_label = QLabel(message)
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(100)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.on_cancel)
        self.detail_label = QLabel()
        
        # Layout
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.message_label)
        main_layout.addWidget(self.progress_bar)
        main_layout.addWidget(self.detail_label)
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_button)
        main_layout.addLayout(button_layout)
        
        self.setLayout(main_layout)
        self.setStyleSheet("""
            QDialog {
                background-color: #2b2b2b;
            }
            QLabel {
                color: #e0e0e0;
                font-size: 13px;
            }
            QPushButton {
                background-color: #424242;
                color: #e0e0e0;
                border: 1px solid #1e1e1e;
                border-radius: 4px;
                padding: 6px 16px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #4a4a4a;
            }
            QPushButton:pressed {
                background-color: #353535;
            }
            QProgressBar {
                border: 1px solid #1e1e1e;
                border-radius: 4px;
                background-color: #424242;
                color: #e0e0e0;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #0d47a1;
                border-radius: 3px;
            }
        """)
        
        # Initialize state
        self.cancelled_flag = False
        
    def set_progress(self, value: int, detail: str = None):
        """Update progress bar and detail message"""
        self.progress_bar.setValue(value)
        if detail:
            self.detail_label.setText(detail)
            
    def was_cancelled(self) -> bool:
        """Check if operation was cancelled"""
        return self.cancelled_flag
        
    def on_cancel(self):
        """Handle cancel button click"""
        self.cancelled_flag = True
        self.cancelled.emit()
        self.cancel_button.setEnabled(False)
        self.message_label.setText("Cancelling...")
