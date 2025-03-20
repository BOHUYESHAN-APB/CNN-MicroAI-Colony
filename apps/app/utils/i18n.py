"""
Internationalization support
国际化支持
"""
import os
import json
import logging

logger = logging.getLogger(__name__)

class I18nManager:
    """Internationalization manager"""
    
    def __init__(self):
        self.translations = {}
        self.current_locale = 'zh_CN'
    
    def initialize(self):
        """Initialize i18n system"""
        try:
            # 加载中文翻译文件
            trans_file = os.path.join(os.path.dirname(__file__), 
                                    '..', 'resources', 'i18n',
                                    f'{self.current_locale}.json')
            
            if os.path.exists(trans_file):
                with open(trans_file, 'r', encoding='utf-8') as f:
                    self.translations = json.load(f)
                logger.info(f"Loaded translations from {trans_file}")
            else:
                logger.warning(f"Translation file not found: {trans_file}")
                
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize i18n: {e}")
            return False
    
    def translate(self, text):
        """Translate text based on current locale"""
        # 如果有翻译则使用翻译，否则返回原文
        return self.translations.get(text, text)
    
    @staticmethod
    def _static_translate(text):
        """Static translation method for compatibility"""
        return text

# Global i18n manager instance
_i18n_manager = I18nManager()

def translate(text):
    """Translate text based on current locale"""
    # Use global manager instance
    return _i18n_manager.translate(text)
