import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Union
from copy import deepcopy

logger = logging.getLogger(__name__)

def _resolve_path(path: Union[str, Path]) -> Path:
    """Resolve configuration file path"""
    path = Path(path)
    
    if not path.is_absolute():
        # Try relative to current directory
        if path.exists():
            return path.resolve()
            
        # Try relative to app directory
        app_dir = Path(__file__).parent.parent
        app_path = app_dir / path
        if app_path.exists():
            return app_path
            
    return path

class ConfigManager:
    """Manage application configuration"""
    
    def __init__(self, config_path: Union[str, Path]):
        """
        Initialize configuration manager
        
        Args:
            config_path: Path to configuration file
        """
        self.config_path = _resolve_path(config_path)
        self.default_config = self._load_yaml(self.config_path)
        self.config = deepcopy(self.default_config)
        self._modified = False
        
    def _load_yaml(self, path: Union[str, Path]) -> Dict[str, Any]:
        """Load YAML file"""
        try:
            path = Path(path)
            if not path.exists():
                raise FileNotFoundError(f"Config file not found: {path}")
                
            with open(path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
                
        except Exception as e:
            logger.error(f"Failed to load config file {path}: {e}")
            raise
            
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value
        
        Args:
            key: Configuration key (dot notation supported)
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
            if default is not None:
                return default
            # Try to get from default config
            try:
                current = self.default_config
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
            key: Configuration key (dot notation supported)
            value: Value to set
            
        Returns:
            True if successful
        """
        try:
            current = self.config
            keys = key.split('.')
            
            # Navigate to the last parent
            for k in keys[:-1]:
                if k not in current:
                    current[k] = {}
                current = current[k]
                
            # Set the value
            current[keys[-1]] = value
            self._modified = True
            return True
            
        except Exception as e:
            logger.error(f"Failed to set config value: {e}")
            return False
            
    def update(self, updates: Dict[str, Any]) -> bool:
        """
        Update configuration with dictionary
        
        Args:
            updates: Dictionary of updates
            
        Returns:
            True if successful
        """
        try:
            def update_recursive(current: Dict, updates: Dict):
                for key, value in updates.items():
                    if isinstance(value, dict) and key in current:
                        update_recursive(current[key], value)
                    else:
                        current[key] = value
            
            update_recursive(self.config, updates)
            self._modified = True
            return True
            
        except Exception as e:
            logger.error(f"Failed to update config: {e}")
            return False
            
    def update_from_file(self, path: Union[str, Path]) -> bool:
        """
        Update configuration from YAML file
        
        Args:
            path: Path to YAML file
            
        Returns:
            True if successful
        """
        try:
            path = _resolve_path(path)
            updates = self._load_yaml(path)
            return self.update(updates)
            
        except Exception as e:
            logger.error(f"Failed to update from file: {e}")
            return False
            
    def save(self, path: Optional[Union[str, Path]] = None) -> bool:
        """
        Save configuration to YAML file
        
        Args:
            path: Optional path to save to
            
        Returns:
            True if successful
        """
        try:
            if path is None:
                path = self.config_path
                
            path = Path(path)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(path, 'w', encoding='utf-8') as f:
                yaml.safe_dump(self.config, f, default_flow_style=False)
                
            self._modified = False
            logger.info(f"Configuration saved to {path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
            return False
            
    def reset(self) -> bool:
        """
        Reset configuration to defaults
        
        Returns:
            True if successful
        """
        try:
            self.config = deepcopy(self.default_config)
            self._modified = True
            return True
            
        except Exception as e:
            logger.error(f"Failed to reset config: {e}")
            return False
            
    def __getitem__(self, key: str) -> Any:
        """Dictionary-style access"""
        return self.get(key)
        
    def __setitem__(self, key: str, value: Any):
        """Dictionary-style assignment"""
        self.set(key, value)
        
    def __contains__(self, key: str) -> bool:
        """Check if key exists"""
        try:
            self.get(key)
            return True
        except:
            return False
