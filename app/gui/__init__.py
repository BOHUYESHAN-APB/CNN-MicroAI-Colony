"""
GUI Components
"""
import logging
from PyQt6.QtWidgets import QApplication

from ..utils.theme_manager import ThemeManager
from .main_window import MainWindow
from .about_dialog import AboutDialog
from .settings_dialog import SettingsDialog
from .project_dialog import NewProjectDialog, OpenProjectDialog
from .image_list_widget import ImageListWidget
from .result_visualizer import ResultVisualizer

logger = logging.getLogger(__name__)

def get_available_themes() -> list[str]:
    """Get list of available themes"""
    return ThemeManager.get_instance().get_available_themes()

def apply_theme(theme_name: str) -> bool:
    """Apply theme to application"""
    return ThemeManager.get_instance().apply_theme(theme_name)

def get_current_theme() -> str:
    """Get current theme name"""
    theme = ThemeManager.get_instance().get_current_theme()
    return theme if theme else "siui_dark"

def initialize_gui() -> bool:
    """Initialize GUI components"""
    try:
        # Ensure QApplication exists
        app = QApplication.instance()
        if not app:
            logger.error("QApplication not initialized")
            return False
            
        # Load default theme
        theme_manager = ThemeManager.get_instance()
        default_theme = theme_manager.get_current_theme()
        if default_theme:
            theme_manager.apply_theme(default_theme)
        else:
            logger.warning("No default theme found")
            
        return True
        
    except Exception as e:
        logger.error(f"Error initializing GUI: {e}")
        return False

# Module exports
__all__ = [
    # Main components
    'MainWindow',
    'AboutDialog', 
    'SettingsDialog',
    'NewProjectDialog',
    'OpenProjectDialog',
    'ImageListWidget',
    'ResultVisualizer',
    
    # Theme management
    'get_available_themes',
    'apply_theme',
    'get_current_theme',
    'initialize_gui'
]
