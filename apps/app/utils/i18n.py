"""
Internationalization utilities
国际化工具
"""
import os
import json
import logging

logger = logging.getLogger(__name__)

class I18n:
    def __init__(self):
        self.translations = {}
        self.current_language = "zh_CN"
        
    def load_translations(self):
        """Load translations from JSON files"""
        try:
            base_path = os.path.join("apps", "app", "resources", "i18n")
            file_path = os.path.join(base_path, f"{self.current_language}.json")
            
            if os.path.exists(file_path):
                with open(file_path, "r", encoding="utf-8") as f:
                    self.translations = json.load(f)
                logger.info(f"Loaded translations for {self.current_language}")
            else:
                logger.warning(f"Translation file not found: {file_path}")
                
        except Exception as e:
            logger.error(f"Failed to load translations: {e}")
            self.translations = {}
            
    def get(self, key, default=None):
        """Get translation for key"""
        try:
            # Split key by dots
            parts = key.split(".")
            value = self.translations
            
            for part in parts:
                value = value[part]
                
            return value
            
        except (KeyError, TypeError):
            return default or key
            
# Global instance
i18n = I18n()
i18n.load_translations()

def tr(key, default=None):
    """Get translation for key"""
    return i18n.get(key, default)
