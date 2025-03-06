import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Union

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
                           QFileDialog, QSplitter)
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
        self.details_plot_container = None
        self.comparison_plot_container = None
        self.setWindowTitle(i18n.get('results.title'))
        self.setup_ui()

    def setup_ui(self):
        """Initialize user interface"""
        layout = QVBoxLayout(self)
        
        # Create main layout components
        self._create_main_layout(layout)
        
        # Initialize plot containers
        self._init_plot_containers()
        
        # Create initial plots if in batch mode
        self._create_initial_plots()
        
        # Add export buttons 
        self._setup_buttons(layout)
        
        # Connect tab change signal
        self.tab_widget.currentChanged.connect(self._on_tab_changed)
        
        # Resize window
        self.resize(1200, 800)

    def _create_main_layout(self, layout: QVBoxLayout):
        """Create main splitter and tab widget"""
        # Create main splitter
        self.splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(self.splitter)
        
        # Left side: tab widget for data and statistics
        self.tab_widget = QTabWidget()
        self.splitter.addWidget(self.tab_widget)
        
        # Add tabs based on mode
        if len(self.results) > 1:
            self.setup_multi_image_view()
        else:
            self.setup_single_image_view()

    def setup_multi_image_view(self):
        """Setup view for multiple image results"""
        self._setup_summary_tab()
        self._setup_details_tab()

    def _setup_summary_tab(self):
        """Setup summary tab with comparison view"""
        summary_tab = QWidget()
        summary_layout = QVBoxLayout(summary_tab)
        
        # Add summary table
        self.summary_table = self._create_table()
        self.populate_summary_table()
        summary_layout.addWidget(self.summary_table)
        
        # Add comparison plots container
        self.comparison_plot_container = self._create_plot_container()
        summary_layout.addWidget(self.comparison_plot_container)
        
        # Create initial comparison plots
        try:
            figure = self.create_comparison_plots()
            if figure:
                self._add_plot_to_container(self.comparison_plot_container,
                                          figure, 'comparison')
        except Exception as e:
            self._show_plot_error(self.comparison_plot_container, e)
            
        summary_tab.setLayout(summary_layout)
        self.tab_widget.addTab(summary_tab, i18n.get('results.summary'))

    def _setup_details_tab(self):
        """Setup details tab with individual image view"""
        details_tab = QWidget()
        details_layout = QVBoxLayout(details_tab)
        
        # Image selector
        self._setup_image_selector(details_layout)
        
        # Split details area
        details_splitter = QSplitter(Qt.Horizontal)
        
        # Left side: data table
        self.details_table = self._create_table()
        details_splitter.addWidget(self.details_table)
        
        # Right side: plots container
        details_container = self._create_plot_container()
        self.details_plot_container = details_container
        details_splitter.addWidget(details_container)
        
        details_layout.addWidget(details_splitter)
        details_tab.setLayout(details_layout)
        
        self.tab_widget.addTab(details_tab, i18n.get('results.details'))
        
        # Initialize details view
        if hasattr(self, 'image_selector') and self.image_selector.count() > 0:
            self.update_details_view()

    def _setup_image_selector(self, parent_layout: QVBoxLayout):
        """Setup image selection dropdown"""
        selector_layout = QHBoxLayout()
        selector_layout.addWidget(QLabel(i18n.get('labels.select_image')))
        self.image_selector = QComboBox()
        valid_images = [path for path, result in self.results.items() 
                       if 'error' not in result]
        self.image_selector.addItems([Path(p).stem for p in valid_images])
        self.image_selector.currentIndexChanged.connect(self.update_details_view)
        selector_layout.addWidget(self.image_selector)
        selector_layout.addStretch()
        parent_layout.addLayout(selector_layout)

    def setup_single_image_view(self):
        """Setup view for single image results"""
        result = list(self.results.values())[0]
        if 'error' in result:
            self.show_error(result['error'])
            return
            
        self._setup_data_tab(result)
        self._setup_stats_tab(result)

    def _setup_data_tab(self, result: Dict[str, Any]):
        """Setup data table tab"""
        data_tab = QWidget()
        data_layout = QVBoxLayout(data_tab)
        
        if self.batch_mode:
            self._setup_run_selector(data_layout)
        
        self.table = self._create_table()
        self.populate_table()
        data_layout.addWidget(self.table)
        data_tab.setLayout(data_layout)
        
        self.tab_widget.addTab(data_tab, i18n.get('results.data_table'))

    def _setup_stats_tab(self, result: Dict[str, Any]):
        """Setup statistics tab"""
        stats_tab = QWidget()
        stats_layout = QVBoxLayout(stats_tab)
        
        if 'statistics' in result:
            self.stats_table = self._create_table()
            self.populate_stats_table()
            stats_layout.addWidget(self.stats_table)
        else:
            stats_layout.addWidget(QLabel(i18n.get('errors.no_stats')))
            
        stats_tab.setLayout(stats_layout)
        self.tab_widget.addTab(stats_tab, i18n.get('results.statistics'))

    def _setup_run_selector(self, parent_layout: QVBoxLayout):
        """Setup run number selector for batch mode"""
        selector_layout = QHBoxLayout()
        selector_layout.addWidget(QLabel(i18n.get('labels.run_number')))
        self.run_selector = QComboBox()
        self.run_selector.currentIndexChanged.connect(self.update_data_view)
        selector_layout.addWidget(self.run_selector)
        selector_layout.addStretch()
        parent_layout.addLayout(selector_layout)

    def _create_table(self) -> QTableWidget:
        """Create a table widget with standard configuration"""
        table = QTableWidget()
        table.setAlternatingRowColors(True)
        table.horizontalHeader().setStretchLastSection(True)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        return table

    def _create_plot_container(self, min_width: Optional[int] = None) -> QWidget:
        """Create a plot container widget"""
        container = QWidget()
        container.setLayout(QVBoxLayout())
        if min_width:
            container.setMinimumWidth(min_width)
        return container

    def _init_plot_containers(self):
        """Initialize plot containers"""
        self.details_plot_container = self._create_plot_container(400)
        self.splitter.addWidget(self.details_plot_container)

    def _create_initial_plots(self):
        """Create initial plots for batch mode"""
        if self.batch_mode:
            try:
                result = self._get_first_valid_result()
                if result:
                    figure = self.create_plots(result['dataframe'])
                    if figure:
                        self._add_plot_to_container(self.details_plot_container,
                                                  figure, 'details')
            except Exception as e:
                logger.error(f"Failed to create plots: {e}")
                self._show_plot_error(self.details_plot_container, e)

    def _setup_buttons(self, layout: QVBoxLayout):
        """Setup export and control buttons"""
        button_layout = QHBoxLayout()
        
        # Export options
        self.export_combo = QComboBox()
        self.export_combo.addItems(['CSV', 'Excel', 'JSON'])
        button_layout.addWidget(self.export_combo)
        
        # Export button
        export_btn = QPushButton(i18n.get('buttons.export'))
        export_btn.clicked.connect(self.export_results)
        button_layout.addWidget(export_btn)
        
        # Save plots button (if plots exist)
        if self.plot_figure or self.comparison_figure:
            save_plots_btn = QPushButton(i18n.get('buttons.save_plots'))
            save_plots_btn.clicked.connect(self.save_plots)
            button_layout.addWidget(save_plots_btn)
        
        # Close button
        close_btn = QPushButton(i18n.get('buttons.close'))
        close_btn.clicked.connect(self.close)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)

    def _get_first_valid_result(self) -> Optional[Dict[str, Any]]:
        """Get first valid result from results dictionary"""
        logger.info(f"Looking for valid result in {len(self.results)} results")
        for path, result in self.results.items():
            logger.info(f"Checking result for {path}")
            if 'error' not in result:
                logger.info(f"Found valid result for {path}")
                if 'dataframe' in result:
                    logger.info(f"DataFrame columns: {list(result['dataframe'].columns)}")
                if 'statistics' in result:
                    logger.info(f"Statistics keys: {list(result['statistics'].keys())}")
                return result
        logger.warning("No valid results found")
        return None

    def _populate_qt_table(self, table: QTableWidget, df: pd.DataFrame,
                        custom_headers: Optional[List[str]] = None):
        """Populate a QTableWidget with DataFrame data"""
        # Set dimensions
        table.setRowCount(len(df))
        table.setColumnCount(len(df.columns))
        
        # Set headers
        if custom_headers:
            headers = custom_headers
        else:
            headers = [i18n.get(f'results.{col}', col) for col in df.columns]
        table.setHorizontalHeaderLabels(headers)
        
        # Fill data
        for i, row in df.iterrows():
            for j, value in enumerate(row):
                item = QTableWidgetItem(str(value))
                item.setTextAlignment(Qt.AlignCenter)
                table.setItem(i, j, item)
                
        # Adjust column widths
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)

    def populate_table(self):
        """Populate data table with results"""
        try:
            result = self._get_first_valid_result()
            if not result:
                raise ValueError("No valid results available")
                
            df = result['dataframe']
            self._populate_qt_table(self.table, df)
                
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
                
            # Convert to DataFrame for easier handling
            df = pd.DataFrame(rows)
            headers = [
                i18n.get('results.stat_type'),
                i18n.get('results.metric'),
                i18n.get('results.value')
            ]
            self._populate_qt_table(self.stats_table, df, custom_headers=headers)
            
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
                    stats = self._get_statistics(result)
                    count_stats = self._get_count_stats(stats)
                    self._validate_count_stats(count_stats)
                    
                    # Add data
                    rows.append(self._create_summary_row(path, count_stats))
                    logger.info(f"Successfully added summary data for {path}")
                    
                except Exception as e:
                    logger.debug(f"Error processing {path}: {str(e)}")
                    continue
                
            if not rows:
                raise ValueError("No valid results to show")
                
            # Convert to DataFrame
            df = pd.DataFrame(rows)
            headers = [
                i18n.get('results.image'),
                i18n.get('results.mean'),
                i18n.get('results.std'),
                i18n.get('results.cv'),
                i18n.get('results.min'),
                i18n.get('results.max'),
                i18n.get('results.median')
            ]
            self._populate_qt_table(self.summary_table, df, custom_headers=headers)
            
        except Exception as e:
            logger.error(f"Failed to populate summary: {e}")
            self.show_error(str(e))

    def _get_statistics(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Get statistics from result"""
        stats = None
        if 'statistics' in result:
            stats = result['statistics']
            logger.info("Found statistics in result")
        elif 'dataframe' in result and 'statistics' in result['dataframe'].columns:
            stats = result['dataframe']['statistics'].iloc[0]
            logger.info("Found statistics in DataFrame")
            
        if isinstance(stats, str):
            stats = json.loads(stats)
            logger.info("Parsed statistics from JSON string")
            
        if not isinstance(stats, dict):
            raise ValueError(f"Invalid statistics format: {type(stats)}")
            
        return stats

    def _get_count_stats(self, stats: Dict[str, Any]) -> Dict[str, Any]:
        """Get count statistics from statistics dictionary"""
        if 'count_stats' not in stats:
            raise ValueError("No count_stats found")
            
        count_stats = stats['count_stats']
        if not isinstance(count_stats, dict):
            raise ValueError(f"Invalid count_stats format: {type(count_stats)}")
            
        return count_stats

    def _validate_count_stats(self, count_stats: Dict[str, float]):
        """Validate required fields in count statistics"""
        required_stats = ['mean', 'std', 'cv', 'min', 'max', 'median']
        missing_stats = [key for key in required_stats if key not in count_stats]
        if missing_stats:
            raise ValueError(f"Missing required stats: {missing_stats}")

    def _create_summary_row(self, path: str, count_stats: Dict[str, float]) -> Dict[str, Union[str, float]]:
        """Create a summary row from count statistics"""
        return {
            'image': Path(path).stem,
            'mean': float(count_stats['mean']),
            'std': float(count_stats['std']),
            'cv': float(count_stats['cv']),
            'min': float(count_stats['min']),
            'max': float(count_stats['max']),
            'median': float(count_stats['median'])
        }

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
            self._populate_qt_table(self.details_table, df)
            self._update_detail_plots(df)
            
        except Exception as e:
            logger.error(f"Failed to update details: {e}")
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

    def _cleanup_container(self, container: QWidget):
        """Clean up widgets in a container"""
        if container:
            layout = container.layout()
            if layout:
                while layout.count():
                    item = layout.takeAt(0)
                    widget = item.widget()
                    if widget:
                        widget.setParent(None)
                        widget.deleteLater()

    def cleanup_plots(self):
        """Clean up all plots"""
        try:
            # Clean up plot containers
            self._cleanup_container(self.details_plot_container)
            self._cleanup_container(self.comparison_plot_container)
            
            # Close matplotlib figures
            if self.plot_figure:
                plt.close(self.plot_figure)
                self.plot_figure = None
            if self.comparison_figure:
                plt.close(self.comparison_figure)
                self.comparison_figure = None
                
        except Exception as e:
            logger.error(f"Failed to cleanup plots: {e}")

    def _add_plot_to_container(self, container: QWidget, figure: plt.Figure, plot_type: str):
        """Add plot to container widget"""
        try:
            if not container or not figure:
                return
                
            # Ensure container has layout
            if not container.layout():
                container.setLayout(QVBoxLayout())
                
            # Create canvas and set size
            canvas = FigureCanvas(figure)
            if plot_type == 'details':
                canvas.setMinimumHeight(400)
            elif plot_type == 'comparison':
                canvas.setMinimumHeight(300)
                
            container.layout().addWidget(canvas)
            
            # Store figure reference
            if plot_type == 'details':
                self.plot_figure = figure
            else:
                self.comparison_figure = figure
                
        except Exception as e:
            logger.error(f"Failed to add plot to container: {e}")
            raise

    def _show_plot_error(self, container: QWidget, error: Exception):
        """Show error message in plot container"""
        error_label = QLabel(str(error))
        error_label.setStyleSheet("color: red;")
        if container and container.layout():
            container.layout().addWidget(error_label)

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

    def _update_detail_plots(self, df: pd.DataFrame):
        """Update detail plots with new data"""
        try:
            self._cleanup_container(self.details_plot_container)
            
            if df is not None and not df.empty:
                figure = self.create_plots(df)
                if figure:
                    self._add_plot_to_container(self.details_plot_container,
                                              figure, 'details')
            
        except Exception as e:
            logger.error(f"Failed to update detail plots: {e}")
            self._show_plot_error(self.details_plot_container, e)

    def _update_comparison_plots(self):
        """Update comparison plots"""
        try:
            self._cleanup_container(self.comparison_plot_container)
            
            figure = self.create_comparison_plots()
            if figure:
                self._add_plot_to_container(self.comparison_plot_container,
                                          figure, 'comparison')
            
        except Exception as e:
            logger.error(f"Failed to update comparison plots: {e}")
            self._show_plot_error(self.comparison_plot_container, e)

    def _on_tab_changed(self, index: int):
        """Handle tab change event"""
        try:
            # Clean up all plots
            self.cleanup_plots()
            
            # Update plots based on current tab
            if index == 0 and len(self.results) > 1:  # Summary tab
                self._update_comparison_plots()
            elif index == 1:  # Details tab
                if hasattr(self, 'image_selector') and self.image_selector.count() > 0:
                    self.update_details_view()
                    
        except Exception as e:
            logger.error(f"Failed to handle tab change: {e}")

    def closeEvent(self, event):
        """Handle dialog close event"""
        try:
            # Clean up all plots
            self.cleanup_plots()
            
            # Close all matplotlib figures
            plt.close('all')
            
        except Exception as e:
            logger.error(f"Failed to cleanup on close: {e}")
            
        super().closeEvent(event)

    def create_plots(self, df: pd.DataFrame) -> Optional[plt.Figure]:
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

    def create_comparison_plots(self) -> Optional[plt.Figure]:
        """Create comparison plots for multiple images"""
        try:
            # Collect data
            data = []
            for path, result in self.results.items():
                try:
                    stats = self._get_statistics(result)
                    count_stats = self._get_count_stats(stats)
                    required_stats = ['mean', 'median', 'std', 'cv']
                    if all(key in count_stats for key in required_stats):
                        data.append({
                            'image': Path(path).stem,
                            'mean': float(count_stats['mean']),
                            'median': float(count_stats['median']),
                            'std': float(count_stats['std']),
                            'cv': float(count_stats['cv'])
                        })
                        logger.info(f"Successfully added data for {path}")
                except Exception as e:
                    logger.debug(f"Error processing {path}: {str(e)}")
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
            ax2.set_ylabel(i18n.get('results.std'), **font_config)
            
            ax2_cv = ax2.twinx()
            ax2_cv.plot(x, df['cv'], 'o-', color='red',
                       label=i18n.get('results.cv'))
            ax2_cv.set_ylabel(i18n.get('results.cv'), **font_config)
            
            ax2.set_xticks(x)
            ax2.set_xticklabels(df['image'], rotation=45, ha='right')
            ax2.set_title(i18n.get('results.plot.std_cv_comparison'), **font_config)
            
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

    def export_results(self):
        """Export results to file"""
        try:
            export_format = self.export_combo.currentText().lower()
            
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
        if not result:
            raise ValueError("No valid result to export")
            
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
            try:
                stats = self._get_statistics(result)
                count_stats = self._get_count_stats(stats)
                summary_data.append(self._create_summary_row(path, count_stats))
            except Exception as e:
                logger.debug(f"Error processing {path}: {str(e)}")
                continue
                
        if not summary_data:
            raise ValueError("No valid results to export")
            
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
                    'statistics': self._get_statistics(result)
                }
                
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)

    def save_plots(self):
        """Save plots to image files"""
        if not self.plot_figure and not self.comparison_figure:
            QMessageBox.warning(
                self,
                i18n.get('errors.no_plots'),
                i18n.get('errors.no_plots_message')
            )
            return
            
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                i18n.get('dialogs.save_plots'),
                "",
                "PNG Files (*.png);;PDF Files (*.pdf)"
            )
            
            if not file_path:
                return
                
            figures_to_save = []
            if self.plot_figure:
                figures_to_save.append(self.plot_figure)
            if self.comparison_figure:
                figures_to_save.append(self.comparison_figure)
                
            base_path = Path(file_path)
            if len(figures_to_save) == 1:
                figures_to_save[0].savefig(file_path, dpi=300, bbox_inches='tight')
            else:
                for i, fig in enumerate(figures_to_save, 1):
                    save_path = base_path.parent / f"{base_path.stem}_{i}{base_path.suffix}"
                    fig.savefig(save_path, dpi=300, bbox_inches='tight')
                
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
