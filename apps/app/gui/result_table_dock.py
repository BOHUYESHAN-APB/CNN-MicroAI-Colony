"""
Result table dock implementation
结果表格停靠窗口实现
"""
import logging
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QToolBar,
                            QTableWidget, QTableWidgetItem, QHeaderView)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QAction
from .base_dock_widget import BaseDockWidget
from .toolbar_constants import SMALL_ICON_SIZE, TOOLBAR_STYLE
from ..utils.i18n import translate

logger = logging.getLogger(__name__)

class ResultTableWidget(QTableWidget):
    """Custom table widget for results"""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
    def setup_ui(self):
        """Setup table appearance"""
        self.setColumnCount(5)
        self.setHorizontalHeaderLabels([
            translate("序号"),
            translate("大小"),
            translate("位置"),
            translate("置信度"),
            translate("类型")
        ])
        
        # Configure table appearance
        self.setStyleSheet("""
            QTableWidget {
                background: #1e1e1e;
                border: none;
                gridline-color: #2d2d2d;
            }
            QTableWidget::item {
                color: #e0e0e0;
                padding: 4px;
            }
            QTableWidget::item:selected {
                background: #404040;
            }
            QHeaderView::section {
                background: #2d2d2d;
                color: #e0e0e0;
                padding: 6px;
                border: none;
                border-right: 1px solid #3d3d3d;
                border-bottom: 1px solid #3d3d3d;
            }
            QScrollBar {
                background: #2d2d2d;
                width: 14px;
                height: 14px;
            }
            QScrollBar::handle {
                background: #404040;
                border-radius: 7px;
                min-height: 20px;
            }
            QScrollBar::add-line, QScrollBar::sub-line {
                width: 0px;
                height: 0px;
            }
        """)
        
        # Configure column behavior
        header = self.horizontalHeader()
        for i in range(5):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        header.setStretchLastSection(True)

class ResultTableDock(BaseDockWidget):
    """Result table dock widget with enhanced docking capabilities"""
    
    def __init__(self, parent=None):
        super().__init__("检测列表", parent)
        self.setup_ui()
        
    def setup_ui(self):
        """Setup user interface"""
        # Create toolbar
        toolbar = QToolBar()
        toolbar.setIconSize(SMALL_ICON_SIZE)
        toolbar.setStyleSheet(TOOLBAR_STYLE)
        
        # Add export action
        export_action = QAction(translate("导出表格"), self)
        export_action.triggered.connect(self.export_table)
        toolbar.addAction(export_action)
        
        # Add clear action
        clear_action = QAction(translate("清空"), self)
        clear_action.triggered.connect(self.clear_table)
        toolbar.addAction(clear_action)
        
        self.add_widget(toolbar)
        
        # Create table widget
        self.table = ResultTableWidget()
        self.set_central_widget(self.table)
        
        # Enable dock features
        self.setObjectName("result_table_dock")
        
    def display_results(self, detections):
        """Display detection results in table"""
        try:
            # Clear existing items
            self.table.setRowCount(0)
            
            # Add detections
            for i, det in enumerate(detections):
                self.table.insertRow(i)
                
                # Index
                self.table.setItem(i, 0, QTableWidgetItem(str(i+1)))
                
                # Size (diameter)
                size = det.get("diameter", 0)
                self.table.setItem(i, 1, QTableWidgetItem(f"{size:.1f}"))
                
                # Position (center)
                center = det.get("center", (0, 0))
                pos_text = f"({center[0]:.0f}, {center[1]:.0f})"
                self.table.setItem(i, 2, QTableWidgetItem(pos_text))
                
                # Confidence
                conf = det.get("confidence", 0)
                self.table.setItem(i, 3, QTableWidgetItem(f"{conf:.3f}"))
                
                # Type (can be extended for multiple colony types)
                self.table.setItem(i, 4, QTableWidgetItem(translate("标准")))
                
            logger.debug(f"Added {len(detections)} detections to table")
            
        except Exception as e:
            logger.error(f"Failed to display results in table: {str(e)}")
            logger.debug(f"Detection data: {detections}", exc_info=True)
            
    def export_table(self):
        """Export table data to file"""
        # TODO: Implement table export functionality
        pass
        
    def clear_table(self):
        """Clear all table data"""
        self.table.setRowCount(0)
        logger.debug("Cleared result table")
        
    def minimumSizeHint(self):
        """Provide reasonable minimum size"""
        return QSize(400, 200)
        
    def clear(self):
        """Clear table data (alias for clear_table)"""
        self.clear_table()
