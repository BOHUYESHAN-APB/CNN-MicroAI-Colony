import logging
from PySide6.QtWidgets import QMainWindow
from app_pyside6.utils.i18n import i18n
from app_pyside6.utils.path_manager import PathManager
from app_pyside6.config.config_manager import ConfigManager

logger = logging.getLogger(__name__)

class BaseWindow(QMainWindow):
    """Base window class with common functionality"""
    
    def __init__(self, config: ConfigManager):
        super().__init__()
        self.config = config
        self.path_manager = PathManager(config)
        self.init_window()
        
    def init_window(self):
        """Initialize window properties"""
        self.setWindowTitle(i18n.get('app.name'))
        self.resize(
            self.config.get('ui.window.width', 1280),
            self.config.get('ui.window.height', 800)
        )
        if self.config.get('ui.window.maximized', False):
            self.showMaximized()

    def change_language(self, lang: str):
        """Change interface language"""
        try:
            i18n.change_language(lang)
            self.config.set('app.language', lang)
            self.config.save()
            self.retranslate_ui()
        except Exception as e:
            logger.error(f"Failed to change language: {e}")
            raise
            
    def retranslate_ui(self):
        """Update interface text"""
        # Subclasses should override this method
        pass
