import sys
import logging
from pathlib import Path
from datetime import datetime
from PyQt5.QtWidgets import QApplication, QMessageBox

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Configure basic logging first
def setup_logging():
    """Setup logging configuration"""
    try:
        # Create logs directory
        log_dir = Path('logs')
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate log filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d')
        log_file = log_dir / f'app_{timestamp}.log'
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler(log_file, encoding='utf-8', mode='a')
            ]
        )
        
        logging.info("Logging initialized")
        return True
        
    except Exception as e:
        print(f"Failed to setup logging: {str(e)}")
        return False

def create_required_directories():
    """Create required application directories"""
    try:
        directories = [
            'logs',
            'results',
            'temp',
            'config',
            'config/defaults'
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
            
        logging.info("Application directories created")
        return True
        
    except Exception as e:
        logging.error(f"Failed to create directories: {str(e)}")
        return False

def initialize_app():
    """Initialize application components"""
    try:
        # Setup logging first
        if not setup_logging():
            raise RuntimeError("Failed to initialize logging")
            
        # Create required directories
        if not create_required_directories():
            raise RuntimeError("Failed to create required directories")
            
        # Import configuration (after logging is setup)
        from app.config import config
        logging.info("Configuration initialized")
        
        # Import main window (after config is ready)
        from app.gui.main_window import MainWindow
        
        return MainWindow, config
        
    except Exception as e:
        error_msg = f"Failed to initialize application: {str(e)}"
        logging.error(error_msg)
        raise RuntimeError(error_msg)

def main():
    """Main application entry point"""
    try:
        # Create QApplication instance
        app = QApplication(sys.argv)
        
        # Initialize application
        MainWindow, config = initialize_app()
        
        # Create and show main window
        window = MainWindow(config)
        window.show()
        
        # Start event loop
        return app.exec_()
        
    except Exception as e:
        error_msg = f"Application failed to start: {str(e)}"
        logging.error(error_msg)
        
        if 'app' in locals():
            QMessageBox.critical(
                None,
                "Startup Error",
                error_msg + "\n\nCheck the logs for more details."
            )
        return 1

if __name__ == '__main__':
    sys.exit(main())
