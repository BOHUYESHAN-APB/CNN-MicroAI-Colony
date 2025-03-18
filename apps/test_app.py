"""
Test Application
测试应用程序
"""
import os
import sys
from PyQt6.QtWidgets import QApplication

# Add parent directory to Python path to allow importing app module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.gui.main_window import MainWindow
from app.utils.config import ConfigManager

def main():
    """Test application entry point"""
    app = QApplication(sys.argv)
    
    # Load configuration
    config = ConfigManager()
    
    # Create and show main window
    window = MainWindow(config)
    window.show()
    
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())
