"""
DAMO-YOLO utilities module.

This package contains utility functions and classes for DAMO-YOLO implementation.
Key components:
- Configuration management
- Data loading and preprocessing
- Data augmentation
"""

from .config import Config
from .dataset import ColonyDataset, create_dataloader
from .transforms import (
    get_train_transforms,
    get_val_transforms,
    get_test_transforms,
    apply_transforms
)

__version__ = '1.0.0'
__author__ = 'Colony Detection Team'

__all__ = [
    # Configuration
    'Config',
    
    # Dataset
    'ColonyDataset',
    'create_dataloader',
    
    # Transforms
    'get_train_transforms',
    'get_val_transforms',
    'get_test_transforms',
    'apply_transforms'
]
