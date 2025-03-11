"""
Enhanced data transformation utilities for YOLOv11.
"""

import cv2
import numpy as np
import albumentations as A
from typing import Dict, Optional, Union, List, Tuple
from .config import Config, ConfigError

class TransformError(Exception):
    """Transform-related error."""
    pass

def get_mosaic_transforms(
    input_size: int = 224,
    scale_range: Tuple[float, float] = (0.5, 1.5)
) -> A.Compose:
    """
    Get mosaic augmentation transforms.
    
    Args:
        input_size: Target image size
        scale_range: Range for random scaling
        
    Returns:
        Albumentations composition of transforms
    """
    return A.Compose([
        A.RandomScale(scale_limit=scale_range, p=1.0),
        A.PadIfNeeded(
            min_height=input_size,
            min_width=input_size,
            border_mode=cv2.BORDER_CONSTANT
        ),
        A.RandomCrop(height=input_size, width=input_size, p=1.0),
        A.HorizontalFlip(p=0.5),
        A.VerticalFlip(p=0.5),
    ])

def get_train_transforms(
    config: Optional[Union[Dict, Config]] = None,
    input_size: int = 224,
    p: float = 0.5
) -> A.Compose:
    """
    Get enhanced training data transforms.
    
    Args:
        config: Optional configuration override
        input_size: Target image size
        p: Base probability for augmentations
        
    Returns:
        Albumentations composition of transforms
    """
    # Load config if provided
    if isinstance(config, Config):
        aug_config = config.get_training_config().get('augmentation', {})
    elif isinstance(config, dict):
        aug_config = config.get('augmentation', {})
    else:
        aug_config = {}

    transforms = [
        # Spatial transforms
        A.RandomResizedCrop(
            height=input_size,
            width=input_size,
            scale=(0.7, 1.0),
            ratio=(0.8, 1.2),
            p=1.0
        ),
        A.ShiftScaleRotate(
            shift_limit=0.1,
            scale_limit=0.2,
            rotate_limit=45,
            p=p
        ),
        A.HorizontalFlip(p=p),
        A.VerticalFlip(p=p),
        A.RandomRotate90(p=p),
        
        # Color transforms
        A.OneOf([
            A.RandomBrightnessContrast(
                brightness_limit=0.2,
                contrast_limit=0.2,
                p=1
            ),
            A.RandomGamma(gamma_limit=(80, 120), p=1),
            A.HueSaturationValue(
                hue_shift_limit=20,
                sat_shift_limit=30,
                val_shift_limit=20,
                p=1
            )
        ], p=p),
        
        # Noise and blur
        A.OneOf([
            A.GaussNoise(var_limit=(10.0, 50.0), p=1),
            A.GaussianBlur(blur_limit=(3, 7), p=1),
            A.MotionBlur(blur_limit=(3, 7), p=1)
        ], p=0.3),
        
        # Advanced augmentations
        A.OneOf([
            A.GridDistortion(p=1),
            A.OpticalDistortion(p=1),
            A.ElasticTransform(p=1)
        ], p=0.2),
        
        # Cutout/dropout for robustness
        A.OneOf([
            A.Cutout(
                num_holes=8,
                max_h_size=input_size//16,
                max_w_size=input_size//16,
                p=1
            ),
            A.CoarseDropout(
                max_holes=8,
                max_height=input_size//16,
                max_width=input_size//16,
                p=1
            )
        ], p=0.2),
        
        # Normalization (always applied)
        A.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225],
            max_pixel_value=255.0,
            p=1.0
        ),
    ]
    
    # Add custom transforms from config
    if 'custom_transforms' in aug_config:
        try:
            transforms.extend(_parse_custom_transforms(aug_config['custom_transforms']))
        except Exception as e:
            raise TransformError(f"Failed to parse custom transforms: {e}")
    
    return A.Compose(transforms, p=1.0)

def get_val_transforms(
    input_size: int = 224,
    pad_mode: int = cv2.BORDER_CONSTANT
) -> A.Compose:
    """
    Get validation data transforms.
    
    Args:
        input_size: Target image size
        pad_mode: OpenCV border mode for padding
        
    Returns:
        Albumentations composition of transforms
    """
    return A.Compose([
        A.LongestMaxSize(max_size=input_size),
        A.PadIfNeeded(
            min_height=input_size,
            min_width=input_size,
            border_mode=pad_mode
        ),
        A.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225],
            max_pixel_value=255.0,
            p=1.0
        ),
    ], p=1.0)

def get_test_transforms(
    input_size: int = 224,
    tta: bool = False
) -> Union[A.Compose, List[A.Compose]]:
    """
    Get test data transforms with optional TTA.
    
    Args:
        input_size: Target image size
        tta: Whether to use test-time augmentation
        
    Returns:
        Single transform composition or list for TTA
    """
    base_transform = get_val_transforms(input_size)
    
    if not tta:
        return base_transform
        
    # Create TTA transforms
    tta_transforms = [
        base_transform,
        A.Compose([
            A.HorizontalFlip(p=1),
            *base_transform
        ]),
        A.Compose([
            A.VerticalFlip(p=1),
            *base_transform
        ]),
        A.Compose([
            A.Transpose(p=1),
            *base_transform
        ])
    ]
    
    return tta_transforms

def apply_transforms(
    image: np.ndarray,
    mask: Optional[np.ndarray] = None,
    transforms: Optional[Union[A.Compose, List[A.Compose]]] = None
) -> Union[Dict[str, np.ndarray], List[Dict[str, np.ndarray]]]:
    """
    Apply transforms to image and mask.
    
    Args:
        image: Input image
        mask: Optional segmentation mask
        transforms: Transforms to apply (single or list for TTA)
        
    Returns:
        Dict or list of dicts containing transformed data
    """
    if transforms is None:
        return {'image': image, 'mask': mask}
        
    if isinstance(transforms, list):
        # Apply TTA transforms
        results = []
        for transform in transforms:
            result = transform(
                image=image,
                mask=mask if mask is not None else np.zeros_like(image[:, :, 0])
            )
            results.append(result)
        return results
        
    # Apply single transform
    return transforms(
        image=image,
        mask=mask if mask is not None else np.zeros_like(image[:, :, 0])
    )

def _parse_custom_transforms(config: List[Dict]) -> List[A.BasicTransform]:
    """Parse custom transforms from config."""
    transforms = []
    for transform_config in config:
        name = transform_config.pop('name')
        if not hasattr(A, name):
            raise TransformError(f"Unknown transform: {name}")
        transform_class = getattr(A, name)
        transforms.append(transform_class(**transform_config))
    return transforms
