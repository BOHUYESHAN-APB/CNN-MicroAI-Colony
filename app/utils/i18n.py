import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from functools import lru_cache

logger = logging.getLogger(__name__)

class I18nManager:
    """Internationalization manager"""
    
    def __init__(self):
        self.current_lang = "en"
        self.translations: Dict[str, Dict] = {}
        self._load_translations()
        
    def _load_translations(self):
        """Load all translation files"""
        i18n_dir = Path(__file__).parent.parent / "resources" / "i18n"
        
        try:
            for file in i18n_dir.glob("*.json"):
                lang = file.stem
                with open(file, 'r', encoding='utf-8') as f:
                    self.translations[lang] = json.load(f)
            logger.info(f"Loaded translations: {list(self.translations.keys())}")
        except Exception as e:
            logger.error(f"Failed to load translations: {e}")
            # Ensure at least English is available
            self.translations["en"] = {}
            
    @lru_cache(maxsize=1024)
    def get(self, key: str, lang: Optional[str] = None, **kwargs) -> str:
        """
        Get translated text
        
        Args:
            key: Translation key (dot notation supported)
            lang: Optional language code
            **kwargs: Format arguments
            
        Returns:
            Translated text
        """
        try:
            # Use specified language or current language
            lang = lang or self.current_lang
            
            # Try to get translation
            current = self.translations[lang]
            for k in key.split('.'):
                current = current[k]
                
            # Format if needed
            if kwargs and isinstance(current, str):
                return current.format(**kwargs)
            return current
            
        except KeyError:
            # Fallback to English
            if lang != "en":
                return self.get(key, "en", **kwargs)
            # Return key if no translation found
            return key
            
    def set_language(self, lang: str) -> bool:
        """
        Set current language
        
        Args:
            lang: Language code
            
        Returns:
            True if successful
        """
        if lang in self.translations:
            self.current_lang = lang
            # Clear cache when language changes
            self.get.cache_clear()
            logger.info(f"Language changed to {lang}")
            return True
        return False
        
    def get_languages(self) -> list:
        """Get list of available languages"""
        return list(self.translations.keys())
        
    def format(self, text: str, **kwargs) -> str:
        """Format text with arguments"""
        try:
            return text.format(**kwargs)
        except Exception as e:
            logger.error(f"Failed to format text: {e}")
            return text

# Create global instance
i18n = I18nManager()

# Export public interface
__all__ = ['i18n']
