import logging
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional, Callable
import cv2
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from matplotlib.gridspec import GridSpec
import json

from .visualization import Visualizer
from app_pyside6.utils.path_manager import PathManager
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

class BatchAnalyzer:
    """Handle batch analysis of images"""
    
    def __init__(self, config, path_manager: PathManager):
        self.config = config
        self.path_manager = path_manager
        self.visualizer = Visualizer()
        
    def run_analysis(self, 
                    model,
                    image_paths: List[str],
                    num_runs: int,
                    progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """Run batch analysis on images"""
        try:
            # Validate number of runs
            min_runs = self.config.get('analysis.batch.min_runs', 10)
            max_runs = self.config.get('analysis.batch.max_runs', 10000)
            num_runs = max(min(num_runs, max_runs), min_runs)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            results_by_image = {}
            total_progress = len(image_paths) * num_runs
            current_progress = 0
            
            # Handle multiple images
            if len(image_paths) > 1:
                multi_image_dir = self.path_manager.get_multi_image_output_dir(timestamp)
            
            # Process each image
            for image_path in image_paths:
                image_name = Path(image_path).stem
                logger.info(f"Processing image: {image_name}")
                
                try:
                    # Load image
                    image = cv2.imread(str(image_path))
                    if image is None:
                        raise ValueError(f"Failed to load image: {image_path}")
                    
                    # Get output directory
                    image_dir = self.path_manager.get_image_output_dir(
                        image_path,
                        timestamp,
                        batch_mode=True
                    )
                    
                    # Run analysis multiple times
                    all_results = []
                    for i in range(num_runs):
                        result = model.predict(image)
                        result['run_number'] = i + 1
                        all_results.append(result)
                        
                        # Update progress
                        current_progress += 1
                        if progress_callback:
                            progress = int(100 * current_progress / total_progress)
                            progress_callback(progress)
                    
                    # Convert results to DataFrame
                    df = pd.DataFrame([
                        {
                            'run_number': r['run_number'],
                            'count': r['count'],
                            'confidence': r['confidence']
                        }
                        for r in all_results
                    ])
                    
                    # Calculate statistics
                    stats = self._calculate_statistics(df)
                    
                    # Create plots
                    if self.config.get('analysis.batch.create_plots', True):
                        plots_dir = image_dir / "plots"
                        plots_dir.mkdir(parents=True, exist_ok=True)
                        self._create_plots(df, plots_dir)
                        logger.info(f"Plots created in {plots_dir}")
                    
                    # Save results if auto-export is enabled
                    if self.path_manager.is_auto_export_enabled():
                        data_dir = image_dir / "data"
                        data_dir.mkdir(parents=True, exist_ok=True)
                        output_base = data_dir / f"{image_name}_results"
                        self._save_results(df, output_base)
                    
                    # Store results
                    results_by_image[str(image_path)] = {
                        'dataframe': df,
                        'statistics': stats,
                        'output_dir': image_dir
                    }
                    
                except Exception as e:
                    logger.error(f"Failed to process image {image_name}: {e}")
                    results_by_image[str(image_path)] = {
                        'error': str(e),
                        'output_dir': image_dir
                    }
            
            # Handle multi-image analysis
            if len(image_paths) > 1 and len(results_by_image) > 0:
                self._export_multi_results(results_by_image, multi_image_dir, timestamp)
            
            return results_by_image
            
        except Exception as e:
            logger.error(f"Batch analysis failed: {e}")
            raise
            
    def _calculate_statistics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate statistics from results"""
        try:
            count_stats = {
                'mean': float(df['count'].mean()),
                'std': float(df['count'].std()),
                'cv': float(df['count'].std() / df['count'].mean() * 100) if df['count'].mean() != 0 else 0,
                'min': float(df['count'].min()),
                'max': float(df['count'].max()),
                'median': float(df['count'].median()),
                'q1': float(df['count'].quantile(0.25)),
                'q3': float(df['count'].quantile(0.75))
            }
            
            confidence_stats = {
                'mean': float(df['confidence'].mean()),
                'std': float(df['confidence'].std()),
                'min': float(df['confidence'].min()),
                'max': float(df['confidence'].max())
            }
            
            return {
                'count_stats': count_stats,
                'confidence_stats': confidence_stats
            }
        except Exception as e:
            logger.error(f"Failed to calculate statistics: {e}")
            return {
                'count_stats': {
                    'mean': 0, 'std': 0, 'cv': 0,
                    'min': 0, 'max': 0, 'median': 0,
                    'q1': 0, 'q3': 0
                },
                'confidence_stats': {
                    'mean': 0, 'std': 0,
                    'min': 0, 'max': 0
                }
            }
            
    def _create_plots(self, df: pd.DataFrame, output_dir: Path):
        """Create analysis visualizations"""
        try:
            # Create figure
            fig = plt.figure(figsize=(12, 10))
            gs = GridSpec(2, 2, figure=fig)
            
            # Count distribution
            ax1 = fig.add_subplot(gs[0, 0])
            font_config = {'fontproperties': font_prop} if font_prop else {}
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
            fig.savefig(output_dir / 'analysis_plots.png', dpi=300, bbox_inches='tight')
            plt.close(fig)
            
        except Exception as e:
            logger.error(f"Failed to create plots: {e}")
            raise
            
    def _export_multi_results(self, results: Dict[str, Any], output_dir: Path, timestamp: str):
        """Export results for multiple images"""
        try:
            # Check if we have valid results
            valid_results = {
                path: result for path, result in results.items() 
                if 'error' not in result
            }
            
            if not valid_results:
                raise ValueError("No valid results to export")
                
            # Export to Excel
            excel_path = output_dir / f"combined_analysis_{timestamp}.xlsx"
            self._export_to_excel(excel_path, valid_results)
            
            # Export to CSV
            csv_path = output_dir / f"combined_analysis_{timestamp}.csv"
            self._export_to_csv(csv_path, valid_results)
            
            # Export to JSON
            json_path = output_dir / f"combined_analysis_{timestamp}.json"
            self._export_to_json(json_path, valid_results)
            
        except Exception as e:
            logger.error(f"Failed to export multi-image results: {e}")
            raise
            
    def _export_to_excel(self, file_path: str, results: Dict[str, Any]):
        """Export results to Excel format"""
        with pd.ExcelWriter(file_path) as writer:
            # Write summary sheet
            summary_data = []
            for path, result in results.items():
                stats = result['statistics']['count_stats']
                summary_data.append({
                    'Image': Path(path).stem,
                    'Mean Count': stats['mean'],
                    'Std Dev': stats['std'],
                    'CV (%)': stats['cv'],
                    'Min': stats['min'],
                    'Max': stats['max'],
                    'Median': stats['median']
                })
                
            if summary_data:
                summary_df = pd.DataFrame(summary_data)
                summary_df.to_excel(writer, sheet_name='Summary', index=False)
                
                # Write individual sheets
                for path, result in results.items():
                    sheet_name = Path(path).stem[:31]  # Excel sheet name length limit
                    df = result['dataframe'].copy()
                    
                    # Add statistics to the sheet
                    stats = result['statistics']
                    stats_data = []
                    
                    for stat_type, values in stats.items():
                        for metric, value in values.items():
                            stats_data.append({
                                'Statistic': f"{stat_type}_{metric}",
                                'Value': value
                            })
                            
                    stats_df = pd.DataFrame(stats_data)
                    
                    # Write main data
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
                    
                    # Write statistics below main data
                    start_row = len(df) + 3
                    stats_df.to_excel(writer, sheet_name=sheet_name, 
                                    startrow=start_row, index=False)
                
    def _export_to_csv(self, file_path: str, results: Dict[str, Any]):
        """Export results to CSV format"""
        # Create base path without extension
        base_path = Path(file_path).with_suffix('')
        
        # Export summary
        summary_data = []
        for path, result in results.items():
            stats = result['statistics']['count_stats']
            summary_data.append({
                'Image': Path(path).stem,
                'Mean Count': stats['mean'],
                'Std Dev': stats['std'],
                'CV (%)': stats['cv'],
                'Min': stats['min'],
                'Max': stats['max'],
                'Median': stats['median']
            })
            
        if summary_data:
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_csv(f"{base_path}_summary.csv", index=False)
            
            # Export individual results
            for path, result in results.items():
                image_name = Path(path).stem
                result_path = f"{base_path}_{image_name}_details.csv"
                result['dataframe'].to_csv(result_path, index=False)
                
    def _export_to_json(self, file_path: str, results: Dict[str, Any]):
        """Export results to JSON format"""
        export_data = {
            'summary': [],
            'details': {}
        }
        
        # Add summary data
        for path, result in results.items():
            image_name = Path(path).stem
            stats = result['statistics']['count_stats']
            export_data['summary'].append({
                'image': image_name,
                'statistics': stats
            })
            
            # Add detailed results
            export_data['details'][image_name] = {
                'data': result['dataframe'].to_dict('records'),
                'statistics': result['statistics']
            }
            
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
            
    def _save_results(self, df: pd.DataFrame, base_path: Path):
        """Save analysis results in multiple formats"""
        try:
            formats = self.path_manager.get_default_export_formats()
            
            for fmt in formats:
                if fmt == 'csv':
                    df.to_csv(f"{base_path}.csv", index=False)
                elif fmt == 'excel':
                    df.to_excel(f"{base_path}.xlsx", index=False)
                elif fmt == 'json':
                    df_dict = df.to_dict('records')
                    with open(f"{base_path}.json", 'w', encoding='utf-8') as f:
                        json.dump(df_dict, f, indent=2, ensure_ascii=False)
                        
            # Save statistics
            stats = self._calculate_statistics(df)
            with open(f"{base_path}_stats.json", 'w', encoding='utf-8') as f:
                json.dump(stats, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"Failed to save results: {e}")
            raise
