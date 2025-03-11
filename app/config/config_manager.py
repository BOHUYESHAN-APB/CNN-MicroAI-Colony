"""
Configuration Manager
"""
import os
import json
import logging
from typing import Any, Dict, Optional

from .defaults import DEFAULTS
from ..utils.path_manager import get_config_dir

logger = logging.getLogger(__name__)

def merge_configs(default: Dict[str, Any], user: Dict[str, Any]) -> Dict[str, Any]:
    """Merge two configuration dictionaries recursively"""
    result = default.copy()
    
    def _merge(d1, d2):
        for key, value in d2.items():
            if key in d1 and isinstance(d1[key], dict) and isinstance(value, dict):
                _merge(d1[key], value)
            else:
                d1[key] = value
    
    _merge(result, user)
    return result

def load_config() -> Dict[str, Any]:
    """Load user configuration"""
    config_file = os.path.join(get_config_dir(), "config.json")
    
    if not os.path.exists(config_file):
        return {}
        
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        return {}

def save_config(config: Dict[str, Any]) -> bool:
    """Save user configuration"""
    try:
        config_dir = get_config_dir()
        os.makedirs(config_dir, exist_ok=True)
        
        config_file = os.path.join(config_dir, "config.json")
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
            
        return True
        
    except Exception as e:
        logger.error(f"Error saving config: {e}")
        return False

class ConfigManager:
    """Configuration manager singleton"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
        return cls._instance
        
    def __init__(self):
        if not ConfigManager._initialized:
            self._config = {}
            self.load()
            ConfigManager._initialized = True
            
    @property
    def config(self) -> Dict[str, Any]:
        """Get current configuration"""
        return self._config
        
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key"""
        try:
            # Handle nested keys
            keys = key.split('.')
            value = self._config
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            # Return default from config defaults if exists
            try:
                value = DEFAULTS
                for k in key.split('.'):
                    value = value[k]
                return value
            except (KeyError, TypeError):
                return default
            
    def set(self, key: str, value: Any):
        """Set configuration value"""
        try:
            # Handle nested keys
            keys = key.split('.')
            config = self._config
            
            # Navigate to the correct level
            for k in keys[:-1]:
                if k not in config or not isinstance(config[k], dict):
                    config[k] = {}
                config = config[k]
                
            # Set the value
            config[keys[-1]] = value
            
        except Exception as e:
            logger.error(f"Error setting config value: {e}")
            
    def load(self) -> bool:
        """Load configuration from file"""
        try:
            # Load user config
            user_config = load_config()
                
            # Merge with defaults
            self._config = merge_configs(DEFAULTS, user_config)
            
            logger.info("Configuration loaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            self._config = DEFAULTS.copy()
            return False
            
    def save(self) -> bool:
        """Save configuration to file"""
        return save_config(self._config)
            
    def reset(self, key: Optional[str] = None):
        """Reset configuration to defaults"""
        if key is None:
            # Reset all
            self._config = DEFAULTS.copy()
        else:
            # Reset specific key
            try:
                keys = key.split('.')
                value = DEFAULTS
                for k in keys:
                    value = value[k]
                    
                config = self._config
                for k in keys[:-1]:
                    if k not in config:
                        config[k] = {}
                    config = config[k]
                config[keys[-1]] = value
                
            except (KeyError, TypeError):
                pass
                
    def reset_all(self):
        """Reset all settings to defaults"""
        self._config = DEFAULTS.copy()
        self.save()
        
    @classmethod
    def get_instance(cls) -> 'ConfigManager':
        """Get ConfigManager singleton instance"""
        if cls._instance is None:
            cls._instance = ConfigManager()
        return cls._instance
