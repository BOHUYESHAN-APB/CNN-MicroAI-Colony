"""
Utility modules
"""
from .config import ConfigManager
from .i18n import tr, get_locale, set_locale, initialize as init_i18n
from .path_manager import (
    get_app_dir,
    get_config_dir,
    get_data_dir,
    get_logs_dir,
    get_resources_dir,
    get_themes_dir,
    get_i18n_dir,
    get_projects_dir,
    get_default_project_path,
    clean_project_name,
    normalize_path,
    ensure_project_structure,
    list_project_directories,
    get_project_images,
    create_app_directories
)
from .project_manager import ProjectManager
from .theme_manager import ThemeManager

# Initialize singletons
config_manager = ConfigManager()
project_manager = ProjectManager()
theme_manager = ThemeManager()

__all__ = [
    # Classes
    'ConfigManager',
    'ProjectManager',
    'ThemeManager',

    # Singleton instances
    'config_manager',
    'project_manager',
    'theme_manager',

    # I18n functions
    'tr',
    'get_locale',
    'set_locale',
    'init_i18n',

    # Path functions
    'get_app_dir',
    'get_config_dir',
    'get_data_dir',
    'get_logs_dir',
    'get_resources_dir',
    'get_themes_dir',
    'get_i18n_dir',
    'get_projects_dir',
    'get_default_project_path',
    'clean_project_name',
    'normalize_path',
    'ensure_project_structure',
    'list_project_directories',
    'get_project_images',
    'create_app_directories'
]
