import os
import json
import logging
from pathlib import Path
import locale
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class I18NManager:
    """国际化管理器"""
    _instance = None
    _initialized = False
    _translations: Dict[str, Dict] = {}
    _current_locale = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_if_needed()
        return cls._instance

    def __init__(self):
        pass  # 移除这里的初始化，改为在 __new__ 中完成
    
    def _load_if_needed(self):
        """如果需要则加载翻译"""
        if not self._initialized:
            self.load_translations()
    
    @property
    def i18n_dir(self) -> Path:
        """获取翻译文件目录"""
        return Path(__file__).parent.parent / 'resources' / 'i18n'

    def load_translations(self):
        """加载所有翻译文件"""
        if self._initialized:
            return

        logger.info("Loading translations")
        total_strings = 0

        # 扫描翻译文件目录
        for file_path in self.i18n_dir.glob('*.json'):
            locale_code = file_path.stem
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    translations = json.load(f)
                    self._translations[locale_code] = translations
                    
                    # 计算翻译字符串数量
                    strings_count = self._count_strings(translations)
                    total_strings += strings_count
                    logger.info(f"Loaded {strings_count} translations for {locale_code}")
            except Exception as e:
                logger.error(f"Failed to load translations for {locale_code}: {e}")

        logger.info(f"Total loaded translations: {total_strings}")
        logger.info(f"Available locales: {list(self._translations.keys())}")

        # 设置默认区域
        self._set_default_locale()
        self._initialized = True

        self._log_status()

    def _count_strings(self, translations: dict, prefix="") -> int:
        """递归计算翻译字符串数量"""
        count = 0
        for key, value in translations.items():
            if isinstance(value, dict):
                count += self._count_strings(value, f"{prefix}{key}.")
            else:
                count += 1
        return count

    def _set_default_locale(self):
        """设置默认区域"""
        # 首选顺序：配置文件 > 系统区域 > 英文
        if not self._current_locale:
            try:
                from .config import ConfigManager
                config = ConfigManager()
                configured_locale = config.get("language")
                if configured_locale and configured_locale in self._translations:
                    self._current_locale = configured_locale
                    logger.info(f"Using configured locale: {configured_locale}")
                    return
            except Exception as e:
                logger.warning(f"Failed to load locale from config: {e}")

        # 尝试使用系统区域
        try:
            system_locale = locale.getdefaultlocale()[0]
            if system_locale:
                # 处理类似 zh_CN, zh_TW 等格式
                lang_code = system_locale.split('_')[0]
                region_code = system_locale.split('_')[1] if '_' in system_locale else None
                
                # 尝试完整匹配
                if system_locale in self._translations:
                    self._current_locale = system_locale
                # 尝试匹配带地区的版本
                elif region_code and f"{lang_code}_{region_code}" in self._translations:
                    self._current_locale = f"{lang_code}_{region_code}"
                # 尝试仅语言匹配
                elif lang_code in self._translations:
                    self._current_locale = lang_code
                
                if self._current_locale:
                    logger.info(f"Using system locale: {self._current_locale}")
                    return
        except Exception as e:
            logger.warning(f"Failed to detect system locale: {e}")

        # 默认使用英文
        self._current_locale = "en"
        logger.info("Set locale to en")

    def get_string(self, key: str, default: str = None) -> str:
        """获取翻译字符串"""
        self._load_if_needed()

        try:
            # 分割键路径
            keys = key.split('.')
            value = self._translations.get(self._current_locale, {})
            
            # 遍历键路径
            for k in keys:
                value = value[k]
            
            return value if isinstance(value, str) else default
        except (KeyError, TypeError):
            logger.warning(f"Missing translation for key '{key}' in locale '{locale}'")
            # 如果当前语言找不到，尝试使用英文
            if self._current_locale != "en":
                try:
                    value = self._translations.get("en", {})
                    for k in keys:
                        value = value[k]
                    logger.info(f"Using fallback translation for key '{key}': {value}")
                    return value if isinstance(value, str) else default
                except (KeyError, TypeError):
                    pass
            
            default_value = default if default is not None else key
            logger.warning(f"Using default value for key '{key}': {default_value}")
            return default_value

    def get_current_locale(self) -> str:
        """获取当前区域"""
        return self._current_locale

    def set_locale(self, locale_code: str) -> bool:
        """设置当前区域"""
        if locale_code in self._translations:
            self._current_locale = locale_code
            logger.info(f"Set locale to {locale_code}")
            return True
        return False

    def get_available_locales(self) -> list:
        """获取可用的区域列表"""
        return list(self._translations.keys())

    def _log_status(self):
        """记录当前状态"""
        logger.info("=== Translation Status ===")
        logger.info(f"Current locale: {self._current_locale}")
        logger.info(f"Available locales: {self.get_available_locales()}")
        logger.info(f"Initialized: {self._initialized}")
        if self._current_locale:
            logger.info(f"Loaded strings for current locale: {self._count_strings(self._translations[self._current_locale])}")
        logger.info("=====================")

def init_translations():
    """初始化翻译"""
    i18n = I18NManager()
    i18n._load_if_needed()  # 确保翻译已加载
    logger.info("Translations initialized successfully")
    return i18n

def get_i18n():
    """获取翻译管理器实例"""
    return I18NManager()
