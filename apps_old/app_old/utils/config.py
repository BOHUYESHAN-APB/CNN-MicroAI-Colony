"""
Configuration Manager
"""
import os
import json
import logging
from typing import Any, Dict, Optional
from ..config.defaults import DEFAULTS
from ..config import save_config, load_config, merge_configs

logger = logging.getLogger(__name__)

class ConfigManager:
    """Configuration manager singleton"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
        return cls._instance
        
    def __init__(self):
        if not self._initialized:
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
            from ..config.defaults import DEFAULTS
            default_value = DEFAULTS
            try:
                for k in key.split('.'):
                    default_value = default_value[k]
                return default_value
            except:
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
        try:
            return save_config(self._config)
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
            return False
            
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
