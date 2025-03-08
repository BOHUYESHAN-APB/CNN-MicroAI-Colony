import os
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class ConfigManager:
    """配置管理类"""
    _instance = None
    _config = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._config:
            self.load()
    
    @property
    def config_file(self):
        """获取配置文件路径"""
        return Path(__file__).parent.parent / 'config' / 'config.json'
    
    def load(self):
        """加载配置"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self._config = json.load(f)
                logger.info("Configuration loaded successfully")
            else:
                self._load_defaults()
                logger.info("Default configuration loaded")
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            self._load_defaults()
    
    def _load_defaults(self):
        """加载默认配置"""
        try:
            default_file = Path(__file__).parent.parent / 'config' / 'defaults' / 'defaults.json'
            if default_file.exists():
                with open(default_file, 'r', encoding='utf-8') as f:
                    self._config = json.load(f)
                logger.info("Default configuration loaded from file")
            else:
                self._config = {
                    "default_path": os.path.expanduser("~/Desktop/MicroAI_Detect"),
                    "export_formats": ["json", "csv", "xlsx"],
                    "analysis_iterations": 100,
                    "window": {
                        "maximized": False,
                        "width": 1200,
                        "height": 800
                    }
                }
                logger.info("Built-in default configuration loaded")
        except Exception as e:
            logger.error(f"Failed to load default configuration: {e}")
            self._config = {}
    
    def save(self):
        """保存配置"""
        try:
            # 确保配置目录存在
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=4, ensure_ascii=False)
            logger.info("Configuration saved successfully")
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
    
    def get(self, key, default=None):
        """获取配置值"""
        try:
            value = self._config
            for k in key.split('.'):
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key, value):
        """设置配置值"""
        try:
            keys = key.split('.')
            config = self._config
            
            # 遍历到最后一个键之前的所有键
            for k in keys[:-1]:
                if k not in config:
                    config[k] = {}
                config = config[k]
            
            # 设置最后一个键的值
            config[keys[-1]] = value
            
            # 保存配置
            self.save()
            logger.info(f"Configuration updated: {key} = {value}")
        except Exception as e:
            logger.error(f"Failed to set configuration {key}: {e}")

def init_config():
    """初始化配置管理器"""
    config_manager = ConfigManager()
    config_manager.load()
    return config_manager

def get_config():
    """获取配置管理器实例"""
    return ConfigManager()
