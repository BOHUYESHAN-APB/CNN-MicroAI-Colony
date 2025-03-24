"""
Slider with value implementation
带数值的滑动条实现
"""
from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QSlider, 
                            QSpinBox, QDoubleSpinBox)
from PyQt6.QtCore import Qt, pyqtSignal

class SliderWithValue(QWidget):
    """Slider with numeric input"""
    
    # Signal emitted when value changes
    valueChanged = pyqtSignal(object)  # int or float
    
    def __init__(self, minimum, maximum, decimal=False, step=1, parent=None):
        """Initialize widget
        
        Args:
            minimum: Minimum value
            maximum: Maximum value 
            decimal: Whether to use decimal values
            step: Step size
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.decimal = decimal
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        # Create slider
        self.slider = QSlider(Qt.Orientation.Horizontal)
        if decimal:
            self.slider.setRange(int(minimum * 100), int(maximum * 100))
            self.slider.setSingleStep(int(step * 100))
        else:
            self.slider.setRange(minimum, maximum)
            self.slider.setSingleStep(step)
        
        # Create spinbox
        if decimal:
            self.spinbox = QDoubleSpinBox()
            self.spinbox.setDecimals(2)
            self.spinbox.setSingleStep(step)
        else:
            self.spinbox = QSpinBox()
            self.spinbox.setSingleStep(step)
        self.spinbox.setRange(minimum, maximum)
        self.spinbox.setFixedWidth(70)
        
        # Add widgets to layout
        layout.addWidget(self.slider)
        layout.addWidget(self.spinbox)
        
        # Connect signals
        self.slider.valueChanged.connect(self._slider_changed)
        self.spinbox.valueChanged.connect(self._spinbox_changed)
        
    def _slider_changed(self, value):
        """Handle slider value change"""
        if self.decimal:
            value = value / 100
        self.spinbox.setValue(value)
        self.valueChanged.emit(value)
        
    def _spinbox_changed(self, value):
        """Handle spinbox value change"""
        if self.decimal:
            self.slider.setValue(int(value * 100))
        else:
            self.slider.setValue(value)
        self.valueChanged.emit(value)
        
    def value(self):
        """Get current value"""
        return self.spinbox.value()
        
    def setValue(self, value):
        """Set current value"""
        self.spinbox.setValue(value)
