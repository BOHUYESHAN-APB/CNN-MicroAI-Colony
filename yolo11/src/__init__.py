"""
YOLOv11 source module.

This package contains the implementation of YOLOv11 model for colony detection.
Key components:
- Advanced training script with attention mechanisms
- Enhanced model architecture with residual connections
- Multi-scale feature processing utilities
"""

from .models import YOLO11Detector, ConvBlock, YOLO11Neck, YOLO11Head

__version__ = '1.0.0'
__author__ = 'Colony Detection Team'

__all__ = [
    'YOLO11Detector',
    'ConvBlock', 
    'YOLO11Neck',
    'YOLO11Head'
]
