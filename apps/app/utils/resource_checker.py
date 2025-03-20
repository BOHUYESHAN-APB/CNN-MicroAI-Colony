"""
Resource Check Utility
资源检查工具
"""
import os
import json
import logging
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

def get_app_dir() -> str:
    """Get application directory"""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def get_resources_dir() -> str:
    """Get resources directory"""
    return os.path.join(get_app_dir(), "resources")

def check_directories() -> bool:
    """Check and create required directories"""
    try:
        # Core directories
        directories = [
            ["resources"],
            ["resources", "i18n"],
            ["resources", "themes"],
            ["resources", "models"],
            ["logs"]
        ]
        
        for parts in directories:
            dir_path = os.path.join(get_app_dir(), *parts)
            if not os.path.exists(dir_path):
                os.makedirs(dir_path)
                logger.info(f"Created directory: {dir_path}")
                
        return True
        
    except Exception as e:
        logger.error(f"Error checking directories: {e}")
        return False

def check_config() -> bool:
    """Check configuration files"""
    try:
        config_file = os.path.join(get_resources_dir(), "config.json")
        
        # Create default config if not exists
        if not os.path.exists(config_file):
            from .config import ConfigManager
            config = ConfigManager()  # This will create default config
            logger.info(f"Created default config: {config_file}")
            
        return True
        
    except Exception as e:
        logger.error(f"Error checking config: {e}")
        return False

def check_translations() -> bool:
    """Check translation files"""
    try:
        i18n_dir = os.path.join(get_resources_dir(), "i18n")
        logger.debug(f"Checking i18n directory: {i18n_dir}")
        
        if not os.path.exists(i18n_dir):
            os.makedirs(i18n_dir)
            logger.info(f"Created i18n directory: {i18n_dir}")
        
        # Check required locales
        required_translations = {
            "en": {
                "app.name": "Colony Analyzer",
                "menu.file": "File",
                "menu.file.new": "New Project",
                "menu.file.open": "Open Project",
                "menu.file.save": "Save",
                "menu.file.quit": "Quit",
                "menu.edit": "Edit",
                "menu.view": "View",
                "menu.help": "Help",
                "menu.help.about": "About",
                "status.ready": "Ready",
                "dialog.error": "Error",
                "dialog.warning": "Warning",
                "dialog.info": "Information"
            },
            "zh_CN": {
                "app.name": "菌落分析器",
                "menu.file": "文件",
                "menu.file.new": "新建项目",
                "menu.file.open": "打开项目",
                "menu.file.save": "保存",
                "menu.file.quit": "退出",
                "menu.edit": "编辑",
                "menu.view": "视图",
                "menu.help": "帮助",
                "menu.help.about": "关于",
                "status.ready": "就绪",
                "dialog.error": "错误",
                "dialog.warning": "警告",
                "dialog.info": "信息"
            }
        }

        for locale, messages in required_translations.items():
            file_path = os.path.join(i18n_dir, f"{locale}.json")
            if not os.path.exists(file_path):
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(messages, f, ensure_ascii=False, indent=4)
                logger.info(f"Created translation file: {file_path}")
                
        return True
        
    except Exception as e:
        logger.error(f"Error checking translations: {e}")
        return False

def check_themes() -> bool:
    """Check theme files"""
    try:
        themes_dir = os.path.join(get_resources_dir(), "themes")
        if not os.path.exists(themes_dir):
            os.makedirs(themes_dir)
            logger.info(f"Created themes directory: {themes_dir}")
            
        # Default light theme
        default_theme = os.path.join(themes_dir, "default.qss")
        if not os.path.exists(default_theme):
            with open(default_theme, 'w', encoding='utf-8') as f:
                f.write("""
/* Default Light Theme */
QMainWindow {
    background-color: #f0f0f0;
}

QStatusBar {
    background-color: #e0e0e0;
}

QMenuBar {
    background-color: #f0f0f0;
}

QMenu {
    background-color: #ffffff;
}

QToolBar {
    background-color: #f0f0f0;
    border: none;
}
""")
            logger.info(f"Created default theme: {default_theme}")
            
        # Dark theme
        dark_theme = os.path.join(themes_dir, "dark.qss")
        if not os.path.exists(dark_theme):
            with open(dark_theme, 'w', encoding='utf-8') as f:
                f.write("""
/* Dark Theme */
QMainWindow {
    background-color: #2b2b2b;
    color: #ffffff;
}

QStatusBar {
    background-color: #1e1e1e;
    color: #ffffff;
}

QMenuBar {
    background-color: #2b2b2b;
    color: #ffffff;
}

QMenu {
    background-color: #2b2b2b;
    color: #ffffff;
}

QToolBar {
    background-color: #2b2b2b;
    border: none;
}

QLabel {
    color: #ffffff;
}

QPushButton {
    background-color: #3c3c3c;
    color: #ffffff;
    border: 1px solid #505050;
    padding: 5px;
    border-radius: 2px;
}

QPushButton:hover {
    background-color: #505050;
}

QPushButton:pressed {
    background-color: #404040;
}
""")
            logger.info(f"Created dark theme: {dark_theme}")
                    
        return True
        
    except Exception as e:
        logger.error(f"Error checking themes: {e}")
        return False

def check_all() -> bool:
    """Check all resources"""
    try:
        checks = [
            ("Directories", check_directories),
            ("Configuration", check_config),
            ("Translations", check_translations),
            ("Themes", check_themes)
        ]
        
        success = True
        for name, checker in checks:
            logger.info(f"Checking {name}...")
            if not checker():
                logger.error(f"{name} check failed")
                success = False
                
        if success:
            logger.info("All resource checks passed")
        return success
        
    except Exception as e:
        logger.error(f"Error during resource check: {e}")
        return False
