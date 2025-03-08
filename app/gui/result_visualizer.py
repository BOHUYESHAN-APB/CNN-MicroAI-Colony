import os
import logging
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QMdiArea, QMdiSubWindow, 
    QScrollArea, QFrame, QFileDialog,
    QPushButton, QProgressBar, QGroupBox
)
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QImage, QPixmap, QPalette, QColor

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

logger = logging.getLogger(__name__)

# 设置 matplotlib 暗色主题
plt.style.use('dark_background')

class DarkMdiArea(QMdiArea):
    """自定义暗色 MDI 区域"""
    def __init__(self, parent=None):
        super().__init__(parent)
        # 设置暗色背景
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor("#282c34"))
        self.setPalette(palette)
        self.setBackground(QColor("#282c34"))

class ResultVisualizer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        logger.info("Initializing ResultVisualizer")
        
        self._setup_ui()
        logger.info("ResultVisualizer initialization complete")
        
    def _setup_ui(self):
        """Setup UI components"""
        layout = QVBoxLayout()
        
        # Actions group
        self.action_group = QGroupBox(self.tr("Result Actions"))
        action_layout = QHBoxLayout()
        
        self.btn_export_all = QPushButton(self.tr("Export All"))
        self.btn_export_all.clicked.connect(self._export_all)
        self.btn_export_all.setEnabled(False)
        self.btn_export_all.setToolTip(self.tr("Export all analysis results"))
        action_layout.addWidget(self.btn_export_all)
        
        self.btn_clear = QPushButton(self.tr("Clear Results"))
        self.btn_clear.clicked.connect(self._clear_results)
        self.btn_clear.setEnabled(False)
        self.btn_clear.setToolTip(self.tr("Clear all analysis results"))
        action_layout.addWidget(self.btn_clear)
        
        action_layout.addStretch()
        self.action_group.setLayout(action_layout)
        layout.addWidget(self.action_group)

        # Progress bar for export operations
        self.progress_layout = QHBoxLayout()
        self.progress_label = QLabel(self.tr("Export Progress:"))
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_layout.addWidget(self.progress_label)
        self.progress_layout.addWidget(self.progress_bar)
        layout.addLayout(self.progress_layout)
        
        # MDI area for multiple result windows
        self.mdi_area = DarkMdiArea()
        self.mdi_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.mdi_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        layout.addWidget(self.mdi_area)
        
        self.setLayout(layout)
        
    def add_single_result(self, result_data):
        """Display single image analysis result"""
        logger.info("Adding single analysis result")
        
        # Create sub window
        sub_window = QMdiSubWindow()
        sub_window.setWindowTitle(self.tr("Single Image Analysis"))
        
        # Result widget container
        result_widget = QWidget()
        content_layout = QVBoxLayout()
        
        # Count display group
        count_group = QGroupBox(self.tr("Colony Count"))
        count_layout = QVBoxLayout()
        count_label = QLabel(f"<h1>{result_data['count']}</h1>")
        count_label.setAlignment(Qt.AlignCenter)
        count_layout.addWidget(count_label)
        count_group.setLayout(count_layout)
        content_layout.addWidget(count_group)
        
        # Confidence visualization
        if 'confidence' in result_data:
            confidence_group = QGroupBox(self.tr("Detection Confidence"))
            confidence_layout = QVBoxLayout()
            
            fig = Figure(figsize=(5, 4), facecolor='#282c34')
            ax = fig.add_subplot(111)
            ax.scatter(range(len(result_data['confidence'])), 
                      result_data['confidence'],
                      color='#61afef')
            ax.set_title(self.tr("Detection Confidence"), color='#abb2bf')
            ax.set_xlabel(self.tr("Colony Index"), color='#abb2bf')
            ax.set_ylabel(self.tr("Confidence Score"), color='#abb2bf')
            ax.set_facecolor('#21252b')
            ax.tick_params(colors='#abb2bf')
            ax.grid(True, linestyle='--', alpha=0.3, color='#abb2bf')
            
            canvas = FigureCanvas(fig)
            confidence_layout.addWidget(canvas)
            confidence_group.setLayout(confidence_layout)
            content_layout.addWidget(confidence_group)
        
        # Export button
        btn_export = QPushButton(self.tr("Export"))
        btn_export.clicked.connect(
            lambda: self._export_result(sub_window, result_data)
        )
        btn_export.setToolTip(self.tr("Export this result"))
        content_layout.addWidget(btn_export)
        
        result_widget.setLayout(content_layout)
        sub_window.setWidget(result_widget)
        
        self.mdi_area.addSubWindow(sub_window)
        sub_window.show()
        
        self.btn_export_all.setEnabled(True)
        self.btn_clear.setEnabled(True)
        
    def add_multi_result(self, results_data):
        """Display multi-image comparison results"""
        logger.info("Adding multi-image comparison results")
        
        # Create sub window
        sub_window = QMdiSubWindow()
        sub_window.setWindowTitle(self.tr("Batch Analysis Results"))
        
        # Result widget
        result_widget = QScrollArea()
        content_widget = QWidget()
        content_layout = QVBoxLayout()
        
        # Summary statistics
        counts = [r['count'] for r in results_data]
        stats = {
            'Mean': sum(counts) / len(counts),
            'Median': sorted(counts)[len(counts)//2],
            'Std Dev': (sum((x - sum(counts)/len(counts))**2 for x in counts) / len(counts))**0.5,
            'CV': (sum((x - sum(counts)/len(counts))**2 for x in counts) / len(counts))**0.5 / (sum(counts)/len(counts)) * 100
        }
        
        stats_group = QGroupBox(self.tr("Summary Statistics"))
        stats_layout = QVBoxLayout()
        stats_text = "\n".join(f"{k}: {v:.2f}" for k, v in stats.items())
        stats_label = QLabel(f"<pre>{stats_text}</pre>")
        stats_layout.addWidget(stats_label)
        stats_group.setLayout(stats_layout)
        content_layout.addWidget(stats_group)
        
        # Distribution plot
        dist_group = QGroupBox(self.tr("Count Distribution"))
        dist_layout = QVBoxLayout()
        fig = Figure(figsize=(8, 6), facecolor='#282c34')
        ax = fig.add_subplot(111)
        bp = ax.boxplot(counts, patch_artist=True)
        
        # 自定义箱型图颜色
        plt.setp(bp['boxes'], facecolor='#61afef', alpha=0.7)
        plt.setp(bp['whiskers'], color='#abb2bf')
        plt.setp(bp['caps'], color='#abb2bf')
        plt.setp(bp['medians'], color='#98c379')
        plt.setp(bp['fliers'], marker='o', markerfacecolor='#e06c75')
        
        ax.set_title(self.tr("Colony Count Distribution"), color='#abb2bf')
        ax.set_ylabel(self.tr("Colony Count"), color='#abb2bf')
        ax.set_facecolor('#21252b')
        ax.tick_params(colors='#abb2bf')
        ax.grid(True, linestyle='--', alpha=0.3, color='#abb2bf')
        
        canvas = FigureCanvas(fig)
        dist_layout.addWidget(canvas)
        dist_group.setLayout(dist_layout)
        content_layout.addWidget(dist_group)
        
        # Individual results
        for i, result in enumerate(results_data):
            result_group = QGroupBox(f"Image {i+1}")
            result_layout = QVBoxLayout()
            
            count_label = QLabel(f"<b>Count: {result['count']}</b>")
            result_layout.addWidget(count_label)
            
            if 'confidence' in result:
                conf_fig = Figure(figsize=(4, 3), facecolor='#282c34')
                conf_ax = conf_fig.add_subplot(111)
                conf_ax.scatter(range(len(result['confidence'])), 
                              result['confidence'],
                              color='#61afef')
                conf_ax.set_title(self.tr("Detection Confidence"), color='#abb2bf')
                conf_ax.set_facecolor('#21252b')
                conf_ax.tick_params(colors='#abb2bf')
                conf_ax.grid(True, linestyle='--', alpha=0.3, color='#abb2bf')
                
                conf_canvas = FigureCanvas(conf_fig)
                result_layout.addWidget(conf_canvas)
            
            result_group.setLayout(result_layout)
            content_layout.addWidget(result_group)
        
        # Export button
        btn_export = QPushButton(self.tr("Export"))
        btn_export.clicked.connect(
            lambda: self._export_result(sub_window, results_data)
        )
        btn_export.setToolTip(self.tr("Export batch analysis results"))
        content_layout.addWidget(btn_export)
        
        content_widget.setLayout(content_layout)
        result_widget.setWidget(content_widget)
        sub_window.setWidget(result_widget)
        
        self.mdi_area.addSubWindow(sub_window)
        sub_window.show()
        
        self.btn_export_all.setEnabled(True)
        self.btn_clear.setEnabled(True)
        
    @Slot()
    def _export_result(self, window, data):
        """Export single result window"""
        file_name, _ = QFileDialog.getSaveFileName(
            self,
            self.tr("Export Result"),
            "",
            self.tr("PDF files (*.pdf);;PNG files (*.png)")
        )
        
        if file_name:
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)
            
            if file_name.endswith('.pdf'):
                self._export_pdf(window, file_name)
            else:
                self._export_png(window, file_name)
                
            self.progress_bar.setValue(100)
            self.progress_bar.setVisible(False)
                
    @Slot()
    def _export_all(self):
        """Export all result windows"""
        export_dir = QFileDialog.getExistingDirectory(
            self,
            self.tr("Select Export Directory")
        )
        
        if export_dir:
            total = len(self.mdi_area.subWindowList())
            self.progress_bar.setVisible(True)
            
            for i, window in enumerate(self.mdi_area.subWindowList()):
                pdf_path = os.path.join(export_dir, f"result_{i+1}.pdf")
                self._export_pdf(window, pdf_path)
                self.progress_bar.setValue(int((i + 1) * 100 / total))
                
            self.progress_bar.setVisible(False)
                
    def _export_pdf(self, window, file_path):
        """Export window content as PDF"""
        # Implementation depends on specific PDF generation library
        logger.info(f"Exporting PDF to: {file_path}")
        
    def _export_png(self, window, file_path):
        """Export window content as PNG"""
        # Implementation depends on specific image generation approach
        logger.info(f"Exporting PNG to: {file_path}")
        
    @Slot()
    def _clear_results(self):
        """Clear all result windows"""
        self.mdi_area.closeAllSubWindows()
        self.btn_export_all.setEnabled(False)
        self.btn_clear.setEnabled(False)

    def retranslateUi(self):
        """Retranslate UI elements."""
        self.action_group.setTitle(self.tr("Result Actions"))
        self.btn_export_all.setText(self.tr("Export All"))
        self.btn_export_all.setToolTip(self.tr("Export all analysis results"))
        self.btn_clear.setText(self.tr("Clear Results"))
        self.btn_clear.setToolTip(self.tr("Clear all analysis results"))
        self.progress_label.setText(self.tr("Export Progress:"))
        # Update existing subwindow titles
        for window in self.mdi_area.subWindowList():
            if window.windowTitle() == "Single Image Analysis":
                window.setWindowTitle(self.tr("Single Image Analysis"))
            elif window.windowTitle() == "Batch Analysis Results":
                window.setWindowTitle(self.tr("Batch Analysis Results"))
            # Find and retranslate widgets within each subwindow
            for widget in window.widget().findChildren(QWidget):
                if hasattr(widget, 'setText') and widget.text():
                    widget.setText(self.tr(widget.text()))
                if hasattr(widget, 'setTitle') and widget.title():
                    widget.setTitle(self.tr(widget.title()))
                if hasattr(widget, 'setToolTip') and widget.toolTip():
                    widget.setToolTip(self.tr(widget.toolTip()))
