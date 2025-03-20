"""
Toolbar related constants and utilities
工具栏相关常量和实用工具
"""
from PyQt6.QtCore import QSize

# Standard toolbar icon sizes
SMALL_ICON_SIZE = QSize(16, 16)
MEDIUM_ICON_SIZE = QSize(24, 24)
LARGE_ICON_SIZE = QSize(32, 32)

# Toolbar styles
TOOLBAR_STYLE = """
    QToolBar {
        background: #2d2d2d;
        border: none;
        spacing: 3px;
        padding: 2px;
    }
    QToolButton {
        background: transparent;
        border: none;
        padding: 3px;
        border-radius: 2px;
    }
    QToolButton:hover {
        background: #404040;
    }
    QToolButton:pressed {
        background: #505050;
    }
"""
