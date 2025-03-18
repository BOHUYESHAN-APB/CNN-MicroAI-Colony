"""
Result Visualizer Widget
结果可视化部件
"""
import os
import logging
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QTableWidget, QTableWidgetItem,
                            QHeaderView, QFrame)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont

logger = logging.getLogger(__name__)

class ResultVisualizer(QFrame):
    """Widget for displaying colony analysis results"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """Setup user interface"""
        # Set frame style
        self.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Sunken)
        self.setStyleSheet("""
            ResultVisualizer {
                background-color: #2b2b2b;
                border: 1px solid #1e1e1e;
                border-radius: 4px;
            }
            QLabel {
                color: #e0e0e0;
            }
            QTableWidget {
                background-color: #2b2b2b;
                border: 1px solid #1e1e1e;
                color: #e0e0e0;
                gridline-color: #3a3a3a;
                outline: none;
            }
            QHeaderView {
                background-color: #323232;
            }
            QHeaderView::section {
                background-color: #323232;
                color: #e0e0e0;
                padding: 6px;
                border: none;
                border-bottom: 2px solid #1e1e1e;
                font-weight: bold;
            }
            QTableWidget::item {
                padding: 6px;
                border-bottom: 1px solid #3a3a3a;
            }
            QTableWidget::item:selected {
                background-color: #3c4147;
                color: #ffffff;
            }
            QTableWidget::item:hover {
                background-color: #353b41;
            }
            QScrollBar:vertical {
                background-color: #2b2b2b;
                width: 14px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background-color: #404040;
                min-height: 30px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #4a4a4a;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setSpacing(8)
        layout.setContentsMargins(8, 8, 8, 8)
        self.setLayout(layout)
        
        # Header
        header_layout = QHBoxLayout()
        
        self.title_label = QLabel("Analysis Results")
        self.title_label.setStyleSheet("""
            QLabel {
                font-weight: bold;
                color: #e0e0e0;
                font-size: 14px;
            }
        """)
        header_layout.addWidget(self.title_label)
        
        header_layout.addStretch()
        
        # Analysis button
        self.analyze_button = QPushButton("Analyze Image")
        self.analyze_button.setEnabled(False)
        self.analyze_button.clicked.connect(self.start_analysis)  # Connect to analysis slot
        self.analyze_button.setStyleSheet("""
            QPushButton {
                background-color: #0d47a1;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 16px;
                min-width: 100px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1565c0;
            }
            QPushButton:pressed {
                background-color: #0a3880;
            }
            QPushButton:disabled {
                background-color: #424242;
                color: #828282;
            }
        """)
        header_layout.addWidget(self.analyze_button)

        # Batch analysis button
        self.batch_analyze_button = QPushButton("Batch Analyze")
        self.batch_analyze_button.setEnabled(False)
        self.batch_analyze_button.clicked.connect(self.start_batch_analysis)  # Connect batch analysis
        self.batch_analyze_button.setStyleSheet("""
            QPushButton {
                background-color: #0d47a1;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 16px;
                min-width: 120px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1565c0;
            }
            QPushButton:pressed {
                background-color: #0a3880;
            }
            QPushButton:disabled {
                background-color: #424242;
                color: #828282;
            }
        """)
        header_layout.addWidget(self.batch_analyze_button)
        
        layout.addLayout(header_layout)

        # Detailed results table
        self.detail_table_label = QLabel("Detailed Results")
        self.detail_table_label.setStyleSheet("""
            QLabel {
                font-weight: bold;
                color: #e0e0e0;
                font-size: 14px;
                margin-top: 10px;
            }
        """)
        layout.addWidget(self.detail_table_label)
        
        self.detail_table = QTableWidget()
        self.detail_table.setColumnCount(5)
        self.detail_table.setHorizontalHeaderLabels([
            "ID", "Confidence", "X", "Y", "Diameter"
        ])

        # Detail table configuration
        detail_header = self.detail_table.horizontalHeader()
        detail_header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)  # ID
        detail_header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)  # Confidence
        detail_header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch) # X
        detail_header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch) # Y
        detail_header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch) # Diameter

        self.detail_table.setColumnWidth(0, 50)   # ID
        self.detail_table.setColumnWidth(1, 100)  # Confidence
        detail_header.setMinimumSectionSize(50)

        self.detail_table.verticalHeader().setVisible(False)
        self.detail_table.setShowGrid(True)
        self.detail_table.setAlternatingRowColors(True)
        self.detail_table.setStyleSheet(self.detail_table.styleSheet() + """
            QTableWidget {
                alternate-background-color: #2f2f2f;
            }
        """)
        layout.addWidget(self.detail_table)

        # Summary table (总数表格)
        self.summary_table_label = QLabel("Summary")
        self.summary_table_label.setStyleSheet("""
            QLabel {
                font-weight: bold;
                color: #e0e0e0;
                font-size: 14px;
                margin-top: 10px;
            }
        """)
        layout.addWidget(self.summary_table_label)
        
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Type", "Count", "Percentage"])

        # Summary table configuration
        summary_header = self.table.horizontalHeader()
        summary_header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch) # Type
        summary_header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)   # Count
        summary_header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)   # Percentage
        summary_header.setMinimumSectionSize(80)
        self.table.setColumnWidth(1, 80)
        self.table.setColumnWidth(2, 100)

        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(True)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet(self.table.styleSheet() + """
            QTableWidget {
                alternate-background-color: #2f2f2f;
            }
        """)
        
        layout.addWidget(self.table)
        
        # Summary section
        summary_layout = QHBoxLayout()
        
        self.total_label = QLabel("Detected Colonies: 0")
        self.total_label.setStyleSheet("""
            QLabel {
                font-weight: bold;
                color: #e0e0e0;
            }
        """)
        summary_layout.addWidget(self.total_label)
        
        summary_layout.addStretch()
        
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("""
            QLabel {
                color: #828282;
                font-style: italic;
            }
        """)
        summary_layout.addWidget(self.status_label)
        
        layout.addLayout(summary_layout)

    def start_analysis(self):
        """Start image analysis process"""
        image_path = self.image_path
        if not image_path:
            self.status_label.setText("No image selected for analysis")
            return
        
        self.status_label.setText("Analyzing...")
        # Here you would typically call your analysis function
        # For now, we'll simulate analysis with dummy data
        dummy_results = {
            'counts': {'TypeA': 150, 'TypeB': 203, 'TypeC': 87},
            'details': [
                {'id': 1, 'confidence': 0.95, 'x': 100, 'y': 200, 'diameter': 50},
                {'id': 2, 'confidence': 0.88, 'x': 150, 'y': 250, 'diameter': 45},
                {'id': 3, 'confidence': 0.92, 'x': 200, 'y': 300, 'diameter': 52},
            ]
        }
        self.show_results(dummy_results)

    def start_batch_analysis(self):
        """Start batch image analysis process"""
        # For batch analysis, you might want to trigger a different process
        self.status_label.setText("Batch analysis started...")
        # Placeholder for batch analysis logic

    def clear_results(self):
        """Clear all results"""
        self.table.setRowCount(0)
        self.detail_table.setRowCount(0)
        self.total_label.setText("Detected Colonies: 0")
        self.status_label.setText("Ready")
        self.analyze_button.setEnabled(False)
        self.batch_analyze_button.setEnabled(False)
    
    def set_image_path(self, path: str):
        """Set current image path and enable analysis buttons"""
        if path and os.path.exists(path):
            self.image_path = path
            self.analyze_button.setEnabled(True)
            self.batch_analyze_button.setEnabled(True)  # Enable batch analysis button
            self.status_label.setText("Ready to analyze")
        else:
            self.image_path = None
            self.analyze_button.setEnabled(False)
            self.batch_analyze_button.setEnabled(False)  # Disable batch analysis button
            self.status_label.setText("No image selected")

    def show_results(self, results: dict):
        """Display analysis results in both tables"""
        self.table.setRowCount(0)  # Clear summary table
        self.detail_table.setRowCount(0) # Clear detail table
        
        if not results:
            self.status_label.setText("No results available")
            return

        # Populate detail table (详细结果表格)
        details = results.get('details', [])
        for detail in details:
            row = self.detail_table.rowCount()
            self.detail_table.insertRow(row)

            item_id = QTableWidgetItem(str(detail.get('id', '')))
            item_confidence = QTableWidgetItem(f"{detail.get('confidence', ''):.2f}")
            item_x = QTableWidgetItem(str(detail.get('x', '')))
            item_y = QTableWidgetItem(str(detail.get('y', '')))
            item_diameter = QTableWidgetItem(f"{detail.get('diameter', ''):.2f}")

            item_id.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_confidence.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_x.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_y.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_diameter.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            self.detail_table.setItem(row, 0, item_id)
            self.detail_table.setItem(row, 1, item_confidence)
            self.detail_table.setItem(row, 2, item_x)
            self.detail_table.setItem(row, 3, item_y)
            self.detail_table.setItem(row, 4, item_diameter)

        # Calculate total colonies for summary
        total = sum(results.get('counts', {}).values())
        self.total_label.setText(f"Detected Colonies: {total}")
        
        # Populate summary table (总数表格)
        counts = results.get('counts', {})
        for colony_type, count in counts.items():
            row = self.table.rowCount()
            self.table.insertRow(row)

            # Type
            type_item = QTableWidgetItem(colony_type)
            type_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, 0, type_item)

            # Count
            count_item = QTableWidgetItem(str(count))
            count_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 1, count_item)

            # Percentage
            percentage = (count / total * 100) if total > 0 else 0
            percent_item = QTableWidgetItem(f"{percentage:.1f}%")
            percent_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 2, percent_item)

        self.status_label.setText("Analysis complete")
