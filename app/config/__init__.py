"""
Configuration module
"""
from .config_manager import ConfigManager, load_config, save_config, merge_configs
from .defaults import DEFAULTS

# Module exports
__all__ = [
    'ConfigManager',
    'DEFAULTS',
    'load_config',
    'save_config',
    'merge_configs'
]
