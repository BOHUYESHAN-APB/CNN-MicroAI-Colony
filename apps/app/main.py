"""
Application entry point
应用程序入口点
"""
import sys
import os
sys.path.insert(0, os.getcwd())

import logging
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from apps.app.utils.i18n import init_translations
from apps.app.gui.main_window import MainWindow

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)

def main():
    """Application main entry"""
    try:
        # Initialize translations
        init_translations()
        
        # Create application
        app = QApplication(sys.argv)
        app.setApplicationName("微生物菌落计数分析")
        
        # Create and show main window
        window = MainWindow()
        window.show()
        
        logger.info("Application initialized successfully")
        
        # Start event loop
        return app.exec()
        
    except Exception as e:
        logger.error(f"Application failed to start: {str(e)}")
        logger.debug("Error details:", exc_info=True)
        return 1
    finally:
        logger.info("Application cleanup completed")

if __name__ == "__main__":
    logger.debug("Logging system initialized")
    sys.exit(main())
