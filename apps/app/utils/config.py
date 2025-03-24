"""
Configuration utilities
配置工具
"""
import os
import json
import logging

logger = logging.getLogger(__name__)

CONFIG_FILE = os.path.join(
    os.path.dirname(__file__), 
    "..", 
    "resources",
    "config.json"
)

def load_config():
    """Load configuration from file
    
    Returns:
        Dict with configuration or None if failed
    """
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                logger.info(f"Configuration loaded from {CONFIG_FILE}")
                return config
    except Exception as e:
        logger.error(f"Error loading configuration: {str(e)}")
        
    return None

def save_config(config):
    """Save configuration to file
    
    Args:
        config: Configuration dict
    """
    try:
        # Create directory if needed
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
        
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
            logger.info(f"Configuration saved to {CONFIG_FILE}")
            
    except Exception as e:
        logger.error(f"Error saving configuration: {str(e)}")

def get_default_config():
    """Get default configuration
    
    Returns:
        Dict with default configuration
    """
    return {
        'window_geometry': None,
        'window_state': None,
        'project_dir': None,
        'last_dir': None,
        'theme': 'dark',
        'language': 'zh_CN'
    }
