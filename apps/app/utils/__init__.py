"""
Utility module initialization
工具模块初始化
"""
from .config import ConfigManager
from .i18n import translate
from .project_manager import ProjectManager
from .image_preprocessing import preprocess_image

# Create global config instance
config_manager = ConfigManager()
load_config = config_manager.load
save_config = config_manager.save
