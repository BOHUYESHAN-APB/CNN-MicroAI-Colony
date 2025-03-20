"""
Result statistics dock implementation
结果统计停靠窗口实现
"""
import logging
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QToolBar,
                            QFormLayout, QLabel, QScrollArea)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QAction
from .base_dock_widget import BaseDockWidget
from .toolbar_constants import SMALL_ICON_SIZE, TOOLBAR_STYLE
from ..utils.i18n import translate

logger = logging.getLogger(__name__)

class StatsForm(QWidget):
    """Statistics form widget"""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
    def setup_ui(self):
        """Setup form layout"""
        layout = QFormLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)
        
        self.setStyleSheet("""
            QWidget {
                background: #1e1e1e;
            }
            QLabel {
                color: #e0e0e0;
                padding: 4px;
            }
            QScrollArea {
                border: none;
                background: #1e1e1e;
            }
        """)
        
        # Create stats labels
        self.colony_count = QLabel("0")
        layout.addRow(translate("菌落总数:"), self.colony_count)
        
        self.avg_size = QLabel("0.0")
        layout.addRow(translate("平均大小(像素):"), self.avg_size)
        
        self.min_size = QLabel("0.0")
        layout.addRow(translate("最小大小(像素):"), self.min_size)
        
        self.max_size = QLabel("0.0")
        layout.addRow(translate("最大大小(像素):"), self.max_size)
        
        self.avg_conf = QLabel("0.0")
        layout.addRow(translate("平均置信度:"), self.avg_conf)
        
        self.total_area = QLabel("0.0")
        layout.addRow(translate("总面积(像素²):"), self.total_area)
        
        self.density = QLabel("0.0")
        layout.addRow(translate("密度(个/cm²):"), self.density)
        
        # Size distribution
        self.dist_label = QLabel(translate("大小分布:"))
        layout.addRow(self.dist_label)
        
        # Distribution list
        self.dist_list = QLabel()
        self.dist_list.setWordWrap(True)
        self.dist_list.setStyleSheet("color: #a0a0a0; font-size: 11px;")
        layout.addRow(self.dist_list)

class ResultStatsDock(BaseDockWidget):
    """Result statistics dock widget with enhanced docking capabilities"""
    
    def __init__(self, parent=None):
        super().__init__("统计信息", parent)
        self.setup_ui()
        
    def setup_ui(self):
        """Setup user interface"""
        # Create toolbar
        toolbar = QToolBar()
        toolbar.setIconSize(SMALL_ICON_SIZE)
        toolbar.setStyleSheet(TOOLBAR_STYLE)
        
        # Add refresh action
        refresh_action = QAction(translate("刷新"), self)
        refresh_action.triggered.connect(self.refresh_stats)
        toolbar.addAction(refresh_action)
        
        self.add_widget(toolbar)
        
        # Create scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setFrameShape(scroll.Shape.NoFrame)
        
        # Create stats form
        self.stats_form = StatsForm()
        scroll.setWidget(self.stats_form)
        
        self.set_central_widget(scroll)
        
        # Enable dock features
        self.setObjectName("result_stats_dock")
        
    def display_stats(self, stats):
        """Display detection statistics"""
        try:
            if stats is None:
                return
                
            # Update basic stats
            self.stats_form.colony_count.setText(str(stats.get("count", 0)))
            self.stats_form.avg_size.setText(f"{stats.get('avg_size', 0.0):.1f}")
            self.stats_form.min_size.setText(f"{stats.get('min_size', 0.0):.1f}")
            self.stats_form.max_size.setText(f"{stats.get('max_size', 0.0):.1f}")
            self.stats_form.avg_conf.setText(f"{stats.get('avg_confidence', 0.0):.3f}")
            self.stats_form.total_area.setText(f"{stats.get('total_area', 0.0):.1f}")
            self.stats_form.density.setText(f"{stats.get('density', 0.0):.2f}")
            
            # Update size distribution
            dist = stats.get("size_distribution", [])
            if dist:
                dist_text = "\n".join([
                    f"{d['range']}: {d['count']}个"
                    for d in dist if d['count'] > 0
                ])
                self.stats_form.dist_list.setText(dist_text)
            else:
                self.stats_form.dist_list.setText(translate("暂无数据"))
            
            logger.debug("Updated statistics display")
            
        except Exception as e:
            logger.error(f"Failed to display statistics: {str(e)}")
            logger.debug(f"Stats data: {stats}", exc_info=True)
            
    def refresh_stats(self):
        """Refresh statistics display"""
        # TODO: Implement refresh logic when needed
        pass
        
    def minimumSizeHint(self):
        """Provide reasonable minimum size"""
        return QSize(250, 300)
