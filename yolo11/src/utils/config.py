"""
Configuration handling utilities for YOLOv11.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, Union, List

class ConfigError(Exception):
    """Configuration validation error."""
    pass

class Config:
    """Configuration manager for YOLOv11."""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration.
        
        Args:
            config_path: Path to config YAML file. If None, uses default config.
        """
        self.config_path = config_path or str(Path(__file__).parent.parent / 'config.yaml')
        self.config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
            
        with open(self.config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            
        # Validate advanced configurations
        self._validate_config(config)
        return config
    
    def _validate_config(self, config: Dict[str, Any]) -> None:
        """
        Validate configuration values.
        
        Raises:
            ConfigError: If configuration is invalid
        """
        # Validate model config
        model_config = config.get('model', {})
        if not model_config.get('name') == 'yolo11':
            raise ConfigError("Model name must be 'yolo11'")
            
        # Validate residual stages
        stages = model_config.get('backbone', {}).get('residual_stages', [])
        if not isinstance(stages, list) or not all(isinstance(x, int) for x in stages):
            raise ConfigError("backbone.residual_stages must be a list of integers")
            
        # Validate attention config
        attention = model_config.get('head', {}).get('attention', {})
        if attention.get('reduction', 0) <= 0:
            raise ConfigError("head.attention.reduction must be positive")
            
        # Validate training config
        train_config = config.get('training', {})
        if train_config.get('batch_size', 0) <= 0:
            raise ConfigError("training.batch_size must be positive")
            
        # Validate optimization config
        opt_config = config.get('optimization', {})
        if opt_config.get('gradient_clipping', 0) < 0:
            raise ConfigError("optimization.gradient_clipping must be non-negative")
    
    def get_model_config(self) -> Dict[str, Any]:
        """Get model configuration section."""
        return self.config.get('model', {})
    
    def get_training_config(self) -> Dict[str, Any]:
        """Get training configuration section."""
        return self.config.get('training', {})
    
    def get_testing_config(self) -> Dict[str, Any]:
        """Get testing configuration section."""
        return self.config.get('testing', {})
    
    def get_data_config(self) -> Dict[str, Any]:
        """Get data configuration section."""
        return self.config.get('data', {})
    
    def get_optimization_config(self) -> Dict[str, Any]:
        """Get optimization configuration section."""
        return self.config.get('optimization', {})
    
    def update_config(self, updates: Dict[str, Any]) -> None:
        """
        Update configuration with new values.
        
        Args:
            updates: Dictionary of configuration updates
        """
        def deep_update(d, u):
            for k, v in u.items():
                if isinstance(v, dict) and k in d:
                    deep_update(d[k], v)
                else:
                    d[k] = v
                    
        deep_update(self.config, updates)
        
        # Revalidate after update
        self._validate_config(self.config)
    
    def save_config(self, save_path: Optional[str] = None) -> None:
        """
        Save current configuration to file.
        
        Args:
            save_path: Path to save config. If None, uses current config path.
        """
        save_path = save_path or self.config_path
        
        with open(save_path, 'w', encoding='utf-8') as f:
            yaml.safe_dump(self.config, f, indent=2, sort_keys=False)
            
    def __str__(self) -> str:
        """Get string representation of config."""
        return yaml.safe_dump(self.config, indent=2, sort_keys=False)
