"""
MicroAI-Colony Package
Automated bacterial colony counter using AI
"""

# Package version and metadata
__version__ = "1.0.0"
__author__ = "MicroAI Team"
__license__ = "MIT"
__website__ = "https://github.com/microai-team/colony-counter"

# Application information
APP_NAME = "MicroAI-Colony"
APP_DESCRIPTION = "Automated bacterial colony counting and analysis using AI"
APP_ORGANIZATION = "MicroAI Team"
APP_DOMAIN = "microai.team"
APP_SUPPORT_EMAIL = "support@microai.team"

# Required Python version
REQUIRED_PYTHON = (3, 7)

# Default configuration file
CONFIG_FILE = "config/defaults/defaults.json"

# Resource directories
RESOURCE_DIRS = [
    "resources/i18n",
    "resources/themes",
    "resources/models",
    "resources/icons"
]

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
        },
        "file": {
            "level": "INFO",
            "formatter": "standard",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "app.log",
            "maxBytes": 10485760,
            "backupCount": 5
        }
    },
    "loggers": {
        "": {
            "handlers": ["default", "file"],
            "level": "INFO",
            "propagate": True
        }
    }
}

# Module exports
__all__ = [
    '__version__',
    '__author__',
    '__license__',
    '__website__',
    'APP_NAME',
    'APP_DESCRIPTION',
    'APP_ORGANIZATION',
    'APP_DOMAIN',
    'APP_SUPPORT_EMAIL',
    'REQUIRED_PYTHON',
    'CONFIG_FILE',
    'RESOURCE_DIRS',
    'LOG_CONFIG'
]
