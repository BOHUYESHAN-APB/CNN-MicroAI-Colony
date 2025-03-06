import pandas as pd
import numpy as np
from pathlib import Path
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
import cv2
import matplotlib.pyplot as plt
plt.switch_backend('agg')  # Use non-interactive backend

logger = logging.getLogger(__name__)

class BatchAnalyzer:
    """Batch analysis and statistics for colony detection"""
    
    def __init__(self, output_dir: str = None):
        """
        Initialize batch analyzer
        
        Args:
            output_dir: Optional default output directory
        """
        self.default_output_dir = output_dir

    def create_output_dir(self, base_dir: str = None) -> Path:
        """Create output directory with timestamp"""
        if base_dir is None:
            if self.default_output_dir is None:
                base_dir = 'results'
            else:
                base_dir = self.default_output_dir
                
        output_path = Path(base_dir)
        if not output_path.is_absolute():
            output_path = Path.cwd() / output_path
            
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        result_dir = output_path / f"batch_analysis_{timestamp}"
        result_dir.mkdir(parents=True, exist_ok=True)
        return result_dir
        
    def run_multiple_analysis(self, 
                            model,
                            image_path: str,
                            num_runs: int = 100,
                            save_all: bool = True,
                            output_dir: str = None,
                            progress_callback=None) -> pd.DataFrame:
        """
        Run multiple analyses on the same image
        
        Args:
            model: Colony detection model
            image_path: Path to image file
            num_runs: Number of analyses to run
            save_all: Whether to save all details
            output_dir: Optional custom output directory
            progress_callback: Optional callback function for progress updates
            
        Returns:
            DataFrame with analysis results
        """
        try:
            logger.info(f"Starting {num_runs} analyses on {image_path}")
            
            # Create analysis directory
            result_dir = self.create_output_dir(output_dir)
            logger.info(f"Results will be saved to: {result_dir}")
            
            # Create results list
            results = []
            
            # Load image once
            image = cv2.imread(str(image_path))
            if image is None:
                raise ValueError(f"Could not load image: {image_path}")
            
            # Run analyses
            for i in range(num_runs):
                try:
                    result = model.predict(image)
                    result['run_id'] = i + 1
                    result['timestamp'] = datetime.now().isoformat()
                    results.append(result)
                    
                    # Update progress
                    if progress_callback:
                        progress = int((i + 1) / num_runs * 100)
                        progress_callback(progress)
                    
                    if (i + 1) % 10 == 0:
                        logger.info(f"Completed {i + 1} runs")
                        
                except Exception as e:
                    logger.error(f"Error in run {i+1}: {str(e)}")
                    continue
            
            # Create DataFrame
            df = pd.DataFrame(results)
            
            # Save results
            if save_all:
                # Save detailed CSV
                csv_path = result_dir / "detailed_results.csv"
                df.to_csv(csv_path, index=False)
                logger.info(f"Saved detailed results to {csv_path}")
                
                # Save Excel with multiple sheets
                excel_path = result_dir / "analysis_results.xlsx"
                with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
                    # Raw data sheet
                    df.to_excel(writer, sheet_name='Raw Data', index=False)
                    
                    # Statistics sheet
                    stats = self.analyze_results(df)
                    stats_df = pd.DataFrame([stats])
                    stats_df.to_excel(writer, sheet_name='Statistics')
                    
                    # Summary sheet
                    summary = pd.Series({
                        'Image': Path(image_path).name,
                        'Total Runs': len(df),
                        'Mean Count': df['count'].mean(),
                        'Count STD': df['count'].std(),
                        'CV (%)': df['count'].std() / df['count'].mean() * 100,
                        'Analysis Time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'Output Directory': str(result_dir)
                    })
                    summary.to_frame().to_excel(writer, sheet_name='Summary')
                
                logger.info(f"Saved Excel report to {excel_path}")
                
                # Create basic plots
                self._create_plots(df, result_dir)
            
            return df
            
        except Exception as e:
            logger.error(f"Batch analysis failed: {str(e)}")
            raise
    
    def analyze_results(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze batch processing results
        
        Args:
            df: DataFrame with results
            
        Returns:
            Dictionary with analysis statistics
        """
        try:
            stats = {}
            
            # Colony count statistics
            count_mean = df['count'].mean()
            count_std = df['count'].std()
            stats['count_stats'] = {
                'mean': count_mean,
                'std': count_std,
                'min': df['count'].min(),
                'max': df['count'].max(),
                'median': df['count'].median(),
                'q1': df['count'].quantile(0.25),
                'q3': df['count'].quantile(0.75),
                'cv': (count_std / count_mean * 100) if count_mean > 0 else 0
            }
            
            # Confidence statistics
            stats['confidence_stats'] = {
                'mean': df['confidence'].mean(),
                'std': df['confidence'].std(),
                'min': df['confidence'].min(),
                'max': df['confidence'].max()
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Statistics calculation failed: {str(e)}")
            raise
            
    def _create_plots(self, df: pd.DataFrame, output_dir: Path):
        """Create basic visualization plots"""
        try:
            # Set style
            plt.style.use('seaborn')
            
            # Count distribution
            plt.figure(figsize=(10, 6))
            df['count'].hist(bins=30, density=True)
            plt.title('Colony Count Distribution')
            plt.xlabel('Count')
            plt.ylabel('Frequency')
            plt.savefig(output_dir / 'count_distribution.png', dpi=300, bbox_inches='tight')
            plt.close()
            
            # Run sequence
            plt.figure(figsize=(10, 6))
            plt.plot(range(1, len(df) + 1), df['count'])
            plt.title('Colony Count by Run')
            plt.xlabel('Run Number')
            plt.ylabel('Count')
            plt.savefig(output_dir / 'count_sequence.png', dpi=300, bbox_inches='tight')
            plt.close()
            
            logger.info(f"Created visualization plots in {output_dir}")
            
        except Exception as e:
            logger.error(f"Plot creation failed: {str(e)}")
            # Continue execution even if plotting fails
