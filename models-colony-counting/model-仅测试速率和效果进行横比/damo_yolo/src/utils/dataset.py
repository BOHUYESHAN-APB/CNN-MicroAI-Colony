"""
Dataset utilities for DAMO-YOLO.

This module handles data loading and preprocessing for colony detection.
"""

import cv2
import torch
import numpy as np
from pathlib import Path
from torch.utils.data import Dataset, DataLoader
from typing import List, Tuple, Dict, Optional

class ColonyDataset(Dataset):
    """Colony detection dataset."""
    
    def __init__(self, data_root: str, transforms=None, train: bool = True):
        """
        Initialize dataset.
        
        Args:
            data_root: Root directory containing images and annotations
            transforms: Optional transforms to apply to images
            train: Whether this is training set
        """
        self.data_root = Path(data_root)
        self.transforms = transforms
        self.train = train
        
        # Load image paths and annotations
        self.samples = self._load_samples()
        
    def _load_samples(self) -> List[Dict]:
        """Load dataset samples."""
        samples = []
        img_files = sorted(self.data_root.glob("*.jpg"))
        
        for img_file in img_files:
            json_file = self.data_root / f"{img_file.stem}.json"
            if json_file.exists():
                samples.append({
                    'image': str(img_file),
                    'annotation': str(json_file)
                })
                
        return samples
    
    def __len__(self) -> int:
        """Get dataset size."""
        return len(self.samples)
    
    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Get dataset item.
        
        Args:
            idx: Item index
            
        Returns:
            tuple: (image, target) where target is the colony mask
        """
        sample = self.samples[idx]
        
        # Load image
        image = cv2.imread(sample['image'])
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Load annotation and create target mask
        # TODO: Implement annotation loading based on format
        target = np.zeros((image.shape[0], image.shape[1]), dtype=np.float32)
        
        # Apply transforms
        if self.transforms is not None:
            transformed = self.transforms(image=image, mask=target)
            image = transformed['image']
            target = transformed['mask']
            
        # Convert to tensor
        image = torch.from_numpy(image).permute(2, 0, 1).float() / 255.0
        target = torch.from_numpy(target).float()
        
        return image, target

def create_dataloader(
    data_root: str,
    batch_size: int,
    num_workers: int = 4,
    transforms = None,
    train: bool = True
) -> DataLoader:
    """
    Create data loader.
    
    Args:
        data_root: Dataset root directory
        batch_size: Batch size
        num_workers: Number of worker processes
        transforms: Optional transforms
        train: Whether this is training set
        
    Returns:
        DataLoader: PyTorch data loader
    """
    dataset = ColonyDataset(
        data_root=data_root,
        transforms=transforms,
        train=train
    )
    
    return DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=train,
        num_workers=num_workers,
        pin_memory=True
    )
