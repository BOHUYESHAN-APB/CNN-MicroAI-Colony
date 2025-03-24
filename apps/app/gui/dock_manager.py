"""
Dock manager implementation
停靠窗口管理器实现
"""
import os
import json
import logging
from PyQt6.QtWidgets import QDockWidget
from PyQt6.QtCore import Qt

logger = logging.getLogger(__name__)

class DockManager:
    """Manager for dock widgets"""
    
    def __init__(self, main_window):
        self.main_window = main_window
        self.docks = {}  # name -> dock widget
        self.layout_file = os.path.join(
            os.path.dirname(__file__), 
            "..", 
            "resources",
            "dock_layout.json"
        )
        
    def register_dock(self, dock):
        """Register a dock widget
        
        Args:
            dock: QDockWidget instance
        """
        if not isinstance(dock, QDockWidget):
            raise TypeError("dock must be a QDockWidget")
            
        name = dock.objectName()
        if not name:
            raise ValueError("dock must have an object name")
            
        self.docks[name] = dock
        
    def get_dock(self, name):
        """Get dock widget by name"""
        return self.docks.get(name)
        
    def save_layouts(self):
        """Save dock layouts to file"""
        try:
            layouts = {}
            for name, dock in self.docks.items():
                # Convert DockWidgetArea to int 
                area = self.main_window.dockWidgetArea(dock)
                if isinstance(area, Qt.DockWidgetArea):
                    area = int(area.value)
                    
                layouts[name] = {
                    'area': area,
                    'floating': dock.isFloating(),
                    'geometry': bytes(dock.saveGeometry()).hex()
                }
                
            # Create directory if needed
            os.makedirs(os.path.dirname(self.layout_file), exist_ok=True)
            
            with open(self.layout_file, 'w', encoding='utf-8') as f:
                json.dump(layouts, f, indent=2)
                logger.info("Saved dock layout")
                
        except Exception as e:
            logger.error(f"Error saving dock layout: {str(e)}")
            
    def restore_layouts(self):
        """Restore dock layouts from file"""
        try:
            if not os.path.exists(self.layout_file):
                return
                
            with open(self.layout_file, 'r', encoding='utf-8') as f:
                layouts = json.load(f)
                
            for name, layout in layouts.items():
                dock = self.get_dock(name)
                if dock:
                    # Restore geometry
                    if 'geometry' in layout:
                        dock.restoreGeometry(bytes.fromhex(layout['geometry']))
                        
                    # Restore area and floating state
                    self.main_window.addDockWidget(
                        Qt.DockWidgetArea(layout.get('area', Qt.DockWidgetArea.LeftDockWidgetArea.value)),
                        dock
                    )
                    dock.setFloating(layout.get('floating', False))
                    
        except Exception as e:
            logger.error(f"Error restoring dock layout: {str(e)}")
