"""
Configuration Manager
配置管理器
"""
import os
import json
import logging
from typing import Any, Dict, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class ConfigManager:
    """Manages application configuration"""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self._initialized = True
        self.config = {}
        self._config_file = os.path.join("apps", "app", "resources", "config.json")
        self.load()
    
    def load(self) -> bool:
        """Load configuration from file"""
        try:
            if os.path.exists(self._config_file):
                with open(self._config_file, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
                logger.info(f"Configuration loaded from {self._config_file}")
            else:
                self._create_default_config()
            return True
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            self._create_default_config()
            return False
    
    def save(self) -> bool:
        """Save configuration to file"""
        try:
            os.makedirs(os.path.dirname(self._config_file), exist_ok=True)
            with open(self._config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            logger.info(f"Configuration saved to {self._config_file}")
            return True
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
            return False
    
    def _create_default_config(self):
        """Create default configuration"""
        self.config = {
            "interface": {
                "theme": "default",
                "language": "en",
                "start_maximized": False
            },
            "analysis": {
                "model": {
                    "type": "faster_rcnn_resnet50",
                    "confidence_threshold": 0.5,
                    "use_gpu": False
                },
                "detection": {
                    "min_size": 5,
                    "max_size": 100,
                    "overlap_threshold": 0.3
                }
            },
            "preprocessing": {
                "enabled": {
                    "remove_glare": True,
                    "normalize_lighting": True,
                    "clahe": True,
                    "gaussian_blur": False,
                    "adaptive_thresholding": False
                },
                "parameters": {
                    "glare_threshold": 220,
                    "clahe_clip_limit": 4.0,
                    "clahe_grid_size": 16,
                    "blur_kernel_size": 5,
                    "adaptive_thresh_block_size": 11,
                    "adaptive_thresh_c": 2
                }
            },
            "paths": {
                "last_project": "",
                "last_image_dir": "",
                "export_dir": "results"
            }
        }
        logger.info("Created default configuration")
        self.save()
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        try:
            value = self.config
            for k in key.split('.'):
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any) -> bool:
        """Set configuration value"""
        try:
            keys = key.split('.')
            config = self.config
            for k in keys[:-1]:
                if k not in config:
                    config[k] = {}
                config = config[k]
            config[keys[-1]] = value
            return True
        except Exception as e:
            logger.error(f"Error setting configuration value: {e}")
            return False
            
    def get_preprocessing_config(self) -> Dict:
        """Get preprocessing configuration with defaults"""
        enabled = self.get("preprocessing.enabled", {
            "remove_glare": True,
            "normalize_lighting": True,
            "clahe": True,
            "gaussian_blur": False,
            "adaptive_thresholding": False
        })
        
        params = self.get("preprocessing.parameters", {
            "glare_threshold": 220,
            "clahe_clip_limit": 4.0,
            "clahe_grid_size": 16,
            "blur_kernel_size": 5,
            "adaptive_thresh_block_size": 11,
            "adaptive_thresh_c": 2
        })
        
        return {
            **enabled,
            **params
        }
