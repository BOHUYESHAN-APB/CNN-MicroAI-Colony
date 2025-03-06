import logging
from pathlib import Path
from datetime import datetime
import pandas as pd
from typing import Dict, Any, Optional
from jinja2 import Environment, FileSystemLoader

logger = logging.getLogger(__name__)

class ReportGenerator:
    """Generate analysis reports using templates"""
    
    def __init__(self, template_dir: Optional[str] = None):
        """Initialize report generator"""
        if template_dir is None:
            template_dir = Path(__file__).parent.parent / 'templates'
        
        self.env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=True
        )
        
    def generate_single_report(self, 
                             results: Dict[str, Any],
                             image_path: str,
                             output_path: str,
                             plots_dir: Optional[str] = None) -> bool:
        """
        Generate report for single analysis
        
        Args:
            results: Analysis results dictionary
            image_path: Path to analyzed image
            output_path: Path to save report
            plots_dir: Optional directory containing plots
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Load template
            template = self.env.get_template('report_template.html')
            
            # Prepare template variables
            template_vars = {
                'datetime': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'image_name': Path(image_path).name,
                'analysis_type': 'Single Analysis',
                'analysis_time': results.get('timestamp', ''),
                'mean_count': results.get('count', 0),
                'confidence': results.get('confidence', 0.0),
                'version': '1.0.0'
            }
            
            # Add plot paths if available
            if plots_dir:
                plots_dir = Path(plots_dir)
                template_vars.update({
                    'plot_dist_path': str(plots_dir / 'count_distribution.png'),
                    'plot_seq_path': str(plots_dir / 'count_sequence.png')
                })
            
            # Render template
            html = template.render(**template_vars)
            
            # Save report
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(html, encoding='utf-8')
            
            logger.info(f"Single analysis report saved to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to generate single report: {str(e)}")
            return False
            
    def generate_batch_report(self,
                            results_df: pd.DataFrame,
                            stats: Dict[str, Any],
                            image_path: str,
                            output_path: str,
                            plots_dir: Optional[str] = None,
                            duration: Optional[str] = None) -> bool:
        """
        Generate report for batch analysis
        
        Args:
            results_df: Results DataFrame
            stats: Statistics dictionary
            image_path: Path to analyzed image
            output_path: Path to save report
            plots_dir: Optional directory containing plots
            duration: Optional analysis duration string
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Load template
            template = self.env.get_template('batch_report_template.html')
            
            # Prepare template variables
            count_stats = stats['count_stats']
            confidence_stats = stats['confidence_stats']
            
            template_vars = {
                'datetime': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'image_name': Path(image_path).name,
                'total_runs': len(results_df),
                'duration': duration or 'Not recorded',
                
                # Count statistics
                'mean_count': count_stats['mean'],
                'std_count': count_stats['std'],
                'cv': count_stats['cv'],
                'min_count': count_stats['min'],
                'max_count': count_stats['max'],
                'median_count': count_stats['median'],
                'q1_count': count_stats['q1'],
                'q3_count': count_stats['q3'],
                'iqr_count': count_stats['q3'] - count_stats['q1'],
                'skewness': results_df['count'].skew(),
                
                # Confidence statistics
                'mean_confidence': confidence_stats['mean'],
                'std_confidence': confidence_stats['std'],
                'min_confidence': confidence_stats['min'],
                'max_confidence': confidence_stats['max'],
                
                # Software version
                'version': '1.0.0'
            }
            
            # Add plot paths if available
            if plots_dir:
                plots_dir = Path(plots_dir)
                template_vars.update({
                    'plot_dist_path': str(plots_dir / 'count_distribution.png'),
                    'plot_seq_path': str(plots_dir / 'count_sequence.png'),
                    'plot_corr_path': str(plots_dir / 'correlation_matrix.png')
                })
            
            # Add summary table
            template_vars['results_table'] = results_df.head(10).to_html(
                classes='table table-striped',
                float_format=lambda x: f'{x:.3f}' if isinstance(x, float) else x
            )
            
            # Render template
            html = template.render(**template_vars)
            
            # Save report
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(html, encoding='utf-8')
            
            logger.info(f"Batch analysis report saved to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to generate batch report: {str(e)}")
            return False
