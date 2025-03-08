import sys
import logging
from pathlib import Path
from datetime import datetime

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import Qt, QCoreApplication, QTranslator
from PySide6.QtGui import QFont, QGuiApplication
from app.gui.main_window import MainWindow
from app.gui.settings_dialog import SettingsDialog
from app.gui.about_dialog import AboutDialog

from app.utils.config import init_config, ConfigManager
from app.utils.path_manager import create_app_dirs
from app.utils.i18n import init_translations, I18NManager

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

def show_error_dialog(title, message):
    """显示错误对话框"""
    msg_box = QMessageBox()
    msg_box.setIcon(QMessageBox.Critical)
    msg_box.setWindowTitle(title)
    msg_box.setText(message)
    msg_box.setStandardButtons(QMessageBox.Ok)
    msg_box.exec()

def main():
    """Application entry point"""
    try:
        # Initialize logging
        logger.info("Logging initialized")
        
        # Create Qt application first
        app = QApplication(sys.argv)
        
        # Initialize High DPI support (Qt6 specific)
        if hasattr(Qt.ApplicationAttribute, 'HighDpiScaleFactorRoundingPolicy'):
            app.setAttribute(Qt.ApplicationAttribute.HighDpiScaleFactorRoundingPolicy, 
                           Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
        
        # Set application properties
        app.setApplicationName("MicroAI-Colony")
        app.setApplicationVersion("1.0.0")
        app.setOrganizationName("MicroAI Team")
        app.setOrganizationDomain("github.com/BOHUYESHAN-APB")
        
        logger.info(f"Application started: {app.applicationName()} {app.applicationVersion()}")
        logger.info(f"Platform: {sys.platform}, Python: {sys.version}")
        
        # Set default font based on platform
        if sys.platform == "win32":
            preferred_fonts = ["Microsoft YaHei UI", "Microsoft YaHei", "Segoe UI"]
        elif sys.platform == "darwin":
            preferred_fonts = ["PingFang SC", "Helvetica Neue", "Helvetica"]
        else:  # Linux and others
            preferred_fonts = ["Noto Sans CJK SC", "DejaVu Sans", "Arial"]
        
        # Find first available font
        selected_font = None
        for font_name in preferred_fonts:
            if QFont(font_name).family() == font_name:
                selected_font = font_name
                break
        
        if selected_font:
            # 设置默认字体
            app_font = QFont(selected_font)
            if sys.platform == "win32":
                app_font.setPointSize(9)
            elif sys.platform == "darwin":
                app_font.setPointSize(13)
            else:
                app_font.setPointSize(10)
            
            app.setFont(app_font)
            logger.info(f"Using font: {selected_font}")
        else:
            logger.warning("No preferred font found, using system default")
        
        # Create necessary directories and initialize components
        try:
            # Create necessary directories
            create_app_dirs()
            logger.info("Application directories created")
            
            # Initialize configuration
            init_config()
            config = ConfigManager()
            logger.info("Configuration initialized")

            # Initialize translations
            i18n = init_translations()
            locale_code = i18n.get_current_locale()
            
            translator = QTranslator()
            if translator.load(str(Path(__file__).parent / "resources" / "i18n" / f"{locale_code}.qm")):
                app.installTranslator(translator)
                logger.info(f"Installed Qt translation for {locale_code}")
            else:
                logger.error(f"Failed to load translation for {locale_code}")
            logger.info(f"Translations initialized. Current locale: {locale_code}")

        except Exception as e:
            error_msg = f"Failed to initialize application components: {str(e)}"
            logger.error(error_msg)
            show_error_dialog("Initialization Error", error_msg)
            return 1

        # Apply theme
        theme_file = Path(__file__).parent / 'resources' / 'themes' / 'py_onedark.qss'
        if theme_file.exists():
            try:
                with open(theme_file, "r", encoding='utf-8') as f:
                    app.setStyleSheet(f.read())
                logger.info("Theme applied successfully")
            except Exception as e:
                logger.error(f"Failed to load theme: {e}")
                # Theme loading failure is not fatal
        
        # Create and show main window
        try:
            logger.info("Creating main window...")
            window = MainWindow()
            
            # Initialize window state
            window_config = config.get("window", {})
            if window_config.get("maximized", False):
                window.setWindowState(Qt.WindowState.WindowMaximized)
            else:
                window.resize(
                    window_config.get("width", 1200),
                    window_config.get("height", 800)
                )
            
            # Connect settings dialog's language change signal
            def on_language_changed(locale):
                logger.info(f"Language change requested: {locale}")
                
                # Re-initialize translator with new locale
                new_translator = QTranslator()
                qm_path = str(Path(__file__).parent / "resources" / "i18n" / f"{locale}.qm")
                logger.info(f"Attempting to load QM file from: {qm_path}")
                if new_translator.load(qm_path):
                    QCoreApplication.installTranslator(new_translator)
                    logger.info(f"Installed Qt translation for {locale}")
                    
                    # Retranslate UI in all windows/dialogs
                    window.retranslateUi()
                    if hasattr(window, 'settings_dialog'):
                        window.settings_dialog.retranslateUi()
                    if hasattr(window, 'about_dialog'):
                        window.about_dialog.retranslateUi()
                else:
                    logger.error(f"Failed to load translation for {locale}")
            
            window.settings_dialog = SettingsDialog(window)  # Create instance
            window.settings_dialog.language_changed.connect(on_language_changed)
            
            # Show window and center it on screen
            window.show()
            if QGuiApplication.primaryScreen() is not None:  # Check if primaryScreen() exists
                screen = QGuiApplication.primaryScreen().geometry()
                window.move(
                    (screen.width() - window.width()) // 2,
                    (screen.height() - window.height()) // 2
                )
            
            logger.info("Main window initialized and shown")
            
            return app.exec()
        except Exception as e:
            error_msg = f"Failed to initialize main window: {str(e)}"
            logger.error(error_msg, exc_info=True)
            show_error_dialog("Startup Error", error_msg)
            return 1
            
    except Exception as e:
        error_msg = f"Application failed to start: {str(e)}"
        logger.error(error_msg, exc_info=True)
        # Show error dialog if QApplication exists
        if 'app' in locals():
            show_error_dialog("Fatal Error", error_msg)
        return 1

if __name__ == '__main__':
    sys.exit(main())
