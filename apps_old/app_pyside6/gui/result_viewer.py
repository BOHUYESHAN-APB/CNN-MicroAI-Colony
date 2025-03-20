import logging
from pathlib import Path
from typing import Dict, Any, Optional

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.gridspec import GridSpec
import json

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTableWidget,
                            QTableWidgetItem, QLabel, QPushButton, QTabWidget,
                            QWidget, QMessageBox, QHeaderView, QComboBox,
                            QFileDialog, QSplitter, QSizePolicy)
from PySide6.QtCore import Qt

from app_pyside6.utils.i18n import i18n

logger = logging.getLogger(__name__)

# Font configuration
FONT_PATH = Path(__file__).parent.parent / 'font' / 'MiSans VF.ttf'
try:
    font_prop = fm.FontProperties(fname=str(FONT_PATH), weight='medium')
    plt.rcParams['font.family'] = ['sans-serif']
    plt.rcParams['font.sans-serif'] = ['MiSans VF'] + plt.rcParams['font.sans-serif']
    plt.rcParams['font.weight'] = 'medium'
    plt.rcParams['axes.unicode_minus'] = False
except Exception as e:
    logger.warning(f"Failed to load Chinese font: {e}")
    font_prop = None

class ResultViewer(QDialog):
    """Dialog for viewing analysis results"""
    
    def __init__(self, results: Dict[str, Any], batch_mode: bool = False, parent=None):
        super().__init__(parent)
        self.results = results
        self.batch_mode = batch_mode
        self.current_image = None
        self.plot_figure = None
        self.comparison_figure = None
        self.details_plot_widget = None
        self.setWindowTitle(i18n.get('results.title'))
        self.setup_ui()

    def setup_ui(self):
        """Initialize user interface"""
        layout = QVBoxLayout(self)
        
        # Center tab widget
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Add tabs based on mode
        if len(self.results) > 1:
            self.setup_multi_image_view()
        else:
            # For single image view, use splitter to show details and plots
            details_container = QWidget()
            details_layout = QHBoxLayout(details_container)
            
            # Create splitter for single image view
            details_splitter = QSplitter(Qt.Horizontal)
            details_layout.addWidget(details_splitter)
            
            # Add data widget to splitter
            self.setup_single_image_view(details_splitter)
            
            # Right side widget will be empty initially
            right_widget = QWidget()
            right_layout = QVBoxLayout(right_widget)
            
            # Add a button to show/hide plots
            show_plots_btn = QPushButton(i18n.get('buttons.show_plots'))
            show_plots_btn.clicked.connect(lambda: self.toggle_detail_plots(details_splitter))
            right_layout.addWidget(show_plots_btn)
            
            details_splitter.addWidget(right_widget)
            
            self.tab_widget.addTab(details_container, i18n.get('results.details'))
            
        # Add export buttons
        button_layout = QHBoxLayout()
        
        # Export options
        self.export_combo = QComboBox()
        self.export_combo.addItems(['CSV', 'Excel', 'JSON'])
        button_layout.addWidget(self.export_combo)
        
        export_btn = QPushButton(i18n.get('buttons.export'))
        export_btn.clicked.connect(self.export_results)
        button_layout.addWidget(export_btn)
        
        if self.plot_figure or self.comparison_figure:
            save_plots_btn = QPushButton(i18n.get('buttons.save_plots'))
            save_plots_btn.clicked.connect(self.save_plots)
            button_layout.addWidget(save_plots_btn)
        
        close_btn = QPushButton(i18n.get('buttons.close'))
        close_btn.clicked.connect(self.close)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        
        # Resize window
        self.resize(1200, 800)

    def setup_multi_image_view(self):
        """Setup view for multiple image results"""
        # Summary tab
        summary_tab = QWidget()
        summary_layout = QVBoxLayout(summary_tab)
        
        # Add comparison plots
        try:
            # Create an expandable widget container for comparison plots
            plot_widget = QWidget()
            plot_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            plot_layout = QVBoxLayout(plot_widget)
            
            self.comparison_figure = self.create_comparison_plots()
            comparison_canvas = FigureCanvas(self.comparison_figure)
            plot_layout.addWidget(comparison_canvas)
            summary_layout.addWidget(plot_widget, stretch=3)  # Give plot more space
            
            # Add summary table below plots
            table_widget = QWidget()
            table_widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
            table_layout = QVBoxLayout(table_widget)
            
            self.summary_table = QTableWidget()
            self.populate_summary_table()
            self.summary_table.setMaximumHeight(200)
            table_layout.addWidget(self.summary_table)
            summary_layout.addWidget(table_widget, stretch=1)  # Give table less space
        except Exception as e:
            logger.error(f"Failed to create comparison plots: {e}")
            error_label = QLabel(str(e))
            error_label.setStyleSheet("color: red;")
            summary_layout.addWidget(error_label)
            
        summary_tab.setLayout(summary_layout)
        self.tab_widget.addTab(summary_tab, i18n.get('results.summary'))
        
        # Individual results tab with splitter
        details_tab = QWidget()
        details_layout = QVBoxLayout(details_tab)
        
        # Image selector
        selector_layout = QHBoxLayout()
        selector_layout.addWidget(QLabel(i18n.get('labels.select_image')))
        self.image_selector = QComboBox()
        valid_images = [path for path, result in self.results.items() 
                       if 'error' not in result]
        self.image_selector.addItems([Path(p).stem for p in valid_images])
        self.image_selector.currentIndexChanged.connect(self.update_details_view)
        selector_layout.addWidget(self.image_selector)
        selector_layout.addStretch()
        details_layout.addLayout(selector_layout)
        
        # Split details area
        details_splitter = QSplitter(Qt.Horizontal)
        
        # Left side: data table
        self.details_table = QTableWidget()
        details_splitter.addWidget(self.details_table)
        
        # Right side: plots
        self.details_plot_widget = QWidget()
        plot_layout = QVBoxLayout(self.details_plot_widget)
        details_splitter.addWidget(self.details_plot_widget)
        
        details_layout.addWidget(details_splitter)
        details_tab.setLayout(details_layout)
        
        self.tab_widget.addTab(details_tab, i18n.get('results.details'))
        
        # Initialize details view
        if self.image_selector.count() > 0:
            self.update_details_view()

    def setup_single_image_view(self, splitter: QSplitter):
        """Setup view for single image results"""
        result = list(self.results.values())[0]
        if 'error' in result:
            self.show_error(result['error'])
            return
            
        # Create container for tables
        tables_widget = QWidget()
        tables_layout = QVBoxLayout(tables_widget)
        
        # Create tabs for data and statistics
        tables_tab = QTabWidget()
        tables_layout.addWidget(tables_tab)
        
        # Data table tab
        data_tab = QWidget()
        data_layout = QVBoxLayout(data_tab)
        
        # Add image selector if batch mode
        if self.batch_mode:
            selector_layout = QHBoxLayout()
            selector_layout.addWidget(QLabel(i18n.get('labels.run_number')))
            self.run_selector = QComboBox()
            self.run_selector.currentIndexChanged.connect(self.update_data_view)
            selector_layout.addWidget(self.run_selector)
            selector_layout.addStretch()
            data_layout.addLayout(selector_layout)
        
        # Add data table
        self.table = QTableWidget()
        self.populate_table()
        data_layout.addWidget(self.table)
        data_tab.setLayout(data_layout)
        
        tables_tab.addTab(data_tab, i18n.get('results.data_table'))
        
        # Add statistics tab
        stats_tab = QWidget()
        stats_layout = QVBoxLayout(stats_tab)
        
        if 'statistics' in result:
            self.stats_table = QTableWidget()
            self.populate_stats_table()
            stats_layout.addWidget(self.stats_table)
        else:
            stats_layout.addWidget(QLabel(i18n.get('errors.no_stats')))
            
        stats_tab.setLayout(stats_layout)
        tables_tab.addTab(stats_tab, i18n.get('results.statistics'))
        
        # Add tables widget to splitter
        splitter.addWidget(tables_widget)

    def show_error(self, message: str):
        """Show error message in dialog"""
        error_label = QLabel(message)
        error_label.setWordWrap(True)
        error_label.setStyleSheet("color: red;")
        layout = QVBoxLayout()
        layout.addWidget(error_label)
        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.tab_widget.addTab(central_widget, i18n.get('errors.error'))
            
    def _get_first_valid_result(self) -> Optional[Dict[str, Any]]:
        """Get first valid result from results dictionary"""
        logger.info(f"Looking for valid result in {len(self.results)} results")
        for path, result in self.results.items():
            logger.info(f"Checking result for {path}")
            logger.info(f"Result keys: {list(result.keys())}")
            if 'error' not in result:
                logger.info(f"Found valid result for {path}")
                if 'dataframe' in result:
                    logger.info(f"DataFrame columns: {list(result['dataframe'].columns)}")
                if 'statistics' in result:
                    logger.info(f"Statistics keys: {list(result['statistics'].keys())}")
                return result
        logger.warning("No valid results found")
        return None

    def populate_table(self):
        """Populate data table with results"""
        try:
            result = self._get_first_valid_result()
            if not result:
                raise ValueError("No valid results available")
                
            df = result['dataframe']
            
            # Set table dimensions
            self.table.setRowCount(len(df))
            self.table.setColumnCount(len(df.columns))
            
            # Set headers
            headers = [i18n.get(f'results.{col}', col) for col in df.columns]
            self.table.setHorizontalHeaderLabels(headers)
            
            # Fill table
            for i, row in df.iterrows():
                for j, value in enumerate(row):
                    item = QTableWidgetItem(str(value))
                    item.setTextAlignment(Qt.AlignCenter)
                    self.table.setItem(i, j, item)
                    
            # Adjust column widths
            self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
            
            # Setup run selector if in batch mode
            if self.batch_mode:
                self.run_selector.clear()
                self.run_selector.addItems([str(i) for i in range(1, len(df) + 1)])
                
        except Exception as e:
            logger.error(f"Failed to populate table: {e}")
            self.show_error(str(e))

    def populate_stats_table(self):
        """Populate statistics table"""
        try:
            result = self._get_first_valid_result()
            if not result or 'statistics' not in result:
                raise ValueError("No statistics available")
                
            stats = result['statistics']
            
            # Prepare data
            rows = []
            for stat_type, values in stats.items():
                for metric, value in values.items():
                    rows.append({
                        'type': stat_type,
                        'metric': metric,
                        'value': value
                    })
                    
            if not rows:
                raise ValueError("No statistics data available")
                
            # Set table dimensions
            self.stats_table.setRowCount(len(rows))
            self.stats_table.setColumnCount(3)
            
            # Set headers
            self.stats_table.setHorizontalHeaderLabels([
                i18n.get('results.stat_type'),
                i18n.get('results.metric'),
                i18n.get('results.value')
            ])
            
            # Fill table
            for i, row in enumerate(rows):
                self.stats_table.setItem(i, 0, QTableWidgetItem(str(row['type'])))
                self.stats_table.setItem(i, 1, QTableWidgetItem(str(row['metric'])))
                self.stats_table.setItem(i, 2, QTableWidgetItem(str(row['value'])))
                
            # Adjust column widths
            self.stats_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
            
        except Exception as e:
            logger.error(f"Failed to populate statistics: {e}")
            self.show_error(str(e))

    def populate_summary_table(self):
        """Populate summary table for multiple images"""
        try:
            logger.info("Populating summary table...")
            if not self.results:
                raise ValueError("No results available")

            # Prepare summary data
            rows = []
            for path, result in self.results.items():
                try:
                    # Get statistics
                    stats = None
                    if 'statistics' in result:
                        stats = result['statistics']
                        logger.info("Found statistics in result")
                    elif 'dataframe' in result and 'statistics' in result['dataframe'].columns:
                        stats = result['dataframe']['statistics'].iloc[0]
                        logger.info("Found statistics in DataFrame")
                    
                    # Parse JSON if needed
                    if isinstance(stats, str):
                        stats = json.loads(stats)
                        logger.info("Parsed statistics from JSON string")
                    
                    if not isinstance(stats, dict):
                        logger.info(f"Invalid statistics format: {type(stats)}")
                        continue
                    
                    # Get count_stats
                    if 'count_stats' not in stats:
                        logger.info("No count_stats found")
                        continue
                        
                    count_stats = stats['count_stats']
                    if not isinstance(count_stats, dict):
                        logger.info(f"Invalid count_stats format: {type(count_stats)}")
                        continue
                    
                    # Check required fields
                    required_stats = ['mean', 'std', 'cv', 'min', 'max', 'median']
                    missing_stats = [key for key in required_stats if key not in count_stats]
                    if missing_stats:
                        logger.info(f"Missing required stats: {missing_stats}")
                        continue
                    
                    # Add data
                    row_data = {
                        'image': Path(path).stem,
                        'mean': float(count_stats['mean']),
                        'std': float(count_stats['std']),
                        'cv': float(count_stats['cv']),
                        'min': float(count_stats['min']),
                        'max': float(count_stats['max']),
                        'median': float(count_stats['median'])
                    }
                    rows.append(row_data)
                    logger.info(f"Successfully added summary data for {path}")
                except Exception as e:
                    logger.debug(f"Error processing {path}: {str(e)}")
                    continue
                
            if not rows:
                raise ValueError("No valid results to show")
                
            # Set table dimensions
            self.summary_table.setRowCount(len(rows))
            self.summary_table.setColumnCount(7)
            
            # Set headers
            self.summary_table.setHorizontalHeaderLabels([
                i18n.get('results.image'),
                i18n.get('results.mean'),
                i18n.get('results.std'),
                i18n.get('results.cv'),
                i18n.get('results.min'),
                i18n.get('results.max'),
                i18n.get('results.median')
            ])
            
            # Fill table
            for i, row in enumerate(rows):
                for j, key in enumerate(['image', 'mean', 'std', 'cv', 'min', 'max', 'median']):
                    item = QTableWidgetItem(str(row[key]))
                    item.setTextAlignment(Qt.AlignCenter)
                    self.summary_table.setItem(i, j, item)
                    
            # Adjust column widths
            self.summary_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
            
        except Exception as e:
            logger.error(f"Failed to populate summary: {e}")
            self.show_error(str(e))

    def update_details_view(self):
        """Update details view when selected image changes"""
        try:
            if self.image_selector.count() == 0:
                return
                
            idx = self.image_selector.currentIndex()
            current_image = list(self.results.keys())[idx]
            result = self.results[current_image]
            
            if 'error' in result:
                raise ValueError(result['error'])
                
            df = result['dataframe']
            
            # Update table
            self.details_table.setRowCount(len(df))
            self.details_table.setColumnCount(len(df.columns))
            
            # Set headers
            headers = [i18n.get(f'results.{col}', col) for col in df.columns]
            self.details_table.setHorizontalHeaderLabels(headers)
            
            # Fill table
            for i, row in df.iterrows():
                for j, value in enumerate(row):
                    item = QTableWidgetItem(str(value))
                    item.setTextAlignment(Qt.AlignCenter)
                    self.details_table.setItem(i, j, item)
                    
            # Adjust column widths
            self.details_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
            
            # Update plots
            self._update_detail_plots(df)
            
        except Exception as e:
            logger.error(f"Failed to update details: {e}")
            self.show_error(str(e))

    def _update_detail_plots(self, df: pd.DataFrame):
        """Update plots for individual image details"""
        try:
            # Clear existing plots
            for i in reversed(range(self.details_plot_widget.layout().count())): 
                self.details_plot_widget.layout().itemAt(i).widget().setParent(None)
            
            # Create new plots
            figure = self.create_plots(df)
            canvas = FigureCanvas(figure)
            self.details_plot_widget.layout().addWidget(canvas)
            self.plot_figure = figure
            
        except Exception as e:
            logger.error(f"Failed to update detail plots: {e}")
            self.show_error(str(e))

    def update_data_view(self):
        """Update data view when selected run changes"""
        if not self.batch_mode:
            return
            
        try:
            run_idx = self.run_selector.currentIndex()
            result = self._get_first_valid_result()
            if not result:
                return
                
            df = result['dataframe']
            
            # Update values
            row = df.iloc[run_idx]
            for col_idx, value in enumerate(row):
                item = QTableWidgetItem(str(value))
                item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(0, col_idx, item)
                
        except Exception as e:
            logger.error(f"Failed to update data view: {e}")
            self.show_error(str(e))

    def create_plots(self, df: pd.DataFrame):
        """Create analysis visualizations for single image"""
        try:
            if df is None or df.empty:
                raise ValueError("No data available for plotting")
            
            # Add run_number if it doesn't exist
            if 'run_number' not in df.columns:
                df = df.copy()
                df['run_number'] = range(1, len(df) + 1)
            
            # Create figure
            fig = plt.figure(figsize=(12, 10))
            gs = GridSpec(2, 2, figure=fig)
            font_config = {'fontproperties': font_prop} if font_prop else {}
            
            # Count distribution
            ax1 = fig.add_subplot(gs[0, 0])
            ax1.hist(df['count'], bins=30, alpha=0.7, color='skyblue')
            ax1.set_title(i18n.get('results.plot.count_distribution'), **font_config)
            ax1.set_xlabel(i18n.get('results.colony_count'), **font_config)
            ax1.set_ylabel(i18n.get('results.frequency'), **font_config)
            ax1.grid(True, linestyle='--', alpha=0.3)
            
            # Count sequence
            ax2 = fig.add_subplot(gs[0, 1])
            ax2.plot(df['run_number'], df['count'],
                    marker='o', markersize=4, linestyle='-', linewidth=1,
                    color='mediumseagreen')
            ax2.set_title(i18n.get('results.plot.count_sequence'), **font_config)
            ax2.set_xlabel(i18n.get('results.run_number'), **font_config)
            ax2.set_ylabel(i18n.get('results.colony_count'), **font_config)
            ax2.grid(True, linestyle='--', alpha=0.3)
            
            # Confidence distribution
            ax3 = fig.add_subplot(gs[1, 0])
            ax3.hist(df['confidence'], bins=30, alpha=0.7, color='lightcoral')
            ax3.set_title(i18n.get('results.plot.confidence_distribution'), **font_config)
            ax3.set_xlabel(i18n.get('results.confidence'), **font_config)
            ax3.set_ylabel(i18n.get('results.frequency'), **font_config)
            ax3.grid(True, linestyle='--', alpha=0.3)
            
            # Count vs Confidence scatter plot
            ax4 = fig.add_subplot(gs[1, 1])
            ax4.scatter(df['count'], df['confidence'],
                      alpha=0.5, color='purple', s=30)
            ax4.set_title(i18n.get('results.plot.count_vs_confidence'), **font_config)
            ax4.set_xlabel(i18n.get('results.colony_count'), **font_config)
            ax4.set_ylabel(i18n.get('results.confidence'), **font_config)
            ax4.grid(True, linestyle='--', alpha=0.3)
            
            plt.tight_layout()
            return fig
            
        except Exception as e:
            logger.error(f"Failed to create plots: {e}")
            raise

    def create_comparison_plots(self):
        """Create comparison plots for multiple images"""
        try:
            logger.info("Creating comparison plots...")
            logger.info(f"Processing {len(self.results)} results")

            # Collect data
            data = []
            
            # Process results
            for path, result in self.results.items():
                logger.info(f"Checking result for {path}")
                try:
                    # Get statistics
                    stats = None
                    if 'statistics' in result:
                        stats = result['statistics']
                        logger.info("Found statistics in result")
                    elif 'dataframe' in result and 'statistics' in result['dataframe'].columns:
                        stats = result['dataframe']['statistics'].iloc[0]
                        logger.info("Found statistics in DataFrame")
                    
                    # Parse JSON if needed
                    if isinstance(stats, str):
                        stats = json.loads(stats)
                        logger.info("Parsed statistics from JSON string")
                    
                    if not isinstance(stats, dict):
                        logger.info(f"Invalid statistics format: {type(stats)}")
                        continue
                    
                    # Get count_stats
                    if 'count_stats' not in stats:
                        logger.info("No count_stats found")
                        continue
                        
                    count_stats = stats['count_stats']
                    if not isinstance(count_stats, dict):
                        logger.info(f"Invalid count_stats format: {type(count_stats)}")
                        continue
                    
                    # Check required fields
                    required_stats = ['mean', 'median', 'std', 'cv']
                    missing_stats = [key for key in required_stats if key not in count_stats]
                    if missing_stats:
                        logger.info(f"Missing required stats: {missing_stats}")
                        continue
                    
                    # Add data point
                    data.append({
                        'image': Path(path).stem,
                        'mean': float(count_stats['mean']),
                        'median': float(count_stats['median']),
                        'std': float(count_stats['std']),
                        'cv': float(count_stats['cv'])
                    })
                    logger.info(f"Successfully added data for {path}")
                    
                except Exception as e:
                    logger.error(f"Error processing {path}: {e}")
                    continue
                
            if not data:
                raise ValueError("No valid data for comparison plots")
                
            df = pd.DataFrame(data)
            
            # Create figure
            fig = plt.figure(figsize=(12, 6))
            gs = GridSpec(1, 2, figure=fig)
            font_config = {'fontproperties': font_prop} if font_prop else {}
            
            # Mean and median comparison
            ax1 = fig.add_subplot(gs[0, 0])
            x = range(len(df))
            width = 0.35
            ax1.bar([i - width/2 for i in x], df['mean'], width,
                    label=i18n.get('results.mean'), color='skyblue')
            ax1.bar([i + width/2 for i in x], df['median'], width,
                    label=i18n.get('results.median'), color='lightcoral')
            ax1.set_xticks(x)
            ax1.set_xticklabels(df['image'], rotation=45, ha='right')
            ax1.set_title(i18n.get('results.plot.mean_median_comparison'), **font_config)
            ax1.legend()
            ax1.grid(True, linestyle='--', alpha=0.3)
            
            # Standard deviation and CV comparison
            ax2 = fig.add_subplot(gs[0, 1])
            x = range(len(df))
            ax2.plot(x, df['std'], 'o-', label=i18n.get('results.std'))
            ax2_cv = ax2.twinx()
            ax2_cv.plot(x, df['cv'], 'o-', color='red',
                        label=i18n.get('results.cv'))
            
            ax2.set_xticks(x)
            ax2.set_xticklabels(df['image'], rotation=45, ha='right')
            ax2.set_title(i18n.get('results.plot.std_cv_comparison'), **font_config)
            ax2.set_ylabel(i18n.get('results.std'), **font_config)
            ax2_cv.set_ylabel(i18n.get('results.cv'), **font_config)
            
            # Add both legends
            lines1, labels1 = ax2.get_legend_handles_labels()
            lines2, labels2 = ax2_cv.get_legend_handles_labels()
            ax2_cv.legend(lines1 + lines2, labels1 + labels2, loc='upper right')
            
            ax2.grid(True, linestyle='--', alpha=0.3)
            
            plt.tight_layout()
            return fig
            
        except Exception as e:
            logger.error(f"Failed to create comparison plots: {e}")
            raise

    def toggle_detail_plots(self, splitter: QSplitter):
        """Toggle the visibility of detail plots"""
        # Get the right widget (second widget in splitter)
        right_widget = splitter.widget(1)
        if not right_widget:
            return
            
        try:
            # If plots are not shown, create and show them
            if not self.plot_figure:
                result = self._get_first_valid_result()
                self.plot_figure = self.create_plots(result['dataframe'])
                canvas = FigureCanvas(self.plot_figure)
                canvas.setMinimumWidth(400)
                
                # Create new widget for plots
                plots_widget = QWidget()
                plots_layout = QVBoxLayout(plots_widget)
                plots_layout.addWidget(canvas)
                
                # Replace the right widget with plots
                old_widget = splitter.widget(1)
                splitter.replaceWidget(1, plots_widget)
                old_widget.deleteLater()
                
            # If plots are shown, remove them
            else:
                # Create new widget with show button
                new_widget = QWidget()
                layout = QVBoxLayout(new_widget)
                show_plots_btn = QPushButton(i18n.get('buttons.show_plots'))
                show_plots_btn.clicked.connect(lambda: self.toggle_detail_plots(splitter))
                layout.addWidget(show_plots_btn)
                
                # Clean up matplotlib objects before replacing widget
                plt.close(self.plot_figure)
                self.plot_figure = None
                
                # Replace plots with button widget
                old_widget = splitter.widget(1)
                splitter.replaceWidget(1, new_widget)
                old_widget.deleteLater()
                
        except Exception as e:
            logger.error(f"Failed to toggle plots: {e}")
            self.show_error(str(e))

    def save_plots(self):
        """Save plots to image file"""
        # Get current tab
        current_tab = self.tab_widget.tabText(self.tab_widget.currentIndex())
        
        # Check if we have plots to save
        if current_tab == i18n.get('results.summary'):
            if not self.comparison_figure:
                QMessageBox.warning(
                    self,
                    i18n.get('errors.no_plots'),
                    i18n.get('errors.no_comparison_plots')
                )
                return
        else:  # Details tab
            if not self.plot_figure:
                QMessageBox.warning(
                    self,
                    i18n.get('errors.no_plots'),
                    i18n.get('errors.no_detail_plots')
                )
                return
            
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            i18n.get('dialogs.save_plots'),
            "",
            "PNG Files (*.png);;PDF Files (*.pdf)"
        )
        
        if file_path:
            try:
                # Save based on current tab
                if current_tab == i18n.get('results.summary'):
                    # Save comparison plots from summary view
                    self.comparison_figure.savefig(file_path, dpi=300, bbox_inches='tight')
                else:
                    # Save detail plots from details view
                    self.plot_figure.savefig(file_path, dpi=300, bbox_inches='tight')
                
                QMessageBox.information(
                    self,
                    i18n.get('dialogs.export_complete'),
                    i18n.get('dialogs.plots_saved')
                )
                
            except Exception as e:
                logger.error(f"Failed to save plots: {e}")
                QMessageBox.critical(
                    self,
                    i18n.get('errors.save_failed'),
                    str(e)
                )

    def closeEvent(self, event):
        """Handle window close event"""
        try:
            # Clean up matplotlib figures
            if self.plot_figure:
                plt.close(self.plot_figure)
            if self.comparison_figure:
                plt.close(self.comparison_figure)
            plt.close('all')
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
        super().closeEvent(event)

    def export_results(self):
        """Export results to file"""
        try:
            export_format = self.export_combo.currentText().lower()
            
            # Get save path
            file_filters = {
                'csv': "CSV Files (*.csv)",
                'excel': "Excel Files (*.xlsx)",
                'json': "JSON Files (*.json)"
            }
            
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                i18n.get('dialogs.save_results'),
                "",
                file_filters[export_format]
            )
            
            if not file_path:
                return
                
            # Export data
            if len(self.results) > 1:
                self._export_multi_results(file_path, export_format)
            else:
                self._export_single_result(file_path, export_format)
                    
            QMessageBox.information(
                self,
                i18n.get('dialogs.export_complete'),
                i18n.get('dialogs.export_complete_message')
            )
            
        except Exception as e:
            logger.error(f"Failed to export results: {e}")
            QMessageBox.critical(
                self,
                i18n.get('errors.export_failed'),
                str(e)
            )

    def _export_single_result(self, file_path: str, export_format: str):
        """Export results for single image"""
        result = self._get_first_valid_result()
        df = result['dataframe']
        
        if export_format == 'csv':
            df.to_csv(file_path, index=False)
        elif export_format == 'excel':
            with pd.ExcelWriter(file_path) as writer:
                df.to_excel(writer, sheet_name='Data', index=False)
                if 'statistics' in result:
                    pd.DataFrame([result['statistics']]).to_excel(
                        writer, sheet_name='Statistics', index=False
                    )
        elif export_format == 'json':
            data = {
                'data': df.to_dict('records'),
                'statistics': result.get('statistics', {})
            }
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

    def _export_multi_results(self, file_path: str, export_format: str):
        """Export results for multiple images"""
        # Prepare summary data
        summary_data = []
        for path, result in self.results.items():
            if 'error' in result or 'statistics' not in result:
                continue
                
            stats = result['statistics']['count_stats']
            summary_data.append({
                'image': Path(path).stem,
                'mean': stats['mean'],
                'std': stats['std'],
                'cv': stats['cv'],
                'min': stats['min'],
                'max': stats['max'],
                'median': stats['median']
            })
            
        summary_df = pd.DataFrame(summary_data)
        
        if export_format == 'csv':
            summary_df.to_csv(file_path, index=False)
            
            # Export individual results
            base_path = Path(file_path).with_suffix('')
            for path, result in self.results.items():
                if 'error' in result:
                    continue
                image_name = Path(path).stem
                result_path = f"{base_path}_{image_name}_details.csv"
                result['dataframe'].to_csv(result_path, index=False)
                
        elif export_format == 'excel':
            with pd.ExcelWriter(file_path) as writer:
                summary_df.to_excel(writer, sheet_name='Summary', index=False)
                
                for path, result in self.results.items():
                    if 'error' in result:
                        continue
                    sheet_name = Path(path).stem[:31]  # Excel sheet name length limit
                    result['dataframe'].to_excel(writer, sheet_name=sheet_name, index=False)
                    
        elif export_format == 'json':
            export_data = {
                'summary': summary_data,
                'details': {}
            }
            
            for path, result in self.results.items():
                if 'error' in result:
                    continue
                image_name = Path(path).stem
                export_data['details'][image_name] = {
                    'data': result['dataframe'].to_dict('records'),
                    'statistics': result['statistics']
                }
                
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)

