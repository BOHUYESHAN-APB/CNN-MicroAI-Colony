import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
from PySide6.QtCore import QTranslator, QCoreApplication

logger = logging.getLogger(__name__)

class I18NManager:
    _instance = None
    _initialized = False
    _current_locale = None
    _available_locales = []
    _strings: Dict[str, Dict[str, str]] = {}
    _translator = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not I18NManager._initialized:
            self._load_translations()
            I18NManager._initialized = True
            
    def _load_translations(self):
        """Load all available translations"""
        logger.info("Loading translations")
        i18n_dir = self._get_i18n_dir()
        
        # Load each translation file
        for file_path in i18n_dir.glob("*.json"):
            locale = file_path.stem
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    strings = json.load(f)
                I18NManager._strings[locale] = strings
                I18NManager._available_locales.append(locale)
                logger.info(f"Loaded {len(strings)} translations for {locale}")
            except Exception as e:
                logger.error(f"Failed to load translations for {locale}: {e}")
                
        logger.info(f"Total loaded translations: {sum(len(s) for s in I18NManager._strings.values())}")
        logger.info(f"Available locales: {I18NManager._available_locales}")
        
        # Set initial locale
        if not I18NManager._current_locale:
            self.set_locale(self._get_default_locale())
            
    def _get_i18n_dir(self) -> Path:
        """Get translations directory path"""
        return Path(__file__).parent.parent / "resources" / "i18n"
        
    def _get_default_locale(self) -> str:
        """Get default locale based on system settings"""
        system_locale = QCoreApplication.instance().property("system_locale")
        if system_locale in I18NManager._available_locales:
            return system_locale
        return "en"  # Default to English
        
    def get_string(self, key: str, locale: Optional[str] = None) -> str:
        """Get translated string for key"""
        if not locale:
            locale = I18NManager._current_locale
            
        try:
            return I18NManager._strings[locale][key]
        except KeyError:
            logger.warning(f"Missing translation for key '{key}' in locale '{locale}'")
            # Fallback to English
            try:
                return I18NManager._strings["en"][key]
            except KeyError:
                logger.error(f"No translation found for key '{key}'")
                return key
                
    def set_locale(self, locale: str) -> bool:
        """Set current locale"""
        if locale not in I18NManager._available_locales:
            logger.error(f"Locale '{locale}' not available")
            return False
            
        I18NManager._current_locale = locale
        logger.info(f"Set locale to {locale}")
        
        # Update Qt translator
        if I18NManager._translator:
            QCoreApplication.removeTranslator(I18NManager._translator)
            
        I18NManager._translator = QTranslator()
        qm_file = self._get_i18n_dir() / f"{locale}.qm"
        
        if qm_file.exists() and I18NManager._translator.load(str(qm_file)):
            QCoreApplication.installTranslator(I18NManager._translator)
            
        self._log_status()
        return True
        
    def get_available_locales(self) -> List[str]:
        """Get list of available locales"""
        return I18NManager._available_locales.copy()
        
    def get_current_locale(self) -> str:
        """Get current locale"""
        return I18NManager._current_locale
        
    def _log_status(self):
        """Log current i18n status"""
        logger.info("=== Translation Status ===")
        logger.info(f"Current locale: {I18NManager._current_locale}")
        logger.info(f"Available locales: {I18NManager._available_locales}")
        logger.info(f"Initialized: {I18NManager._initialized}")
        logger.info(f"Loaded strings for current locale: {len(I18NManager._strings.get(I18NManager._current_locale, {}))}")
        logger.info("=====================")

def init_translations():
    """Initialize translations system"""
    i18n = I18NManager()
    logger.info("Translations initialized successfully")
    return i18n
