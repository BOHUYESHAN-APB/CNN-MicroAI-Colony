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
from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot, QRect, QRectF
from PyQt6.QtGui import QPixmap, QPainter, QPen, QColor, QPainterPath

from ..utils.i18n import tr
from ..analysis_core import ColonyDetector
from ..utils.project_manager import get_project_name

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
    
    current_project_path: str | None = None

    def __init__(self, parent=None, project_path: Optional[str] = None):
        super().__init__(parent)
        self._detector = ColonyDetector() # Initialize detector
        self.setup_ui()
        self.current_image = None
        self.current_results = None
        self.image_cache = {} # Cache for processed images
        self.max_cache_size = 10  # Maximum number of cached images
        self.current_project_path = project_path

    def resizeEvent(self, event):
        """Handle resize events"""
        super().resizeEvent(event)
        # Clear cache and redraw current image
        self.clear_cache()
        if self.current_image:
            self.display_image(self.current_image, self.current_results)
            
    def clear_cache(self):
        """Clear image cache"""
        self.image_cache.clear()
        
    def manage_cache(self):
        """Remove oldest items if cache is too large"""
        if len(self.image_cache) > self.max_cache_size:
            # Remove oldest entries until we're back at max_cache_size
            while len(self.image_cache) > self.max_cache_size:
                oldest_key = next(iter(self.image_cache))
                del self.image_cache[oldest_key]
            logger.debug(f"Cache pruned to {len(self.image_cache)} items")

    def load_image(self, path: str):
        """Load image for analysis"""
        self.current_image = path
        self.display_image(path)
        self.current_results = None
        self.export_btn.setEnabled(False)
        self.summary.setVisible(False)

    @property
    def detector(self):
        """Get detector instance (lazy initialization)"""
        if self._detector is None:
            self._detector = ColonyDetector()
        return self._detector

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

    def retranslateUi(self):
        """Retranslate UI elements"""
        # Find and update the labels for analysis settings
        for child in self.findChildren(QLabel):
            if "Confidence" in child.text():
                child.setText(tr("analysis.settings.confidence"))
            elif "Min Size" in child.text():
                child.setText(tr("analysis.settings.min_size"))
            elif "Max Size" in child.text():
                child.setText(tr("analysis.settings.max_size"))
            elif "Device" in child.text():
                child.setText(tr("analysis.settings.device"))

        self.analyze_btn.setText(tr("analysis.start"))
        self.export_btn.setText(tr("analysis.export"))

        # Update summary if results are available
        if self.current_results:
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

    def display_image(self, path: str, results: Optional[Dict] = None):
        """Display image with optional overlay of results"""
        if not path or not os.path.exists(path):
            return
            
        # Check cache first
        cache_key = f"{path}_{hash(str(results)) if results else 'raw'}"
        if cache_key in self.image_cache:
            self.display.setPixmap(self.image_cache[cache_key])
            return
            
        # Load image
        pixmap = QPixmap(path)
        if pixmap.isNull():
            return
            
        # Scale to fit
        scaled = pixmap.scaled(
            int(self.scroll.size().width() * 0.8),  # Leave space for info panel
            self.scroll.size().height(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        
        # Create a new wider pixmap to accommodate the info panel
        info_width = 200  # Width of info panel
        final_pixmap = QPixmap(scaled.width() + info_width, scaled.height())
        final_pixmap.fill(Qt.GlobalColor.white)  # Fill with white background
        
        # Draw the original image
        painter = QPainter(final_pixmap)
        painter.drawPixmap(0, 0, scaled)
        
        # Draw results if available
        if results:
            # Draw colonies on the image part
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            for colony in results.get("colonies", []):
                x = colony["x"]
                y = colony["y"]
                r = colony["radius"]
                conf = colony["confidence"]
                
                try:
                    # Calculate scaled coordinates for circle
                    scale_x = scaled.width() / pixmap.width()
                    scale_y = scaled.height() / pixmap.height()
                    
                    # Scale coordinates
                    scaled_x = int(x * scale_x)
                    scaled_y = int(y * scale_y)
                    scaled_r = int(r * min(scale_x, scale_y))
                    
                    # Draw circle with confidence-based color
                    color = QColor(
                        int(255 * (1 - conf)),  # Red decreases with confidence
                        int(255 * conf),        # Green increases with confidence
                        0                       # No blue component
                    )
                    pen = QPen(color)
                    pen.setWidth(2)
                    painter.setPen(pen)
                    
                    # Draw circle with antialiasing
                    painter.drawEllipse(
                        scaled_x - scaled_r,
                        scaled_y - scaled_r,
                        2 * scaled_r,
                        2 * scaled_r
                    )
                    
                    # Draw confidence text
                    text = f"{conf:.2f}"
                    painter.setPen(QPen(Qt.GlobalColor.white))
                    metrics = painter.fontMetrics()
                    text_rect = metrics.boundingRect(text)
                    
                    # Create path for text background
                    text_path = QPainterPath()
                    bg_rect = QRectF(
                        scaled_x - text_rect.width()//2 - 2,
                        scaled_y - text_rect.height()//2 - 2,
                        text_rect.width() + 4,
                        text_rect.height() + 4
                    )
                    text_path.addRoundedRect(bg_rect, 2, 2)
                    
                    # Draw background with antialiasing
                    painter.fillPath(text_path, QColor(0, 0, 0, 127))
                    
                    # Draw text
                    painter.drawText(
                        scaled_x - text_rect.width()//2,
                        scaled_y + text_rect.height()//2,
                        text
                    )
                    
                except Exception as e:
                    logger.error(f"Error drawing overlay: {e}")

            # Draw info panel
            info_x = scaled.width() + 10  # Start 10 pixels from the image edge
            info_y = 20  # Start 20 pixels from top
            line_height = painter.fontMetrics().height() + 5
            
            # Draw title
            painter.setPen(QPen(Qt.GlobalColor.black))
            font = painter.font()
            font.setBold(True)
            painter.setFont(font)
            painter.drawText(info_x, info_y, tr("analysis.results.title"))
            font.setBold(False)
            painter.setFont(font)
            info_y += line_height * 2

            # Draw timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            painter.drawText(info_x, info_y, tr("analysis.results.time"))
            info_y += line_height
            painter.drawText(info_x, info_y, timestamp)
            info_y += line_height * 2

            # Draw colony count
            count = results.get("count", 0)
            painter.drawText(info_x, info_y, tr("analysis.results.colony_count"))
            info_y += line_height
            painter.drawText(info_x, info_y, str(count))
            info_y += line_height * 2

            # Draw confidence metrics
            total_conf = sum(c["confidence"] for c in results.get("colonies", []))
            avg_conf = total_conf / len(results["colonies"]) if results["colonies"] else 0
            error_rate = 1 - avg_conf

            painter.drawText(info_x, info_y, tr("analysis.results.confidence"))
            info_y += line_height
            painter.drawText(info_x, info_y, f"{avg_conf:.2f}")
            info_y += line_height * 2

            painter.drawText(info_x, info_y, tr("analysis.results.error_rate"))
            info_y += line_height
            painter.drawText(info_x, info_y, f"{error_rate:.2f}")
            info_y += line_height * 2

            # Draw density and area
            density = results.get("density", 0)
            painter.drawText(info_x, info_y, tr("analysis.results.density"))
            info_y += line_height
            painter.drawText(info_x, info_y, f"{density:.2f}")
            info_y += line_height * 2

            area = results.get("area", 0)
            painter.drawText(info_x, info_y, tr("analysis.results.area"))
            info_y += line_height
            painter.drawText(info_x, info_y, f"{area:.2f}%")
            
            painter.end()
            
        # Manage cache before adding new item
        self.manage_cache()
        
        # Cache the result and display
        self.image_cache[cache_key] = final_pixmap
        self.display.setPixmap(final_pixmap)
        
        # Log cache status
        logger.debug(f"Image cache size: {len(self.image_cache)}")
        
    @pyqtSlot()
    def start_analysis(self):
        """Start colony analysis"""
        if not self.current_image:
            return
            
        try:
            # Clear previous results and cache
            self.clear_cache()
            
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
            
            # Emit results and save
            self.analysis_finished.emit(self.current_results)
            self.save_analysis_results(self.current_image, self.current_results)

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

    def save_analysis_results(self, image_path: str, results: Dict[str, Any]):
        """Save analysis results to project directory"""
        if not self.current_project_path:
            logger.warning("Project path not set, skipping result saving.")
            return

        project_name = get_project_name(self.current_project_path)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_filename = f"{project_name}_result_{timestamp}"
        results_dir = os.path.join(self.current_project_path, "results")
        
        # Create results directory if it doesn't exist
        os.makedirs(results_dir, exist_ok=True)

        # Save result image
        image_filename = f"{base_filename}.png"
        image_filepath = os.path.join(results_dir, image_filename)
        self.display.pixmap().save(image_filepath)

        # Save CSV results
        csv_filename = f"{base_filename}.csv"
        csv_filepath = os.path.join(results_dir, csv_filename)
        ResultExporter.export_csv(csv_filepath, results)

        # Save JSON results
        json_filename = f"{base_filename}.json"
        json_filepath = os.path.join(results_dir, json_filename)
        ResultExporter.export_json(json_filepath, results)

        logger.info(f"Results saved to: {results_dir}")
        
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
        """Show status bar message"""
        if hasattr(self.parent(), "show_status_message"):
            self.parent().show_status_message(message)
