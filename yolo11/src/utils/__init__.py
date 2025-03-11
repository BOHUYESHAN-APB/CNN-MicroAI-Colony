"""
YOLOv11 utilities module.

This package contains utility functions and classes for YOLOv11 implementation.
Key components:
- Advanced configuration management
- Enhanced data loading and preprocessing
- Advanced data augmentation with TTA
- Custom transform support
"""

from .config import Config, ConfigError
from .dataset import (
    ColonyDataset,
    create_dataloader,
    DatasetError
)
from .transforms import (
    get_train_transforms,
    get_val_transforms,
    get_test_transforms,
    get_mosaic_transforms,
    apply_transforms,
    TransformError
)

# Version information
__version__ = '1.0.0'
__author__ = 'Colony Detection Team'

# Module exports
__all__ = [
    # Configuration
    'Config',
    'ConfigError',
    
    # Dataset
    'ColonyDataset',
    'create_dataloader',
    'DatasetError',
    
    # Transforms
    'get_train_transforms',
    'get_val_transforms',
    'get_test_transforms',
    'get_mosaic_transforms',
    'apply_transforms',
    'TransformError'
]
