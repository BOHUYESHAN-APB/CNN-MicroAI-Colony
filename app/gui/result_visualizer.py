"""
Result Visualizer
"""
import os
import csv
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                            QLabel, QScrollArea, QFrame, QFileDialog, QMessageBox,
                            QSpinBox, QComboBox, QProgressBar)
from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QPixmap, QPainter, QPen, QColor

from ..utils.i18n import tr
from ..analysis_core import ColonyDetector

logger = logging.getLogger(__name__)

class ResultExporter:
    """Handles exporting analysis results"""
    
    @staticmethod
    def export_csv(path: str, results: Dict[str, Any]) -> bool:
        """Export results to CSV"""
        try:
            with open(path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                # Write header
                writer.writerow(['Parameter', 'Value'])
                # Write summary
                writer.writerow(['Total Colonies', results['count']])
                writer.writerow(['Colony Density', f"{results['density']:.2f}"])
                writer.writerow(['Area Coverage', f"{results['area']:.2f}"])
                writer.writerow(['Processing Time', f"{results['time']:.2f}s"])
                # Write colony details
                writer.writerow([])
                writer.writerow(['Colony Details'])
                writer.writerow(['X', 'Y', 'Radius', 'Confidence'])
                for colony in results['colonies']:
                    writer.writerow([
                        colony['x'],
                        colony['y'],
                        colony['radius'],
                        f"{colony['confidence']:.2f}"
                    ])
            return True
        except Exception as e:
            logger.error(f"CSV export failed: {e}")
            return False
            
    @staticmethod
    def export_json(path: str, results: Dict[str, Any]) -> bool:
        """Export results to JSON"""
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            logger.error(f"JSON export failed: {e}")
            return False
            
    @staticmethod
    def export_excel(path: str, results: Dict[str, Any]) -> bool:
        """Export results to Excel"""
        try:
            import pandas as pd
            
            # Create summary dataframe
            summary_data = {
                'Parameter': ['Total Colonies', 'Colony Density', 
                            'Area Coverage', 'Processing Time'],
                'Value': [
                    results['count'],
                    f"{results['density']:.2f}",
                    f"{results['area']:.2f}",
                    f"{results['time']:.2f}s"
                ]
            }
            summary_df = pd.DataFrame(summary_data)
            
            # Create colonies dataframe
            colonies_df = pd.DataFrame(results['colonies'])
            colonies_df['confidence'] = colonies_df['confidence'].map('{:.2f}'.format)
            
            # Write to Excel
            with pd.ExcelWriter(path) as writer:
                summary_df.to_excel(writer, sheet_name='Summary', index=False)
                colonies_df.to_excel(writer, sheet_name='Colony Details', index=False)
                
            return True
            
        except Exception as e:
            logger.error(f"Excel export failed: {e}")
            return False

class ResultVisualizer(QWidget):
    """Widget for displaying analysis results"""
    
    # Signals
    analysis_started = pyqtSignal()
    analysis_finished = pyqtSignal(dict)  # Emits results dictionary
    analysis_error = pyqtSignal(str)    # Emits error message
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.detector = ColonyDetector()
        self.current_image = None
        self.current_results = None
        
    def setup_ui(self):
        """Setup user interface"""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Controls
        controls = QHBoxLayout()
        
        # Analysis settings
        settings = QHBoxLayout()
        
        # Confidence threshold
        settings.addWidget(QLabel(tr("analysis.settings.confidence")))
        self.confidence = QSpinBox()
        self.confidence.setRange(1, 100)
        self.confidence.setValue(50)
        self.confidence.setSuffix("%")
        settings.addWidget(self.confidence)
        
        # Size range
        settings.addWidget(QLabel(tr("analysis.settings.min_size")))
        self.min_size = QSpinBox()
        self.min_size.setRange(1, 1000)
        self.min_size.setValue(5)
        settings.addWidget(self.min_size)
        
        settings.addWidget(QLabel(tr("analysis.settings.max_size")))
        self.max_size = QSpinBox()
        self.max_size.setRange(1, 10000)
        self.max_size.setValue(100)
        settings.addWidget(self.max_size)
        
        # GPU acceleration
        settings.addWidget(QLabel(tr("analysis.settings.device")))
        self.device = QComboBox()
        self.device.addItems(["CPU", "GPU"])
        settings.addWidget(self.device)
        
        settings.addStretch()
        controls.addLayout(settings)
        
        # Action buttons
        actions = QHBoxLayout()
        
        self.analyze_btn = QPushButton(tr("analysis.start"))
        self.analyze_btn.clicked.connect(self.start_analysis)
        actions.addWidget(self.analyze_btn)
        
        self.export_btn = QPushButton(tr("analysis.export"))
        self.export_btn.clicked.connect(self.export_results)
        self.export_btn.setEnabled(False)
        actions.addWidget(self.export_btn)
        
        controls.addLayout(actions)
        layout.addLayout(controls)
        
        # Progress bar
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        layout.addWidget(self.progress)
        
        # Results display
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        self.display = QLabel()
        self.display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.scroll.setWidget(self.display)
        
        layout.addWidget(self.scroll)
        
        # Results summary
        self.summary = QLabel()
        self.summary.setVisible(False)
        layout.addWidget(self.summary)
        
    def load_image(self, path: str):
        """Load image for analysis"""
        self.current_image = path
        self.display_image(path)
        self.current_results = None
        self.export_btn.setEnabled(False)
        self.summary.setVisible(False)
        
    def display_image(self, path: str, results: Optional[Dict] = None):
        """Display image with optional overlay of results"""
        if not path or not os.path.exists(path):
            return
            
        # Load image
        pixmap = QPixmap(path)
        if pixmap.isNull():
            return
            
        # Scale to fit
        scaled = pixmap.scaled(
            self.scroll.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        
        # Draw results if available
        if results:
            painter = QPainter(scaled)
            pen = QPen(QColor(0, 255, 0))
            pen.setWidth(2)
            painter.setPen(pen)
            
            for colony in results.get("colonies", []):
                x = colony["x"]
                y = colony["y"]
                r = colony["radius"]
                painter.drawEllipse(x-r, y-r, 2*r, 2*r)
                
            painter.end()
            
        self.display.setPixmap(scaled)
        
    @pyqtSlot()
    def start_analysis(self):
        """Start colony analysis"""
        if not self.current_image:
            return
            
        try:
            # Update UI
            self.analyze_btn.setEnabled(False)
            self.progress.setVisible(True)
            self.progress.setRange(0, 0)
            self.analysis_started.emit()
            
            # Get parameters
            params = {
                "confidence": self.confidence.value() / 100,
                "min_size": self.min_size.value(),
                "max_size": self.max_size.value(),
                "use_gpu": self.device.currentText() == "GPU"
            }
            
            # Run analysis
            self.current_results = self.detector.analyze(
                self.current_image,
                **params
            )
            
            # Update display
            self.display_image(self.current_image, self.current_results)
            
            # Update summary
            count = self.current_results.get("count", 0)
            density = self.current_results.get("density", 0)
            area = self.current_results.get("area", 0)
            time = self.current_results.get("time", 0)
            
            self.summary.setText(
                f"{tr('analysis.results.colony_count')}: {count}\n"
                f"{tr('analysis.results.density')}: {density:.2f}\n"
                f"{tr('analysis.results.area')}: {area:.2f}\n"
                f"{tr('analysis.results.processing_time')}: {time:.2f}s"
            )
            self.summary.setVisible(True)
            
            # Enable export
            self.export_btn.setEnabled(True)
            
            # Emit results
            self.analysis_finished.emit(self.current_results)
            
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            self.analysis_error.emit(str(e))
            QMessageBox.critical(
                self,
                tr("dialog.error"),
                str(e)
            )
            
        finally:
            # Reset UI
            self.analyze_btn.setEnabled(True)
            self.progress.setVisible(False)
            
    @pyqtSlot()
    def export_results(self):
        """Export analysis results"""
        if not self.current_results:
            return
            
        try:
            # Get save path
            path, filter = QFileDialog.getSaveFileName(
                self,
                tr("analysis.results.export"),
                "",
                "CSV (*.csv);;JSON (*.json);;Excel (*.xlsx)"
            )
            
            if not path:
                return
                
            # Determine format and export
            if filter == "CSV (*.csv)":
                if not path.endswith('.csv'):
                    path += '.csv'
                success = ResultExporter.export_csv(path, self.current_results)
            elif filter == "JSON (*.json)":
                if not path.endswith('.json'):
                    path += '.json'
                success = ResultExporter.export_json(path, self.current_results)
            else:  # Excel
                if not path.endswith('.xlsx'):
                    path += '.xlsx'
                success = ResultExporter.export_excel(path, self.current_results)
                
            if success:
                self.show_status_message(tr("status.export_complete"))
            else:
                raise RuntimeError(tr("error.export_failed"))
                
        except Exception as e:
            logger.error(f"Export failed: {e}")
            QMessageBox.critical(
                self,
                tr("dialog.error"),
                str(e)
            )
            
    def show_status_message(self, message: str):
        """Show status message"""
        if hasattr(self.parent(), "show_status_message"):
            self.parent().show_status_message(message)
