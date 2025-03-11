"""
Resource Check Utility
"""
import os
import json
import logging
import shutil
from typing import Dict, List, Any

from .utils.path_manager import (get_config_dir, get_resources_dir,
                               get_i18n_dir, create_app_directories)

logger = logging.getLogger(__name__)

def check_config() -> bool:
    """Check and create default configuration"""
    try:
        config_dir = get_config_dir()
        config_file = os.path.join(config_dir, "config.json")
        
        # Create config directory if not exists
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)
            logger.info(f"Created config directory: {config_dir}")
            
        # Create default config if not exists
        if not os.path.exists(config_file):
            from .config import DEFAULTS
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(DEFAULTS, f, indent=4)
            logger.info(f"Created default config: {config_file}")
            
        return True
        
    except Exception as e:
        logger.error(f"Error checking config: {e}")
        return False

def check_translations() -> bool:
    """Check translation files"""
    try:
        i18n_dir = get_i18n_dir()
        if not os.path.exists(i18n_dir):
            os.makedirs(i18n_dir)
            logger.info(f"Created i18n directory: {i18n_dir}")
            
        # Check required locales
        required_locales = ["en", "zh_CN", "zh_TW"]
        for locale in required_locales:
            json_file = os.path.join(i18n_dir, f"{locale}.json")
            if not os.path.exists(json_file):
                # Copy default translation file
                default_file = os.path.join(
                    get_resources_dir(),
                    "defaults",
                    "translations",
                    f"{locale}.json"
                )
                if os.path.exists(default_file):
                    shutil.copy2(default_file, json_file)
                    logger.info(f"Copied default translation: {locale}")
                else:
                    logger.warning(f"Missing default translation: {locale}")
                    
        # Create QM directory
        qm_dir = os.path.join(i18n_dir, "qm")
        if not os.path.exists(qm_dir):
            os.makedirs(qm_dir)
            
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
            
        # Check required themes
        required_themes = ["siui_dark", "py_onedark"]
        for theme in required_themes:
            qss_file = os.path.join(themes_dir, f"{theme}.qss")
            if not os.path.exists(qss_file):
                # Copy default theme file
                default_file = os.path.join(
                    get_resources_dir(),
                    "defaults",
                    "themes",
                    f"{theme}.qss"
                )
                if os.path.exists(default_file):
                    shutil.copy2(default_file, qss_file)
                    logger.info(f"Copied default theme: {theme}")
                else:
                    logger.warning(f"Missing default theme: {theme}")
                    
        return True
        
    except Exception as e:
        logger.error(f"Error checking themes: {e}")
        return False

def check_directories() -> bool:
    """Check required directories"""
    try:
        # Create app directories
        if not create_app_directories():
            return False
            
        # Check resource directories
        resource_dirs = [
            ["resources"],
            ["resources", "i18n"],
            ["resources", "themes"],
            ["resources", "models"],
            ["resources", "icons"]
        ]
        
        for parts in resource_dirs:
            dir_path = os.path.join(get_resources_dir(), *parts)
            if not os.path.exists(dir_path):
                os.makedirs(dir_path)
                logger.info(f"Created directory: {dir_path}")
                
        return True
        
    except Exception as e:
        logger.error(f"Error checking directories: {e}")
        return False

def check_all() -> bool:
    """Check all resources"""
    try:
        checkers = [
            ("Directories", check_directories),
            ("Configuration", check_config),
            ("Translations", check_translations),
            ("Themes", check_themes)
        ]
        
        success = True
        for name, checker in checkers:
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
