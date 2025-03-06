from PySide6.QtWidgets import (QWidget, QVBoxLayout, QTableWidget,
                                    QTableWidgetItem, QHeaderView)
from PySide6.QtCore import Qt
import pandas as pd
import logging

logger = logging.getLogger(__name__)

class ResultsTableWindow(QWidget):
    """Window for displaying results in table format"""
    
    def __init__(self, data: pd.DataFrame):
        """
        Initialize table window
        
        Args:
            data: DataFrame containing results
        """
        super().__init__()
        self.data = data
        self.setup_ui()
        
    def setup_ui(self):
        """Initialize the user interface"""
        try:
            layout = QVBoxLayout()
            self.setLayout(layout)
            
            # Create table
            self.table = QTableWidget()
            layout.addWidget(self.table)
            
            # Set table data
            self.update_table()
            
            # Set table properties
            self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
            self.table.horizontalHeader().setStretchLastSection(True)
            self.table.setAlternatingRowColors(True)
            self.table.setSortingEnabled(True)
            
        except Exception as e:
            logger.error(f"Failed to setup table window: {str(e)}")
            raise
            
    def update_table(self):
        """Update table with current data"""
        try:
            # Set dimensions
            self.table.setRowCount(len(self.data))
            self.table.setColumnCount(len(self.data.columns))
            
            # Set headers
            self.table.setHorizontalHeaderLabels(self.data.columns)
            
            # Fill data
            for i, row in enumerate(self.data.itertuples()):
                for j, value in enumerate(row[1:]):  # Skip index
                    item = QTableWidgetItem(str(value))
                    if isinstance(value, (int, float)):
                        item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    self.table.setItem(i, j, item)
                    
            logger.debug("Table updated successfully")
            
        except Exception as e:
            logger.error(f"Failed to update table: {str(e)}")
            raise
            
    def sort_table(self, column: int, order=Qt.AscendingOrder):
        """
        Sort table by column
        
        Args:
            column: Column index to sort by
            order: Sort order (Qt.AscendingOrder or Qt.DescendingOrder)
        """
        try:
            self.table.sortItems(column, order)
            logger.debug(f"Table sorted by column {column}")
        except Exception as e:
            logger.error(f"Failed to sort table: {str(e)}")
            
    def resize_columns_to_contents(self):
        """Resize columns to fit contents"""
        try:
            self.table.resizeColumnsToContents()
            logger.debug("Columns resized to contents")
        except Exception as e:
            logger.error(f"Failed to resize columns: {str(e)}")
            
    def set_data(self, data: pd.DataFrame):
        """
        Update table with new data
        
        Args:
            data: New DataFrame to display
        """
        try:
            self.data = data
            self.update_table()
            self.resize_columns_to_contents()
            logger.info("Table data updated")
        except Exception as e:
            logger.error(f"Failed to set new data: {str(e)}")
            raise
