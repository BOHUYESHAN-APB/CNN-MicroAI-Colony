"""
Theme Manager Utility
"""
import os
import logging
from typing import List, Optional, Dict, Any
import json

from .path_manager import get_themes_dir
from ..config import ConfigManager

logger = logging.getLogger(__name__)

class ThemeManager:
    """Theme manager singleton"""
    
    _instance = None
    _initialized = False
    _current_theme: Optional[str] = None
    _theme_data: Dict[str, Any] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
        
    def __init__(self):
        if not self._initialized:
            self.config = ConfigManager()
            self._load_themes()
            ThemeManager._initialized = True
            
    def _load_themes(self):
        """Load available themes"""
        try:
            themes_dir = get_themes_dir()
            
            for file in os.listdir(themes_dir):
                if file.endswith('.qss'):
                    theme_name = os.path.splitext(file)[0]
                    theme_path = os.path.join(themes_dir, file)
                    
                    # Load theme file
                    with open(theme_path, 'r', encoding='utf-8') as f:
                        self._theme_data[theme_name] = f.read()
                        logger.info(f"Loaded theme: {theme_name}")
                        logger.info(f"Available themes: {self.get_available_themes()}")
                        
            # Set default theme
            default_theme = self.config.get("theme.default", "siui_dark")
            if default_theme in self._theme_data:
                self._current_theme = default_theme
                
        except Exception as e:
            logger.error(f"Error loading themes: {e}")
            
    def get_available_themes(self) -> List[str]:
        """Get list of available themes"""
        return list(self._theme_data.keys())
        
    def get_current_theme(self) -> Optional[str]:
        """Get current theme name"""
        return self._current_theme
        
    def get_theme_content(self, theme_name: str) -> Optional[str]:
        """Get theme content by name"""
        return self._theme_data.get(theme_name)
        
    def apply_theme(self, theme_name: str) -> bool:
        """Apply theme"""
        try:
            from PyQt6.QtWidgets import QApplication
            
            if theme_name not in self._theme_data:
                logger.error(f"Theme not found: {theme_name}")
                return False
                
            # Apply theme
            app = QApplication.instance()
            if app:
                app.setStyleSheet(self._theme_data[theme_name])
                self._current_theme = theme_name
                
                # Save to config
                self.config.set("theme.default", theme_name)
                self.config.save()
                
                logger.info(f"Applied theme: {theme_name}")
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"Error applying theme: {e}")
            return False
            
    @classmethod
    def get_instance(cls) -> 'ThemeManager':
        """Get ThemeManager singleton instance"""
        if cls._instance is None:
            cls._instance = ThemeManager()
        return cls._instance
