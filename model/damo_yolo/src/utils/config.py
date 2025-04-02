"""
Configuration handling utilities for DAMO-YOLO.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional

class Config:
    """Configuration manager for DAMO-YOLO."""
    
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
            
        return config
    
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
