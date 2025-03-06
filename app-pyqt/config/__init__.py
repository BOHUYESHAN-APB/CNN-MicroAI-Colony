import logging
from pathlib import Path
from .config_manager import ConfigManager

# Initialize logging
logger = logging.getLogger(__name__)

def get_config_paths():
    """Get configuration file paths"""
    app_dir = Path(__file__).parent.parent
    
    paths = {
        'defaults': app_dir / 'config' / 'defaults' / 'defaults.yaml',
        'user': app_dir / 'config' / 'config.yaml',
        'app': app_dir / 'config.yaml'
    }
    
    return paths

def initialize_config():
    """Initialize configuration system"""
    try:
        paths = get_config_paths()
        
        # Try to load configuration in order: defaults -> app -> user
        config_path = None
        for key, path in paths.items():
            if path.exists():
                config_path = path
                logger.info(f"Using {key} configuration from: {path}")
                break
                
        if config_path is None:
            raise FileNotFoundError("No configuration file found")
            
        # Create configuration manager
        config_manager = ConfigManager(config_path)
        
        # If using defaults, copy to user config
        if config_path == paths['defaults']:
            from shutil import copy
            paths['user'].parent.mkdir(parents=True, exist_ok=True)
            copy(config_path, paths['user'])
            logger.info(f"Copied default config to: {paths['user']}")
            
        return config_manager
        
    except Exception as e:
        logger.error(f"Failed to initialize configuration: {e}")
        raise

# Create global configuration instance
config = initialize_config()

# Export public interface
__all__ = ['config']
