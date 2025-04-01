"""
Main application entry point
应用程序入口点
"""
import os
import sys
import logging
from logging.handlers import RotatingFileHandler  # 导入 RotatingFileHandler

from PyQt6.QtWidgets import QApplication
from apps.app.utils.gpu_utils import check_gpu_available, get_device
from apps.app.utils.config_manager import ConfigManager

# Setup logging
log_formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

# Console logger (输出到控制台)
console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)

# File logger (输出到文件, 每天生成新的日志文件, 保留最近7天的日志)
file_handler = RotatingFileHandler(
    'logs/app.log',  # 日志文件路径
    maxBytes=10*1024*1024,  # 每个日志文件最大 10MB
    backupCount=5  # 最多保留 5 个备份文件
)
file_handler.setFormatter(log_formatter)

try:
    logging.basicConfig(
        level=logging.DEBUG,  # 设置为 DEBUG 级别，记录更详细的日志
        handlers=[console_handler, file_handler] # 同时使用控制台和文件日志处理器
    )
    logger = logging.getLogger(__name__)
    logger.debug("Logging system initialized")  # 添加启动日志消息
except Exception as e:
    print(f"Error initializing logging: {e}") # 打印到控制台，即使文件日志失败也能看到
    logging.basicConfig() # 尝试基本配置，至少保证控制台日志可用
    logger = logging.getLogger(__name__)

# Add project root to path
project_root = 'd:/-Users-/Documents/GitHub/CNN-MicroAI-Colony' # Explicitly set project root
sys.path.insert(0, project_root)

print(f"Project root path (explicitly set): {project_root}")
print(f"Python sys.path: {sys.path}")

# Use absolute imports
from apps.app.gui.main_window import MainWindow
from apps.app.utils.i18n import I18nManager

def main():
    """Application main entry point"""
    try:
        # Check GPU availability
        device = get_device()
        logger.info(f"Using device: {device}")
        
        # Create application
        app = QApplication(sys.argv)
        
        # Initialize i18n
        i18n = I18nManager()
        if not i18n.initialize():
            logger.error("Failed to initialize i18n")
            return 1
            
        # Initialize config
        config = ConfigManager()
        
        # Create main window with config
        window = MainWindow(config)
        window.show()
        
        # Start event loop
        logger.info("Application initialized successfully")
        return app.exec()
        
    except Exception as e:
        logger.error(f"Application failed to start: {e}")
        return 1
    
    finally:
        # Cleanup
        logger.info("Application cleanup completed")

if __name__ == "__main__":
    sys.exit(main())
