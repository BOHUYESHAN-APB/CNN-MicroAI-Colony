"""
Application Entry Point
应用程序入口
"""
import os
import sys
import logging
import signal
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

# Add parent directory to Python path to allow importing app module
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from app.gui.main_window import MainWindow
from app.utils.config import ConfigManager
from app import initialize_app, cleanup, APP_NAME, APP_ORGANIZATION, APP_DOMAIN

logger = logging.getLogger(__name__)

def signal_handler(signum, frame):
    """Handle system signals"""
    logger.info(f"Received signal {signum}")
    cleanup()
    sys.exit(0)

def setup_environment() -> bool:
    """Setup application environment"""
    try:
        # Handle high DPI displays
        if hasattr(Qt, 'AA_EnableHighDpiScaling'):
            QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
            QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
            
        # Set Qt platform plugin path if packaged
        if getattr(sys, 'frozen', False):
            os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = os.path.join(
                os.path.dirname(sys.executable), 'platforms'
            )
            
        return True
    except Exception as e:
        logger.error(f"Error setting up environment: {e}")
        return False

def main():
    """Application entry point"""
    try:
        # Setup environment
        if not setup_environment():
            logger.error("Environment setup failed")
            return 1
            
        # Register signal handlers
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Create Qt application
        qt_app = QApplication(sys.argv)
                
        # Initialize application components
        if not initialize_app():
            logger.error("Application initialization failed")
            return 1

        # Set application attributes
        qt_app.setApplicationName(APP_NAME)
        qt_app.setOrganizationName(APP_ORGANIZATION)
        qt_app.setOrganizationDomain(APP_DOMAIN)

        # Load configuration
        config = ConfigManager()

        # Create main window
        window = MainWindow(config)
            
        if config.get("interface.start_maximized", False):
            window.showMaximized()
        else:
            window.show()
            
        # Execute application
        result = qt_app.exec()
        
        # Cleanup
        cleanup()
        
        return result
        
    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        cleanup()
        return 1

if __name__ == "__main__":
    sys.exit(main())
