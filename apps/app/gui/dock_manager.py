"""
Dock widget management implementation
停靠窗口管理实现
"""
import logging
from PyQt6.QtWidgets import QMainWindow
from PyQt6.QtCore import Qt, QSettings, QByteArray, QSize
from PyQt6.QtGui import QBitmap

logger = logging.getLogger(__name__)

class DockManager:
    """Manager for dock widget states and layouts"""
    
    def __init__(self, main_window):
        """Initialize dock manager
        
        Args:
            main_window (QMainWindow): Parent main window
        """
        self.main_window = main_window
        self.dock_widgets = {}  # name -> widget mapping
        
        # Default dock positions
        self.default_positions = {
            "image_list_dock": Qt.DockWidgetArea.LeftDockWidgetArea,
            "image_viewer_dock": Qt.DockWidgetArea.RightDockWidgetArea,
            "result_image_dock": Qt.DockWidgetArea.RightDockWidgetArea,
            "result_stats_dock": Qt.DockWidgetArea.RightDockWidgetArea,
            "result_table_dock": Qt.DockWidgetArea.BottomDockWidgetArea
        }
        
        # Dock relationships for splitting
        self.dock_relationships = {
            "result_stats_dock": ("result_image_dock", Qt.Orientation.Vertical),
            "result_table_dock": ("result_stats_dock", Qt.Orientation.Vertical)
        }
        
    def register_dock(self, name, widget, area=None):
        """Register a dock widget
        
        Args:
            name (str): Unique name for the dock
            widget (QDockWidget): Dock widget to register
            area (Qt.DockWidgetArea, optional): Default dock area
        """
        self.dock_widgets[name] = widget
        if area:
            self.default_positions[name] = area
            
    def setup_docks(self):
        """Setup initial dock layout"""
        # Add all docks in their default positions
        for name, widget in self.dock_widgets.items():
            if name in self.default_positions:
                self.main_window.addDockWidget(self.default_positions[name], widget)
                
        # Setup relationships (splits)
        for child, (parent, orientation) in self.dock_relationships.items():
            if child in self.dock_widgets and parent in self.dock_widgets:
                self.main_window.splitDockWidget(
                    self.dock_widgets[parent],
                    self.dock_widgets[child],
                    orientation
                )
                
    def save_layout(self, settings_path=None):
        """Save current dock layout
        
        Args:
            settings_path (str, optional): Path to save settings file
        """
        try:
            if settings_path:
                settings = QSettings(settings_path, QSettings.Format.IniFormat)
            else:
                settings = QSettings('MicroAI', 'ColonyCounter')
                
            settings.setValue("windowGeometry", self.main_window.saveGeometry())
            settings.setValue("windowState", self.main_window.saveState())
            
            # Save individual dock states
            for name, widget in self.dock_widgets.items():
                settings.setValue(f"dock_{name}_visible", widget.isVisible())
                settings.setValue(f"dock_{name}_floating", widget.isFloating())
                if widget.isFloating():
                    settings.setValue(f"dock_{name}_geometry", widget.saveGeometry())
                    
            logger.info("Saved dock layout")
            
        except Exception as e:
            logger.error(f"Failed to save dock layout: {str(e)}")
            
    def load_layout(self, settings_path=None):
        """Load saved dock layout
        
        Args:
            settings_path (str, optional): Path to settings file
        """
        try:
            if settings_path:
                settings = QSettings(settings_path, QSettings.Format.IniFormat)
            else:
                settings = QSettings('MicroAI', 'ColonyCounter')
                
            # Restore window state
            geometry = settings.value("windowGeometry", QByteArray())
            state = settings.value("windowState", QByteArray())
            
            if geometry:
                self.main_window.restoreGeometry(geometry)
            if state:
                self.main_window.restoreState(state)
                
            # Restore individual dock states
            for name, widget in self.dock_widgets.items():
                visible = settings.value(f"dock_{name}_visible", True, type=bool)
                floating = settings.value(f"dock_{name}_floating", False, type=bool)
                
                widget.setVisible(visible)
                widget.setFloating(floating)
                
                if floating:
                    geometry = settings.value(f"dock_{name}_geometry", QByteArray())
                    if geometry:
                        widget.restoreGeometry(geometry)
                        
            logger.info("Restored dock layout")
            
        except Exception as e:
            logger.error(f"Failed to load dock layout: {str(e)}")
            
    def reset_layout(self):
        """Reset docks to default layout"""
        try:
            # Remove all docks
            for widget in self.dock_widgets.values():
                self.main_window.removeDockWidget(widget)
                widget.setVisible(False)
                widget.setFloating(False)
                
            # Re-add in default positions
            self.setup_docks()
            
            # Show all docks
            for widget in self.dock_widgets.values():
                widget.setVisible(True)
                
            logger.info("Reset dock layout to default")
            
        except Exception as e:
            logger.error(f"Failed to reset dock layout: {str(e)}")
            
    def create_layout_preset(self, name, layout):
        """Create a new layout preset
        
        Args:
            name (str): Preset name
            layout (dict): Layout configuration
        """
        # TODO: Implement layout preset creation
        pass
