"""
Base dock widget implementation with enhanced docking capabilities
增强型停靠组件基类实现
"""
from PyQt6.QtWidgets import QDockWidget, QWidget, QVBoxLayout
from PyQt6.QtCore import Qt, QPoint, QRect, QSize
from PyQt6.QtGui import QPainter, QColor
from ..utils.i18n import translate

class BaseDockWidget(QDockWidget):
    """Base class for all dockable widgets with enhanced features"""
    
    def __init__(self, title, parent=None):
        super().__init__(translate(title), parent)
        self.setup_base_ui()
        
    def setup_base_ui(self):
        """Setup base UI configuration"""
        # Configure dock widget behavior
        self.setAllowedAreas(Qt.DockWidgetArea.AllDockWidgetAreas)
        self.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetMovable |
            QDockWidget.DockWidgetFeature.DockWidgetFloatable |
            QDockWidget.DockWidgetFeature.DockWidgetClosable
        )
        
        # Create container widget
        self.container = QWidget()
        self.layout = QVBoxLayout(self.container)
        self.layout.setContentsMargins(2, 2, 2, 2)
        self.layout.setSpacing(1)
        self.setWidget(self.container)
        
        # Set style
        self.setStyleSheet("""
            QDockWidget {
                border: 1px solid #2d2d2d;
                background: #1e1e1e;
            }
            QDockWidget::title {
                background: #2d2d2d;
                padding: 6px;
                border-bottom: 1px solid #3d3d3d;
            }
            QDockWidget::close-button, QDockWidget::float-button {
                background: #2d2d2d;
                padding: 2px;
                border: none;
            }
            QDockWidget::close-button:hover, QDockWidget::float-button:hover {
                background: #404040;
            }
            QDockWidget::close-button:pressed, QDockWidget::float-button:pressed {
                background: #505050;
            }
        """)
        
    def add_widget(self, widget, stretch=0):
        """Add a widget to the dock's layout"""
        self.layout.addWidget(widget, stretch)
        
    def set_central_widget(self, widget):
        """Set the main widget with stretch"""
        self.layout.addWidget(widget, 1)
        
    def dragEnterEvent(self, event):
        """Enhanced drag enter handling"""
        if isinstance(event.source(), BaseDockWidget):
            event.acceptProposedAction()
            self.setStyleSheet(self.styleSheet() + """
                QDockWidget {
                    border: 1px solid #4b6eaf;
                }
            """)
        else:
            super().dragEnterEvent(event)
            
    def dragLeaveEvent(self, event):
        """Reset style on drag leave"""
        self.setStyleSheet(self.styleSheet().replace("""
            QDockWidget {
                border: 1px solid #4b6eaf;
            }
        """, ""))
        super().dragLeaveEvent(event)
        
    def dropEvent(self, event):
        """Enhanced drop handling"""
        if isinstance(event.source(), BaseDockWidget):
            # Get the relative position in the widget
            pos = event.pos()
            rect = self.rect()
            
            # Determine drop area
            if pos.x() < rect.width() * 0.25:  # Left
                self.parent().splitDockWidget(self, event.source(), Qt.Orientation.Horizontal)
            elif pos.x() > rect.width() * 0.75:  # Right
                self.parent().splitDockWidget(self, event.source(), Qt.Orientation.Horizontal)
            elif pos.y() < rect.height() * 0.25:  # Top
                self.parent().splitDockWidget(self, event.source(), Qt.Orientation.Vertical)
            elif pos.y() > rect.height() * 0.75:  # Bottom
                self.parent().splitDockWidget(self, event.source(), Qt.Orientation.Vertical)
            else:  # Tab
                self.parent().tabifyDockWidget(self, event.source())
                
            event.acceptProposedAction()
        else:
            super().dropEvent(event)
            
    def paintEvent(self, event):
        """Custom paint for drop zone indicators"""
        super().paintEvent(event)
        
        if self.isActiveWindow() and not self.isFloating():
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            rect = self.rect()
            highlight = QColor(75, 110, 175, 40)  # Semi-transparent blue
            
            # Draw drop zone indicators with integer coordinates
            painter.fillRect(QRect(0, 0, int(rect.width() * 0.25), rect.height()), highlight)  # Left
            painter.fillRect(QRect(int(rect.width() * 0.75), 0, int(rect.width() * 0.25), rect.height()), highlight)  # Right
            painter.fillRect(QRect(0, 0, rect.width(), int(rect.height() * 0.25)), highlight)  # Top
            painter.fillRect(QRect(0, int(rect.height() * 0.75), rect.width(), int(rect.height() * 0.25)), highlight)  # Bottom

    def minimumSizeHint(self):
        """Provide reasonable minimum size"""
        return QSize(200, 100)
