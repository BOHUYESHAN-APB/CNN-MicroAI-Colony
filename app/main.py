import sys
import logging
from pathlib import Path
from datetime import datetime

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from app.gui.main_window import MainWindow
from app.utils.config import init_config
from app.utils.path_manager import create_app_dirs
from app.utils.i18n import init_translations

# Setup logging
LOG_DIR = Path(__file__).parent / 'logs'
LOG_DIR.mkdir(exist_ok=True)
log_file = LOG_DIR / f'app_{datetime.now().strftime("%Y%m%d")}.log'

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def main():
    """Application entry point"""
    try:
        # Initialize logging
        logger.info("Logging initialized")
        
        # Create necessary directories
        create_app_dirs()
        logger.info("Application directories created")
        
        # Initialize configuration
        init_config()
        logger.info("Configuration initialized")
        
        # Create Qt application
        app = QApplication(sys.argv)
        app.setApplicationName("Colony Detection")
        
        # Initialize translations
        init_translations()
        
        # Set dark mode flag (temporary)
        app.setStyle("Fusion")  # Will be replaced with PyOneDark
        
        # Create and show main window
        window = MainWindow()
        window.show()
        
        return app.exec()
        
    except Exception as e:
        logger.error(f"Application failed to start: {e}", exc_info=True)
        return 1

if __name__ == '__main__':
    sys.exit(main())