# Utils package initialization
from .config import Config
from .batch_analysis import BatchAnalyzer
from .single_result import SingleResultExporter
from .report import ReportGenerator
from .visualization import Visualizer

__all__ = [
    'Config',
    'BatchAnalyzer',
    'SingleResultExporter',
    'ReportGenerator',
    'Visualizer'
]

# Module level configuration
import matplotlib
matplotlib.use('agg')  # Use non-interactive backend

# Configure logging
import logging
logger = logging.getLogger(__name__)

# Initialize paths
from pathlib import Path
UTILS_DIR = Path(__file__).parent
APP_DIR = UTILS_DIR.parent
PROJECT_DIR = APP_DIR.parent

# Create necessary directories
REQUIRED_DIRS = [
    APP_DIR / 'logs',
    APP_DIR / 'results',
    APP_DIR / 'temp',
    APP_DIR / 'config'
]

for directory in REQUIRED_DIRS:
    try:
        directory.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        logger.warning(f"Could not create directory {directory}: {e}")

# Initialize configuration if needed
CONFIG_FILE = APP_DIR / 'config' / 'config.yaml'
if not CONFIG_FILE.exists():
    try:
        DEFAULT_CONFIG = APP_DIR / 'config.yaml'
        if DEFAULT_CONFIG.exists():
            from shutil import copy
            CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
            copy(DEFAULT_CONFIG, CONFIG_FILE)
            logger.info(f"Copied default config to {CONFIG_FILE}")
    except Exception as e:
        logger.warning(f"Could not copy default config: {e}")
