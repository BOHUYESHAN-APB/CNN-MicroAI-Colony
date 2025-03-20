"""
Result image dock implementation
结果图像停靠窗口实现
"""
import os
import cv2
import numpy as np
import logging
from PyQt6.QtWidgets import (QLabel, QVBoxLayout, QPushButton, 
                            QToolBar, QFileDialog, QMessageBox)
from PyQt6.QtCore import Qt, QSize, QDir
from PyQt6.QtGui import QImage, QPixmap, QAction
from .base_dock_widget import BaseDockWidget
from .toolbar_constants import SMALL_ICON_SIZE, TOOLBAR_STYLE
from ..utils.i18n import translate

logger = logging.getLogger(__name__)

class ResultImageDock(BaseDockWidget):
    """Result image dock widget with enhanced docking capabilities"""
    
    def __init__(self, parent=None):
        super().__init__("检测结果", parent)
        self.setup_ui()
        
    def setup_ui(self):
        """Setup user interface"""
        # Create toolbar
        toolbar = QToolBar()
        toolbar.setIconSize(SMALL_ICON_SIZE)
        toolbar.setStyleSheet(TOOLBAR_STYLE)
        
        # Add save action
        save_action = QAction(translate("保存结果图像"), self)
        save_action.triggered.connect(self.save_image)
        toolbar.addAction(save_action)
        
        self.add_widget(toolbar)
        
        # Create image label
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet("""
            QLabel {
                background: #1e1e1e;
                border: none;
            }
        """)
        self.set_central_widget(self.image_label)
        
        # Store current image
        self.current_image = None
        
        # Enable dock features
        self.setObjectName("result_image_dock")
        
    def display_image(self, image):
        """Display OpenCV image"""
        try:
            # Store image
            self.current_image = image.copy()
            
            # Convert to QImage
            height, width, channel = image.shape
            bytes_per_line = 3 * width
            qimg = QImage(image.data, width, height, bytes_per_line, 
                         QImage.Format.Format_RGB888)
            
            # Create pixmap and display
            pixmap = QPixmap.fromImage(qimg)
            self.display_pixmap(pixmap)
            
        except Exception as e:
            logger.error(f"Failed to display result image: {str(e)}")
            logger.debug("Image shape: {}".format(image.shape if image is not None else None), 
                        exc_info=True)
            
    def display_pixmap(self, pixmap):
        """Display QPixmap with proper scaling"""
        try:
            # Get sizes
            pixmap_size = pixmap.size()
            label_size = self.image_label.size()
            
            # Scale maintaining aspect ratio
            scaled_pixmap = pixmap.scaled(
                label_size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            
            # Display
            self.image_label.setPixmap(scaled_pixmap)
            
        except Exception as e:
            logger.error(f"Failed to display pixmap: {str(e)}")
            
    def display_results(self, image, detections):
        """Display detection results"""
        try:
            # Make copy for drawing
            display_image = image.copy()
            
            # Draw detection results
            for det in detections:
                # Get detection info
                box = det.get("box", [0, 0, 0, 0])
                center = det.get("center", (0, 0))
                diameter = det.get("diameter", 0)
                confidence = det.get("confidence", 0)
                
                # Draw bounding box
                cv2.rectangle(display_image, 
                            (int(box[0]), int(box[1])),
                            (int(box[2]), int(box[3])),
                            (0, 255, 0), 2)
                
                # Draw center point
                cv2.circle(display_image,
                          (int(center[0]), int(center[1])),
                          3, (255, 0, 0), -1)
                
                # Draw diameter
                cv2.circle(display_image,
                          (int(center[0]), int(center[1])),
                          int(diameter/2), (255, 0, 0), 2)
                
                # Add confidence text
                cv2.putText(display_image,
                           f"{confidence:.2f}",
                           (int(box[0]), int(box[1]-5)),
                           cv2.FONT_HERSHEY_SIMPLEX,
                           0.6, (0, 255, 0), 2)
                           
            # Display result
            self.display_image(display_image)
            
        except Exception as e:
            logger.error(f"Failed to display detection results: {str(e)}")
            logger.debug(f"Image shape: {image.shape if image is not None else None}", 
                        exc_info=True)
            
    def save_image(self):
        """Save current result image"""
        if self.current_image is None:
            QMessageBox.warning(
                self,
                translate("警告"),
                translate("没有可保存的结果图像")
            )
            return
            
        try:
            # Get save path
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                translate("保存结果图像"),
                "",
                "Images (*.png *.jpg *.jpeg)"
            )
            
            if file_path:
                # Convert path to native format
                save_path = QDir.toNativeSeparators(os.path.abspath(file_path))
                
                # Convert to BGR for saving
                save_image = cv2.cvtColor(self.current_image, cv2.COLOR_RGB2BGR)
                
                # Save image
                cv2.imwrite(save_path, save_image)
                logger.info(f"Saved result image to: {save_path}")
                
        except Exception as e:
            logger.error(f"Failed to save result image: {str(e)}")
            QMessageBox.critical(
                self,
                translate("错误"),
                translate("保存图像失败: ") + str(e)
            )
            
    def resizeEvent(self, event):
        """Handle resize events"""
        super().resizeEvent(event)
        # Update image display on resize if we have an image
        if self.current_image is not None:
            self.display_image(self.current_image)
