"""
Result visualization and interaction implementation
结果可视化与交互实现
"""
import cv2
import numpy as np
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                          QScrollArea, QTableWidget, QTableWidgetItem, 
                          QHeaderView)
from PyQt6.QtGui import QPixmap, QImage, QColor
from PyQt6.QtCore import Qt

class ResultVisualizer(QWidget):
    """Result visualization widget with interaction support"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_image = None
        self.current_detections = None
        self.setup_ui()
        
    def setup_ui(self):
        """Setup user interface"""
        layout = QHBoxLayout(self)
        
        # Left side: Image display
        self.image_scroll = QScrollArea()
        self.image_scroll.setWidgetResizable(True)
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_scroll.setWidget(self.image_label)
        
        # Right side: Statistics panel
        stats_layout = QVBoxLayout()
        
        # Statistics table
        self.stats_table = QTableWidget()
        self.stats_table.setColumnCount(2)
        self.stats_table.setHorizontalHeaderLabels(["项目", "数值"])
        header = self.stats_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        stats_layout.addWidget(self.stats_table)
        
        # Colony list
        self.colony_table = QTableWidget()
        self.colony_table.setColumnCount(4)
        self.colony_table.setHorizontalHeaderLabels(["ID", "置信度", "直径", "位置"])
        self.colony_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.colony_table.itemClicked.connect(self.on_colony_selected)
        stats_layout.addWidget(self.colony_table)
        
        # Add to main layout
        layout.addWidget(self.image_scroll, 2)
        layout.addLayout(stats_layout, 1)
        
    def display_results(self, image, detections, stats):
        """Display detection results"""
        self.current_image = image
        self.current_detections = detections
        
        # Update statistics
        self.update_statistics(stats)
        
        # Update colony list
        self.update_colony_list(detections)
        
        # Display image with annotations
        if image is not None and detections is not None:
            display_image = image.copy()
            
            # Convert to RGB if needed
            if len(display_image.shape) == 2:
                display_image = cv2.cvtColor(display_image, cv2.COLOR_GRAY2RGB)
            elif display_image.shape[2] == 3:
                display_image = cv2.cvtColor(display_image, cv2.COLOR_BGR2RGB)
                
            # Draw detections
            for i, det in enumerate(detections):
                center = det['center']
                confidence = det['confidence']
                box = det['box']
                
                # Color based on confidence
                if confidence >= 0.8:
                    color = (0, 255, 0)  # Green
                elif confidence >= 0.6:
                    color = (255, 165, 0)  # Orange
                else:
                    color = (255, 0, 0)  # Red
                
                # Draw box and ID
                cv2.rectangle(display_image, 
                            (box[0], box[1]),
                            (box[2], box[3]),
                            color, 2)
                cv2.putText(display_image,
                           f"#{i+1}",
                           (center[0] - 10, center[1] - 10),
                           cv2.FONT_HERSHEY_SIMPLEX,
                           0.5, color, 2)
                
            # Convert to Qt image
            height, width = display_image.shape[:2]
            bytes_per_line = 3 * width
            qt_image = QImage(display_image.data, width, height,
                            bytes_per_line, QImage.Format.Format_RGB888)
            
            # Display
            self.image_label.setPixmap(QPixmap.fromImage(qt_image))
            
    def update_statistics(self, stats):
        """Update statistics table"""
        if not stats:
            return
            
        self.stats_table.setRowCount(0)
        
        # Add basic statistics
        self.add_stat_row("菌落总数", f"{stats['total_count']}")
        self.add_stat_row("平均置信度", f"{stats['average_confidence']:.3f}")
        self.add_stat_row("平均直径", f"{stats['average_diameter']:.1f}像素")
        self.add_stat_row("密度", f"{stats['density']:.2f}个/mm²")
        
    def add_stat_row(self, name, value):
        """Add a row to statistics table"""
        row = self.stats_table.rowCount()
        self.stats_table.insertRow(row)
        self.stats_table.setItem(row, 0, QTableWidgetItem(name))
        self.stats_table.setItem(row, 1, QTableWidgetItem(value))
        
    def update_colony_list(self, detections):
        """Update colony list table"""
        if not detections:
            return
            
        self.colony_table.setRowCount(len(detections))
        
        for i, det in enumerate(detections):
            # ID
            self.colony_table.setItem(i, 0, QTableWidgetItem(f"#{i+1}"))
            
            # Confidence
            conf_item = QTableWidgetItem(f"{det['confidence']:.3f}")
            if det['confidence'] >= 0.8:
                conf_item.setForeground(QColor(0, 255, 0))
            elif det['confidence'] >= 0.6:
                conf_item.setForeground(QColor(255, 165, 0))
            else:
                conf_item.setForeground(QColor(255, 0, 0))
            self.colony_table.setItem(i, 1, conf_item)
            
            # Diameter
            self.colony_table.setItem(i, 2, QTableWidgetItem(f"{det['diameter']}"))
            
            # Position
            pos = det['center']
            self.colony_table.setItem(i, 3, QTableWidgetItem(f"({pos[0]}, {pos[1]})"))
            
    def on_colony_selected(self, item):
        """Handle colony selection"""
        row = item.row()
        if self.current_image is None or self.current_detections is None:
            return
            
        # Create highlighted display
        display_image = self.current_image.copy()
        if len(display_image.shape) == 2:
            display_image = cv2.cvtColor(display_image, cv2.COLOR_GRAY2RGB)
        elif display_image.shape[2] == 3:
            display_image = cv2.cvtColor(display_image, cv2.COLOR_BGR2RGB)
            
        det = self.current_detections[row]
        center = det['center']
        box = det['box']
        
        # Draw highlight
        cv2.rectangle(display_image,
                     (box[0]-2, box[1]-2),
                     (box[2]+2, box[3]+2),
                     (0, 255, 255), 3)  # Yellow highlight
                     
        # Convert to Qt image and display
        height, width = display_image.shape[:2]
        bytes_per_line = 3 * width
        qt_image = QImage(display_image.data, width, height,
                         bytes_per_line, QImage.Format.Format_RGB888)
        self.image_label.setPixmap(QPixmap.fromImage(qt_image))
