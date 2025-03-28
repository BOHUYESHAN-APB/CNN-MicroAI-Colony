"""
Configuration management utility
配置管理工具
"""
import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class ConfigManager:
    """Configuration manager singleton"""
    _instance = None
    _config_file = Path('config/app_config.json')
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance._config = {}
            cls._instance._load_config()
        return cls._instance
    
    def _load_config(self):
        """Load configuration from file"""
        try:
            if self._config_file.exists():
                with open(self._config_file, 'r', encoding='utf-8') as f:
                    self._config = json.load(f)
                logger.debug("Configuration loaded successfully")
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            self._config = {}
    
    def save(self):
        """Save current configuration to file"""
        try:
            self._config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self._config_file, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=4, ensure_ascii=False)
            logger.debug("Configuration saved successfully")
            return True
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        return self._config.get(key, default)
    
    def set(self, key: str, value: Any):
        """Set configuration value"""
        self._config[key] = value
        self.save()
    
    @property
    def model_path(self) -> Optional[str]:
        """Get model file path"""
        return self.get('model_path')
    
    @model_path.setter
    def model_path(self, path: str):
        """Set model file path"""
        if path and Path(path).exists():
            self.set('model_path', str(path))
        else:
            logger.warning(f"Invalid model path: {path}")
    
    @property
    def config_path(self) -> Optional[str]:
        """Get model config file path"""
        return self.get('config_path')
    
    @config_path.setter
    def config_path(self, path: str):
        """Set model config file path"""
        if path and Path(path).exists():
            self.set('config_path', str(path))
        else:
            logger.warning(f"Invalid config path: {path}")
    
    @property
    def device(self) -> str:
        """Get computation device (cpu/cuda)"""
        return self.get('device', 'cpu')
    
    @device.setter
    def device(self, device: str):
        """Set computation device"""
        if device in ['cpu', 'cuda']:
            self.set('device', device)
        else:
            logger.warning(f"Invalid device: {device}")
    
    @property
    def all_settings(self) -> Dict[str, Any]:
        """Get all configuration settings"""
        return self._config.copy()
