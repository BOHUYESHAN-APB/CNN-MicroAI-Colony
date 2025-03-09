"""
MicroAI-Colony - Bacterial Colony Analysis Software
"""
import os
import sys
import logging
import logging.config
from typing import Dict, Any

# Application metadata
__version__ = "1.0.0"
__author__ = "MicroAI Team"
__license__ = "MIT"
__website__ = "https://github.com/microai-team/colony-counter"

APP_NAME = "MicroAI-Colony"
APP_ORGANIZATION = "MicroAI Team"
APP_DOMAIN = "microai.team"
APP_DESCRIPTION = "Automated bacterial colony counting and analysis using AI"

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
            "level": "INFO",
            "formatter": "standard",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout"
        }
    },
    "loggers": {
        "": {
            "handlers": ["default"],
            "level": "INFO",
            "propagate": True
        }
    }
}

# Setup logging
logging.config.dictConfig(LOG_CONFIG)
logger = logging.getLogger(__name__)

def initialize_app() -> bool:
    """Initialize application components"""
    try:
        # Import required components only when needed
        from .utils.i18n import initialize as init_i18n
        from .utils.config import ConfigManager
        from .check_resources import check_all
        from .gui import apply_theme, initialize_gui
        
        # Create required directories
        from .utils.path_manager import create_app_directories
        if not create_app_directories():
            logger.error("Failed to create application directories")
            return False
            
        # Check resources
        if not check_all():
            logger.error("Resource check failed")
            return False
            
        # Initialize configuration
        config = ConfigManager()
        if not config:
            logger.error("Failed to initialize configuration")
            return False
            
        # Initialize translations
        if not init_i18n():
            logger.error("Failed to initialize translations")
            return False
            
        # Initialize GUI
        if not initialize_gui():
            logger.error("Failed to initialize GUI")
            return False
            
        logger.info("Application initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error initializing application: {e}")
        return False

def cleanup():
    """Clean up application resources"""
    try:
        # Import required components only when needed
        from .utils.config import ConfigManager
        from .utils.project_manager import ProjectManager
        
        # Save configuration
        config = ConfigManager()
        if config:
            config.save()
            
        # Close current project
        project = ProjectManager()
        if project:
            project.close_project()
            
        logger.info("Application cleanup completed")
        
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")

# Application specific exceptions
class AppError(Exception):
    """Base application exception"""
    pass

class ResourceError(AppError):
    """Resource related errors"""
    pass

class ConfigError(AppError):
    """Configuration related errors"""
    pass

class ProjectError(AppError):
    """Project related errors"""
    pass

class TranslationError(AppError):
    """Translation related errors"""
    pass

# Module exports
__all__ = [
    '__version__',
    '__author__',
    '__license__',
    '__website__',
    'APP_NAME',
    'APP_ORGANIZATION',
    'APP_DOMAIN',
    'APP_DESCRIPTION',
    'initialize_app',
    'cleanup',
    'AppError',
    'ResourceError',
    'ConfigError',
    'ProjectError',
    'TranslationError'
]
