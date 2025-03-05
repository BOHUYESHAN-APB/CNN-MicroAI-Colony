import logging
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from typing import Optional, List, Tuple
from app.utils.i18n import i18n

# 设置中文字体支持
try:
    plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']  # Windows和Linux字体
    plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题
except Exception as e:
    print(f"Warning: Failed to set Chinese font: {e}")

logger = logging.getLogger(__name__)

class Visualizer:
    """Generate visualizations for analysis results"""
    
    def __init__(self):
        """Initialize visualizer"""
        # Use seaborn style
        sns.set_style("whitegrid")
        # Use non-interactive backend
        plt.switch_backend('agg')
        
    def plot_count_distribution(self, counts: pd.Series, 
                              output_path: Optional[str] = None) -> Optional[Tuple[plt.Figure, plt.Axes]]:
        """
        Plot colony count distribution
        
        Args:
            counts: Series of colony counts
            output_path: Optional path to save plot
            
        Returns:
            Figure and axes if not saving, None if saving
        """
        try:
            fig, ax = plt.subplots(figsize=(10, 6))
            sns.histplot(data=counts, bins=30, ax=ax)
            ax.set_title(i18n.get('results.plot.count_distribution'))
            ax.set_xlabel(i18n.get('results.colony_count'))
            ax.set_ylabel(i18n.get('results.frequency'))
            
            if output_path:
                plt.savefig(output_path, dpi=300, bbox_inches='tight')
                plt.close(fig)
                logger.info(f"Count distribution plot saved to {output_path}")
                return None
            return fig, ax
            
        except Exception as e:
            logger.error(f"Failed to plot count distribution: {str(e)}")
            return None
            
    def plot_confidence_distribution(self, confidences: pd.Series,
                                   output_path: Optional[str] = None) -> Optional[Tuple[plt.Figure, plt.Axes]]:
        """Plot confidence score distribution"""
        try:
            fig, ax = plt.subplots(figsize=(10, 6))
            sns.histplot(data=confidences, bins=30, ax=ax)
            ax.set_title(i18n.get('results.plot.confidence_distribution'))
            ax.set_xlabel(i18n.get('results.confidence'))
            ax.set_ylabel(i18n.get('results.frequency'))
            
            if output_path:
                plt.savefig(output_path, dpi=300, bbox_inches='tight')
                plt.close(fig)
                logger.info(f"Confidence distribution plot saved to {output_path}")
                return None
            return fig, ax
            
        except Exception as e:
            logger.error(f"Failed to plot confidence distribution: {str(e)}")
            return None
            
    def plot_sequence(self, counts: pd.Series,
                     output_path: Optional[str] = None) -> Optional[Tuple[plt.Figure, plt.Axes]]:
        """Plot count sequence"""
        try:
            fig, ax = plt.subplots(figsize=(12, 6))
            ax.plot(range(1, len(counts) + 1), counts, '-o', alpha=0.5)
            ax.set_title(i18n.get('results.plot.count_sequence'))
            ax.set_xlabel(i18n.get('results.run_number'))
            ax.set_ylabel(i18n.get('results.colony_count'))
            
            if output_path:
                plt.savefig(output_path, dpi=300, bbox_inches='tight')
                plt.close(fig)
                logger.info(f"Sequence plot saved to {output_path}")
                return None
            return fig, ax
            
        except Exception as e:
            logger.error(f"Failed to plot sequence: {str(e)}")
            return None
            
    def create_summary_plots(self, results_df: pd.DataFrame, 
                           output_dir: str) -> bool:
        """
        Create all summary plots
        
        Args:
            results_df: Results DataFrame
            output_dir: Directory to save plots
            
        Returns:
            True if successful, False otherwise
        """
        try:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Count distribution
            self.plot_count_distribution(
                results_df['count'],
                output_dir / 'count_distribution.png'
            )
            
            # Confidence distribution
            self.plot_confidence_distribution(
                results_df['confidence'],
                output_dir / 'confidence_distribution.png'
            )
            
            # Sequence plot
            self.plot_sequence(
                results_df['count'],
                output_dir / 'count_sequence.png'
            )
            
            # Create correlation heatmap
            plt.figure(figsize=(8, 6))
            sns.heatmap(results_df.corr(), annot=True, cmap='coolwarm')
            plt.title(i18n.get('results.plot.count_vs_confidence'))
            plt.savefig(output_dir / 'correlation_matrix.png', dpi=300, bbox_inches='tight')
            plt.close()
            
            logger.info(f"All summary plots saved to {output_dir}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create summary plots: {str(e)}")
            return False
