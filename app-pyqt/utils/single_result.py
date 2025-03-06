import pandas as pd
import numpy as np
from pathlib import Path
import logging
from datetime import datetime
import matplotlib.pyplot as plt
plt.switch_backend('agg')

logger = logging.getLogger(__name__)

class SingleResultExporter:
    """Handle exporting of single analysis results"""
    
    def __init__(self):
        """Initialize exporter"""
        pass

    def export_result(self, 
                     result: dict, 
                     image_path: str,
                     output_dir: str,
                     timestamp: str = None) -> Path:
        """
        Export single analysis result
        
        Args:
            result: Analysis result dictionary
            image_path: Path to analyzed image
            output_dir: Directory to save results
            timestamp: Optional timestamp string
            
        Returns:
            Path to result directory
        """
        try:
            # Create output directory
            output_path = Path(output_dir)
            if not output_path.is_absolute():
                output_path = Path.cwd() / output_path
            
            # Create timestamp and result directory
            if timestamp is None:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            image_name = Path(image_path).stem
            result_dir = output_path / f"{image_name}_{timestamp}"
            result_dir.mkdir(parents=True, exist_ok=True)
            
            # Create result DataFrame
            df = pd.DataFrame([{
                'Image': Path(image_path).name,
                'Count': result.get('count', 0),
                'Confidence': result.get('confidence', 0.0),
                'Analysis Time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }])

            # Save to Excel
            excel_path = result_dir / "analysis_result.xlsx"
            with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Result', index=False)
                
                # Add metadata sheet
                metadata = pd.Series({
                    'Image Path': str(image_path),
                    'Analysis Time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'Software Version': '1.0.0',  # Add version tracking
                    'Output Directory': str(output_path)
                })
                metadata.to_frame(name='Value').to_excel(writer, sheet_name='Metadata')

            logger.info(f"Saved result to Excel: {excel_path}")

            # Save to CSV
            csv_path = result_dir / "result.csv"
            df.to_csv(csv_path, index=False)
            logger.info(f"Saved result to CSV: {csv_path}")

            # Save JSON for programmatic access
            json_path = result_dir / "result.json"
            result_copy = result.copy()
            result_copy.update({
                'image_path': str(image_path),
                'timestamp': datetime.now().isoformat(),
                'output_directory': str(output_path)
            })
            pd.Series(result_copy).to_json(json_path)
            logger.info(f"Saved result to JSON: {json_path}")

            return result_dir

        except Exception as e:
            logger.error(f"Failed to export result: {str(e)}")
            raise

    def create_comparison_excel(self, results: list, output_path: str) -> str:
        """
        Create Excel file comparing multiple single analyses
        
        Args:
            results: List of result dictionaries
            output_path: Path to save Excel file
            
        Returns:
            Path to saved Excel file
        """
        try:
            output_path = Path(output_path)
            if not output_path.is_absolute():
                output_path = Path.cwd() / output_path
                
            # Create parent directory if needed
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Create DataFrame
            df = pd.DataFrame(results)
            
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                # Results sheet
                df.to_excel(writer, sheet_name='Results', index=False)
                
                # Statistics sheet
                stats = {
                    'Mean Count': df['count'].mean(),
                    'Count STD': df['count'].std(),
                    'Min Count': df['count'].min(),
                    'Max Count': df['count'].max(),
                    'CV (%)': df['count'].std() / df['count'].mean() * 100
                }
                pd.Series(stats).to_frame(name='Value').to_excel(
                    writer, sheet_name='Statistics'
                )

            logger.info(f"Saved comparison to: {output_path}")
            return str(output_path)

        except Exception as e:
            logger.error(f"Failed to create comparison: {str(e)}")
            raise
