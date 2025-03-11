"""
Data transformation utilities for DAMO-YOLO.
"""

import cv2
import numpy as np
import albumentations as A
from typing import Dict, Optional

def get_train_transforms(
    input_size: int = 224,
    p: float = 0.5
) -> A.Compose:
    """
    Get training data transforms.
    
    Args:
        input_size: Target image size
        p: Probability of applying each augmentation
        
    Returns:
        Albumentations composition of transforms
    """
    return A.Compose([
        A.RandomResizedCrop(
            height=input_size,
            width=input_size,
            scale=(0.8, 1.0),
            ratio=(0.9, 1.1),
            p=1.0
        ),
        A.HorizontalFlip(p=p),
        A.VerticalFlip(p=p),
        A.RandomRotate90(p=p),
        A.OneOf([
            A.RandomBrightnessContrast(p=1),
            A.RandomGamma(p=1)
        ], p=p),
        A.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225],
            max_pixel_value=255.0,
            p=1.0
        ),
    ], p=1.0)

def get_val_transforms(
    input_size: int = 224
) -> A.Compose:
    """
    Get validation data transforms.
    
    Args:
        input_size: Target image size
        
    Returns:
        Albumentations composition of transforms
    """
    return A.Compose([
        A.Resize(input_size, input_size),
        A.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225],
            max_pixel_value=255.0,
            p=1.0
        ),
    ], p=1.0)

def get_test_transforms(
    input_size: int = 224
) -> A.Compose:
    """
    Get test data transforms.
    
    Args:
        input_size: Target image size
        
    Returns:
        Albumentations composition of transforms
    """
    return get_val_transforms(input_size)

def apply_transforms(
    image: np.ndarray,
    mask: Optional[np.ndarray] = None,
    transforms: Optional[A.Compose] = None
) -> Dict[str, np.ndarray]:
    """
    Apply transforms to image and mask.
    
    Args:
        image: Input image
        mask: Optional segmentation mask
        transforms: Albumentations transforms to apply
        
    Returns:
        Dict containing transformed image and mask
    """
    if transforms is None:
        return {'image': image, 'mask': mask}
        
    result = transforms(
        image=image,
        mask=mask if mask is not None else np.zeros_like(image[:, :, 0])
    )
    
    return result
