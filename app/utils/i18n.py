"""
Internationalization Utility
"""
import os
import json
import logging
from typing import Optional, List, Dict

from PyQt6.QtWidgets import QApplication

logger = logging.getLogger(__name__)

SUPPORTED_LOCALES = ["en", "zh_CN", "zh_TW"]
_current_locale: str = "en"
_translations: Dict[str, str] = {}

def get_locales() -> List[str]:
    """Get list of supported locales"""
    return SUPPORTED_LOCALES

def tr(key: str, **kwargs) -> str:
    """Get translation for key with formatting arguments"""
    # Get translation from loaded translations
    translated = _translations.get(key, key)
    
    # Return directly if no formatting needed
    if not kwargs:
        return translated
        
    # Format with provided arguments
    try:
        return translated.format(**kwargs)
    except KeyError as e:
        logger.error(f"Missing formatting argument {e} for translation key {key}")
        return translated
    except Exception as e:
        logger.error(f"Error formatting translation key {key}: {e}")
        return translated

def get_locale() -> str:
    """Get current locale"""
    return _current_locale

def set_locale(locale: str) -> bool:
    """Set current locale and load translations"""
    global _current_locale, _translations
    
    try:
        if locale not in SUPPORTED_LOCALES:
            logger.error(f"Unsupported locale: {locale}")
            return False
            
        # Load translations from JSON file
        translations_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                               "resources", "translations")
        json_path = os.path.join(translations_dir, f"{locale}.json")
        
        if not os.path.exists(json_path):
            logger.error(f"Translation file not found: {json_path}")
            return False
            
        with open(json_path, 'r', encoding='utf-8') as f:
            _translations = json.load(f)
            
        _current_locale = locale
        logger.info(f"Loaded translations for {locale} from {json_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error setting locale to {locale}: {e}")
        return False

def initialize() -> bool:
    """Initialize internationalization"""
    try:
        # Set default locale
        from ..config import ConfigManager
        config = ConfigManager.get_instance()
        
        default_locale = config.get("locale", "en")
        if not set_locale(default_locale):
            logger.warning(f"Failed to set default locale: {default_locale}")
            if not set_locale("en"):  # Fallback to English
                logger.error("Failed to set fallback locale (en)")
                return False
                
        logger.info("Internationalization initialized")
        return True
        
    except Exception as e:
        logger.error(f"Error initializing i18n: {e}")
        return False
