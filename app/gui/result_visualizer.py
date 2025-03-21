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

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QScrollArea, QFrame, QFileDialog, QMessageBox,
    QSpinBox, QComboBox, QProgressBar, QDoubleSpinBox,
    QGroupBox, QGridLayout
)
from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot, QRect, QRectF
from PyQt6.QtGui import QPixmap, QPainter, QPen, QColor, QPainterPath, QImage

from ..utils.i18n import tr
from ..analysis_core import ColonyDetector
from ..utils.project_manager import get_project_name
from ..utils.config import ConfigManager

logger = logging.getLogger(__name__)

class ResultExporter:
    """Handles exporting analysis results"""
    
    @staticmethod
    def export_csv(path: str, results: Dict[str, Any]) -> bool:
        """Export results to CSV"""
        try:
            with open(path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['Parameter', 'Value'])
                writer.writerow(['Total Colonies', results.get('count', 0)])
                writer.writerow(['Colony Density', f"{results.get('density', 0):.2f}"])
                writer.writerow(['Area Coverage', f"{results.get('area', 0):.2f}"])
                writer.writerow(['Processing Time', f"{results.get('time', 0):.2f}s"])
                writer.writerow([])
                writer.writerow(['Colony Details'])
                writer.writerow(['X', 'Y', 'Radius', 'Confidence'])
                for colony in results.get('colonies', []):
                    writer.writerow([
                        colony.get('x', 0),
                        colony.get('y', 0),
                        colony.get('radius', 0),
                        f"{colony.get('confidence', 0):.2f}"
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
            
            summary_data = {
                'Parameter': [
                    'Total Colonies', 'Colony Density',
                    'Area Coverage', 'Processing Time'
                ],
                'Value': [
                    results.get('count', 0),
                    f"{results.get('density', 0):.2f}",
                    f"{results.get('area', 0):.2f}",
                    f"{results.get('time', 0):.2f}s"
                ]
            }
            summary_df = pd.DataFrame(summary_data)
            
            colonies_df = pd.DataFrame(results.get('colonies', []))
            if not colonies_df.empty:
                colonies_df['confidence'] = colonies_df['confidence'].map('{:.2f}'.format)
            
            with pd.ExcelWriter(path) as writer:
                summary_df.to_excel(writer, sheet_name='Summary', index=False)
                colonies_df.to_excel(writer, sheet_name='Colony Details', index=False)
                
            return True
        except Exception as e:
            logger.error(f"Excel export failed: {e}")
            return False

class ResultVisualizer(QWidget):
    """Widget for displaying analysis results"""

    def retranslateUi(self):
        """Retranslate UI elements"""
        self.analyze_btn.setText(tr("analysis.start"))
        self.export_btn.setText(tr("analysis.export"))
        self.auto_opt_btn.setText(tr("analysis.auto_optimize"))
        params_group = self.findChild(QGroupBox, "params_group") # added name in setup_ui
        if params_group:
            params_group.setTitle(tr("analysis.params.title"))
        nms_label = self.findChild(QLabel, "nms_label")
        if nms_label:
            nms_label.setText(tr("settings.nms_threshold"))
        score_label = self.findChild(QLabel, "score_label")
        if score_label:
            score_label.setText(tr("settings.score_threshold"))
        min_size_label = self.findChild(QLabel, "min_size_label")
        if min_size_label:
            min_size_label.setText(tr("settings.min_size"))
        max_size_label = self.findChild(QLabel, "max_size_label")
        if max_size_label:
            max_size_label.setText(tr("settings.max_size"))
        petri_size_label = self.findChild(QLabel, "petri_size_label")
        if petri_size_label:
            petri_size_label.setText(tr("settings.petri_size"))
        device_label = self.findChild(QLabel, "device_label")
        if device_label:
            device_label.setText(tr("analysis.settings.device"))

    # Signals
    analysis_started = pyqtSignal()
    analysis_finished = pyqtSignal(dict)  # Emits results dictionary
    analysis_error = pyqtSignal(str)      # Emits error message
    
    current_project_path: str | None = None
    max_cache_size: int = 10
    current_image: str | None = None
    analysis_thread: Optional[Any] = None
    analysis_results: Optional[Dict[str, Any]] = None
    image_cache: Dict[str, QPixmap] = {}
    _detector: Optional[ColonyDetector] = None
    _opt_cache: Dict[str, Dict[str, float]] = {}
    config: Optional[ConfigManager] = None
    
    def __init__(self, parent=None, project_path: Optional[str] = None):
        super().__init__(parent)
        self.config = None
        self.current_project_path = project_path
        self.image_path = None
        self.analysis_thread = None
        self.analysis_results = None
        self._detector = None
        self.image_cache = {}
        self._opt_cache = {}
        self.current_image = None
        self.current_results = None
        self.max_cache_size = 10
        self.setup_ui()
        self.load_settings()

    def setup_ui(self):
        """Initialize the UI"""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        controls = QHBoxLayout()
        layout.addLayout(controls)
        
        # Create buttons with translations
        self.analyze_btn = QPushButton(tr("analysis.start"))
        self.export_btn = QPushButton(tr("analysis.export"))
        self.auto_opt_btn = QPushButton(tr("analysis.auto_optimize"))
        
        controls.addWidget(self.analyze_btn)
        controls.addWidget(self.export_btn)
        controls.addWidget(self.auto_opt_btn)
        
        params = QHBoxLayout()
        layout.addLayout(params)
        
        # 参数设置区域
        params_group = QGroupBox(tr("analysis.params.title"))
        params_layout = QGridLayout()
        params_group.setLayout(params_layout)
        layout.addWidget(params_group)
        
        current_row = 0
        
        # NMS threshold
        self.nms_spin = QDoubleSpinBox()
        self.nms_spin.setRange(0.1, 1.0)
        self.nms_spin.setSingleStep(0.01)
        self.nms_spin.setValue(0.45)
        params_layout.addWidget(QLabel(tr("settings.nms_threshold")), current_row, 0)
        params_layout.addWidget(self.nms_spin, current_row, 1)
        
        # Confidence threshold
        self.score_spin = QDoubleSpinBox()
        self.score_spin.setRange(0.1, 1.0)
        self.score_spin.setSingleStep(0.01)
        self.score_spin.setValue(0.25)
        params_layout.addWidget(QLabel(tr("settings.score_threshold")), current_row, 2)
        params_layout.addWidget(self.score_spin, current_row, 3)
        current_row += 1
        
        # Min/Max size
        self.min_size_spin = QSpinBox()
        self.min_size_spin.setRange(1, 50)
        self.min_size_spin.setValue(5)
        params_layout.addWidget(QLabel(tr("settings.min_size")), current_row, 0)
        params_layout.addWidget(self.min_size_spin, current_row, 1)
        
        self.max_size_spin = QSpinBox()
        self.max_size_spin.setRange(10, 200)
        self.max_size_spin.setValue(100)
        params_layout.addWidget(QLabel(tr("settings.max_size")), current_row, 2)
        params_layout.addWidget(self.max_size_spin, current_row, 3)
        current_row += 1
        
        # Petri dish size and device selection
        self.petri_size_combo = QComboBox()
        self.petri_size_combo.addItems(['60mm', '90mm'])
        params_layout.addWidget(QLabel(tr("settings.petri_size")), current_row, 0)
        params_layout.addWidget(self.petri_size_combo, current_row, 1)
        
        self.device = QComboBox()
        self.device.addItems(['cpu', 'cuda'])
        params_layout.addWidget(QLabel(tr("analysis.settings.device")), current_row, 2)
        params_layout.addWidget(self.device, current_row, 3)
        
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        layout.addWidget(self.progress)
        
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        layout.addWidget(self.scroll)
        
        self.display = QLabel()
        self.display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.scroll.setWidget(self.display)
        
        self.summary = QLabel()
        self.summary.setVisible(False)
        layout.addWidget(self.summary)
        
        self.analyze_btn.clicked.connect(self.start_analysis)
        self.export_btn.clicked.connect(self.export_results)
        self.auto_opt_btn.clicked.connect(self.auto_optimize_params)
        self.nms_spin.valueChanged.connect(self.on_params_changed)
        self.score_spin.valueChanged.connect(self.on_params_changed)
        
        self.export_btn.setEnabled(False)

    def load_settings(self):
        """Load settings from config"""
        if self.config:
            self.nms_spin.setValue(self.config.get('nms_threshold', 0.45))
            self.score_spin.setValue(self.config.get('confidence_threshold', 0.25))
            self.device.setCurrentText(self.config.get('device', 'cpu'))

    def get_analysis_params(self) -> Dict[str, Any]:
        """Get current analysis parameters"""
        return {
            'nms_threshold': self.nms_spin.value(),
            'confidence': self.score_spin.value(),  # Changed from confidence_threshold
            'min_size': self.min_size_spin.value(),
            'max_size': self.max_size_spin.value(),
            'petri_size': int(self.petri_size_combo.currentText().replace('mm', '')),  # Convert '90mm' to 90
            'use_gpu': self.device.currentText() == 'cuda',
            'device': self.device.currentText()
        }

    def set_config(self, config: ConfigManager):
        """Set configuration"""
        self.config = config
        self._detector = ColonyDetector(config=config)
        self.load_settings()

    def load_image(self, path: str):
        """Load image for analysis"""
        if not path or not os.path.exists(path):
            logger.warning(f"Invalid image path: {path}")
            return

        self.current_image = path
        self.current_results = None
        self.export_btn.setEnabled(False)
        self.summary.setVisible(False)
        
        self.display_image(path)
        
        if hasattr(self.parent(), "setWindowTitle"):
            filename = os.path.basename(path)
            self.parent().setWindowTitle(f"{tr('window.title')} - {filename}")

    def _update_summary_text(self, results: Dict[str, Any]):
        """Update summary text with results"""
        colonies = results.get('colonies', [])
        total_conf = sum(colony['confidence'] for colony in colonies)
        avg_conf = total_conf / len(colonies) if colonies else 0
        
        # Make sure we have these translations in zh_CN.json:
        # analysis.results.summary = "菌落数量: {count} 菌落密度: {density} 覆盖面积: {area} 平均置信度: {confidence:.2f}"
        
        self.summary.setText(
            tr("analysis.results.summary").format(
                count=results.get('count', 0),
                density=results.get('density', 0),
                area=results.get('area', 0),
                confidence=avg_conf
            )
        )
        self.summary.setVisible(True)

    def _save_result_image(self, results_dir: str, base_filename: str):
        """Save result image with overlays"""
        if not self.current_image or not self.current_results:
            return

        try:
            import cv2
            import numpy as np
            
            # 读取原始图像
            img_array = np.fromfile(self.current_image, np.uint8)
            img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
            if img is None:
                raise RuntimeError("Failed to load image")

            # 左侧是标注后的图像
            height, width = img.shape[:2]
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = min(width, height) / 2000
            thickness = max(1, int(font_scale * 2))
            
            # 添加标注信息
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            filename = os.path.basename(self.current_image)
            
            # 添加标注
            colonies = self.current_results.get("colonies", [])
            for i, colony in enumerate(colonies, 1):
                x = int(colony.get("x", 0))
                y = int(colony.get("y", 0))
                r = int(colony.get("radius", 0))
                conf = colony.get("confidence", 0)
                
                # 根据置信度设置颜色
                color = (
                    0,  # B
                    int(255 * conf),  # G
                    int(255 * (1 - conf))  # R
                )
                
                # 画圆和编号
                cv2.circle(img, (x, y), r, color, thickness)
                cv2.putText(img, str(i), (x-r//2, y), font, font_scale * 0.8, color, thickness)

            # 添加文件信息
            cv2.putText(img, f"文件: {filename}", (10, 30), font, font_scale, (0, 0, 0), thickness + 1)
            cv2.putText(img, f"分析时间: {timestamp}", (10, 60), font, font_scale, (0, 0, 0), thickness + 1)
            cv2.putText(img, f"文件: {filename}", (10, 30), font, font_scale, (255, 255, 255), thickness)
            cv2.putText(img, f"分析时间: {timestamp}", (10, 60), font, font_scale, (255, 255, 255), thickness)
            
            # 添加分析结果信息
            y_pos = 100
            results_text = [
                f"菌落数量: {len(colonies)}",
                f"置信度阈值: {self.score_spin.value():.2f}",
                f"培养皿大小: {self.petri_size_combo.currentText()}",
                f"菌落密度: {self.current_results.get('density', 0):.2f}/mm²",
                f"覆盖面积: {self.current_results.get('area', 0):.2%}"
            ]
            
            for text in results_text:
                text_pos = (10, y_pos)  # 创建元组
                cv2.putText(img, text, text_pos, font, font_scale, (0, 0, 0), thickness + 1)
                cv2.putText(img, text, text_pos, font, font_scale, (255, 255, 255), thickness)
                y_pos += int(30 * font_scale)

            # 保存结果图像
            output_path = os.path.join(results_dir, f"{base_filename}.png")
            cv2.imencode('.png', img)[1].tofile(output_path)
            
        except Exception as e:
            logger.error(f"Error saving result image: {e}")
            self.show_status_message(tr("error.save_image"))

    def _save_csv_results(self, results_dir: str, base_filename: str, results: Dict[str, Any]):
        """Save results as CSV"""
        csv_path = os.path.join(results_dir, f"{base_filename}.csv")
        ResultExporter.export_csv(csv_path, results)

    def _save_json_results(self, results_dir: str, base_filename: str, results: Dict[str, Any]):
        """Save results as JSON"""
        json_path = os.path.join(results_dir, f"{base_filename}.json")
        ResultExporter.export_json(json_path, results)

    def show_status_message(self, message: str):
        """Show status bar message"""
        if hasattr(self.parent(), "show_status_message"):
            self.parent().show_status_message(message)

    @pyqtSlot()
    def start_analysis(self):
        """Start colony analysis and return the results"""
        if not self.current_image:
            return None
            
        try:
            self.clear_cache()
            self.analyze_btn.setEnabled(False)
            self.progress.setVisible(True)
            self.progress.setRange(0, 0)
            self.analysis_started.emit()
            
            params = self.get_analysis_params()
            # Use correct params from get_analysis_params
            self.current_results = self._detector.analyze_image(  # Changed from analyze to analyze_image
                self.current_image,
                **params  # Pass all parameters directly
            )
            
            self.display_image(self.current_image, self.current_results)
            self._update_summary_text(self.current_results)
            
            self.export_btn.setEnabled(True)
            self.analysis_finished.emit(self.current_results)
            self.save_analysis_results(self.current_image, self.current_results)
            
            return self.current_results

        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            self.analysis_error.emit(str(e))
            QMessageBox.critical(
                self,
                tr("dialog.error"),
                str(e)
            )
            return None
            
        finally:
            self.analyze_btn.setEnabled(True)
            self.progress.setVisible(False)

    def clear_cache(self):
        """Clear image cache"""
        self.image_cache.clear()
        self._opt_cache.clear()

    def auto_optimize_params(self):
        """Auto-optimize parameters based on image characteristics"""
        if not self.current_image:
            return

        try:
            import cv2
            import numpy as np
            
            with open(self.current_image, 'rb') as f:
                img_array = np.frombuffer(f.read(), np.uint8)
                img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
                
            if img is None:
                raise RuntimeError(tr("error.load_image"))
                
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            thresh = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY_INV, 21, 5
            )
            
            density = np.count_nonzero(thresh) / (gray.shape[0] * gray.shape[1])
            contrast = np.std(gray) / 255.0
            blur = cv2.Laplacian(gray, cv2.CV_64F).var()
            
            if density > 0.3:  # Dense
                nms = min(0.4 + density * 0.3, 0.6)
                conf = max(0.3 - density * 0.2, 0.15)
            else:  # Sparse
                nms = 0.4
                conf = 0.25
                
            if blur < 100:  # Blurry
                conf *= 0.8
            if contrast < 0.15:  # Low contrast
                conf *= 0.9
                
            self.nms_spin.setValue(nms)
            self.score_spin.setValue(conf)
            
            self.start_analysis()
            
        except Exception as e:
            logger.error(f"Auto-optimization failed: {e}")
            self.show_status_message(tr("error.auto_optimize_failed"))

    def save_analysis_results(self, image_path: str, results: Dict[str, Any]):
        """Save analysis results to project directory"""
        if not self.current_project_path:
            logger.warning("Project path not set, skipping result saving.")
            return

        project_name = get_project_name(self.current_project_path)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_filename = f"{project_name}_result_{timestamp}"
        results_dir = os.path.join(self.current_project_path, "results")
        
        os.makedirs(results_dir, exist_ok=True)
        
        try:
            self._save_result_image(results_dir, base_filename)
            self._save_csv_results(results_dir, base_filename, results)
            self._save_json_results(results_dir, base_filename, results)
            logger.info(f"Results saved to: {results_dir}")
        except Exception as e:
            logger.error(f"Error saving results: {e}")
            QMessageBox.warning(
                self,
                tr("dialog.warning"),
                tr("error.save_results").format(error=str(e))
            )

    @pyqtSlot()
    def export_results(self):
        """Show export dialog and handle result export"""
        if not self.current_results:
            return
            
        try:
            path, chosen_filter = QFileDialog.getSaveFileName(
                self,
                tr("analysis.results.export"),
                "",
                "CSV (*.csv);;JSON (*.json);;Excel (*.xlsx)"
            )
            
            if not path:
                return
                
            success = False
            if chosen_filter == "CSV (*.csv)":
                if not path.endswith('.csv'):
                    path += '.csv'
                success = ResultExporter.export_csv(path, self.current_results)
            elif chosen_filter == "JSON (*.json)":
                if not path.endswith('.json'):
                    path += '.json'
                success = ResultExporter.export_json(path, self.current_results)
            else:
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

    def on_params_changed(self):
        """Handle parameter changes"""
        if self.current_image and self.current_results:
            self.start_analysis()

    def display_image(self, path: str, results: Optional[Dict[str, Any]] = None):
        """Display image with results overlay"""
        if not path or not os.path.exists(path):
            return
            
        try:
            # 使用cv2读取图片以确保正确处理编码
            import cv2
            import numpy as np
            
            img_array = np.fromfile(path, np.uint8)
            img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
            if img is None:
                raise RuntimeError("Failed to load image")
            
            # 转换为RGB
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            height, width = img.shape[:2]
            
            # 在图像上添加标注
            if results:
                # 绘制标注时间和文件名
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                filename = os.path.basename(path)
                font = cv2.FONT_HERSHEY_SIMPLEX
                font_scale = min(width, height) / 2000
                thickness = max(1, int(font_scale * 2))
                
                # 添加文本背景
                # 添加文本（使用正确的元组格式）
                file_pos = (10, 30)
                time_pos = (10, 60)
                
                cv2.putText(img, f"文件: {filename}", 
                           file_pos, font, font_scale, (0, 0, 0), thickness + 1)
                cv2.putText(img, f"分析时间: {timestamp}", 
                           time_pos, font, font_scale, (0, 0, 0), thickness + 1)
                
                cv2.putText(img, f"文件: {filename}", 
                           file_pos, font, font_scale, (255, 255, 255), thickness)
                cv2.putText(img, f"分析时间: {timestamp}", 
                           time_pos, font, font_scale, (255, 255, 255), thickness)
                
                # 绘制菌落标注
                colonies = results.get("colonies", [])
                for i, colony in enumerate(colonies, 1):
                    x = int(colony.get("x", 0))
                    y = int(colony.get("y", 0))
                    r = int(colony.get("radius", 0))
                    conf = colony.get("confidence", 0)
                    
                    # 根据置信度设置颜色
                    color = (
                        int(255 * (1 - conf)),  # R
                        int(255 * conf),        # G
                        0                       # B
                    )
                    
                    # 画圆和编号
                    cv2.circle(img, (x, y), r, color, thickness)
                    text_pos = (x-r//2, y)  # 创建元组
                    cv2.putText(img, str(i), text_pos, 
                              font, font_scale * 0.8, color, thickness)
            
            # 转换为QPixmap显示
            height, width = img.shape[:2]
            bytes_per_line = 3 * width
            image = QImage(img.data, width, height, bytes_per_line, QImage.Format.Format_RGB888)
            pixmap = QPixmap.fromImage(image)
            
            # 缩放以适应显示区域
            scaled = pixmap.scaled(
                self.scroll.width(),
                self.scroll.height(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            
            self.display.setPixmap(scaled)
            
        except Exception as e:
            logger.error(f"Error displaying image: {e}")
            self.show_status_message(tr("error.display_image"))
