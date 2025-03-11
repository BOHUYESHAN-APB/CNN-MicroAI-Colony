"""
DAMO-YOLO source module.

This package contains the implementation of DAMO-YOLO model for colony detection.
Key components:
- Training script
- Model architecture
- Data processing utilities
"""

from .models import DAMODetector, ConvBlock, DAMONeck, DAMOHead

__version__ = '1.0.0'
__author__ = 'Colony Detection Team'

__all__ = [
    'DAMODetector',
    'ConvBlock', 
    'DAMONeck',
    'DAMOHead'
]
