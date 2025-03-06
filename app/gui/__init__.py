"""
GUI components using PySide6 with PyOneDark theme
"""
import os
from pathlib import Path

THEMES_DIR = Path(__file__).parent.parent / 'resources' / 'themes'

def load_theme(theme_name: str = 'py_onedark') -> str:
    """Load theme stylesheet from QSS file"""
    theme_file = THEMES_DIR / f'{theme_name}.qss'
    if not theme_file.exists():
        return ''
        
    with open(theme_file, 'r', encoding='utf-8') as f:
        return f.read()

def apply_theme(widget, theme_name: str = 'py_onedark'):
    """Apply theme to widget and all its children"""
    stylesheet = load_theme(theme_name)
    if stylesheet:
        widget.setStyleSheet(stylesheet)