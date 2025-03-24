"""
Internationalization utilities
国际化工具
"""
import os
import json
import logging

logger = logging.getLogger(__name__)

_translations = {}  # Store loaded translations

def init_translations(lang='zh_CN'):
    """Initialize translations
    
    Args:
        lang: Language code (default: zh_CN)
    """
    try:
        # Load translations file
        translation_file = os.path.join(
            os.path.dirname(__file__),
            '..',
            'resources',
            'i18n',
            f'{lang}.json'
        )
        
        if os.path.exists(translation_file):
            with open(translation_file, 'r', encoding='utf-8') as f:
                _translations.update(json.load(f))
                logger.info(f"Loaded translations from {translation_file}")
    except Exception as e:
        logger.error(f"Error loading translations: {str(e)}")

def translate(key, default=None):
    """Get translation for key
    
    Args:
        key: Translation key
        default: Default value if key not found
        
    Returns:
        Translated string or default value
    """
    return _translations.get(key, default if default else key)
