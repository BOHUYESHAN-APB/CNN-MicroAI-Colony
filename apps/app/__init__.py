"""
Colony Detection and Analysis Software
菌落检测与分析软件
"""
import os
import sys
import logging
import logging.config
from typing import Dict, Any

# Application metadata
__version__ = "1.0.0"
__author__ = "MicroAI Team"
__license__ = "GPL-3.0"

APP_NAME = "Colony Analyzer"
APP_ORGANIZATION = "MicroAI"
APP_DOMAIN = "microai.dev"
APP_DESCRIPTION = "Automated bacterial colony detection and analysis"

# Logging configuration
LOG_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        }
    },
    "handlers": {
        "default": {
            "level": "DEBUG",
            "formatter": "standard",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout"
        },
        "file": {
            "level": "DEBUG",
            "formatter": "standard",
            "class": "logging.FileHandler",
            "filename": "app.log",
            "mode": "a"
        }
    },
    "loggers": {
        "": {
            "handlers": ["default", "file"],
            "level": "INFO",
            "propagate": True
        },
        "app.models.colony_detector": {
            "handlers": ["default", "file"],
            "level": "DEBUG",
            "propagate": False
        },
        "app.gui.main_window": {
            "handlers": ["default", "file"],
            "level": "DEBUG",
            "propagate": False
        }
    }
}

# Setup logging
logging.config.dictConfig(LOG_CONFIG)
logger = logging.getLogger(__name__)

def initialize_app() -> bool:
    """Initialize application components"""
    try:
        # Import required components
        from .utils.config import ConfigManager
        from .utils.resource_checker import check_all
        
        # Check resources (config, translations, themes)
        if not check_all():
            logger.error("Resource check failed")
            return False
            
        # Initialize configuration
        config = ConfigManager()
        if not config:
            logger.error("Failed to initialize configuration")
            return False
            
        logger.info("Application initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error initializing application: {e}")
        return False

def cleanup():
    """Clean up application resources"""
    try:
        from .utils.config import ConfigManager
        
        # Save configuration
        config = ConfigManager()
        if config:
            config.save()
            
        logger.info("Application cleanup completed")
        
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")

# Application exceptions
class AppError(Exception):
    """Base application exception"""
    pass

class ResourceError(AppError):
    """Resource related errors"""
    pass

class ConfigError(AppError):
    """Configuration related errors"""
    pass

# Module exports
__all__ = [
    '__version__',
    '__author__',
    '__license__',
    'APP_NAME',
    'APP_ORGANIZATION',
    'APP_DOMAIN',
    'APP_DESCRIPTION',
    'initialize_app',
    'cleanup',
    'AppError',
    'ResourceError',
    'ConfigError'
]
