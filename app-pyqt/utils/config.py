import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class Config:
    """Configuration manager"""
    
    def __init__(self, config_path: str):
        """
        Initialize configuration
        
        Args:
            config_path: Path to YAML configuration file
        """
        self.config_path = Path(config_path)
        self.config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        try:
            if not self.config_path.exists():
                logger.warning(f"Config file not found: {self.config_path}")
                return self._get_default_config()
                
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                
            logger.info(f"Configuration loaded from {self.config_path}")
            return config
            
        except Exception as e:
            logger.error(f"Failed to load config: {str(e)}")
            return self._get_default_config()
            
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            'model': {
                'demo_mode': True,
                'inference_type': 'mock',
                'input_size': [800, 800],
                'confidence_threshold': 0.5
            },
            'ui': {
                'window_title': 'Colony Counter',
                'window_size': [1024, 768],
                'default_runs': 100
            },
            'results': {
                'save_formats': ['excel', 'csv'],
                'create_visualizations': True
            },
            'system': {
                'gpu_enabled': False,
                'num_threads': 4
            }
        }
        
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value
        
        Args:
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        try:
            current = self.config
            for k in key.split('.'):
                current = current[k]
            return current
        except (KeyError, TypeError):
            logger.debug(f"Config key not found: {key}, using default: {default}")
            return default
            
    def set(self, key: str, value: Any) -> bool:
        """
        Set configuration value
        
        Args:
            key: Configuration key
            value: Value to set
            
        Returns:
            True if successful, False otherwise
        """
        try:
            keys = key.split('.')
            current = self.config
            
            # Navigate to the last parent
            for k in keys[:-1]:
                if k not in current:
                    current[k] = {}
                current = current[k]
                
            # Set the value
            current[keys[-1]] = value
            
            # Save to file
            self.save()
            return True
            
        except Exception as e:
            logger.error(f"Failed to set config value: {str(e)}")
            return False
            
    def save(self) -> bool:
        """
        Save configuration to file
        
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.safe_dump(self.config, f, default_flow_style=False)
                
            logger.info(f"Configuration saved to {self.config_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save config: {str(e)}")
            return False
            
    def __getitem__(self, key: str) -> Any:
        """Dictionary-style access to configuration"""
        return self.get(key)
        
    def __setitem__(self, key: str, value: Any):
        """Dictionary-style setting of configuration"""
        self.set(key, value)

    def __contains__(self, key: str) -> bool:
        """Check if configuration key exists"""
        try:
            self.get(key)
            return True
        except:
            return False
