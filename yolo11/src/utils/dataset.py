"""
Enhanced dataset utilities for YOLOv11.

This module provides advanced data loading and preprocessing functionality.
"""

import cv2
import json
import torch
import numpy as np
from pathlib import Path
from typing import List, Tuple, Dict, Optional, Union, Any
from torch.utils.data import Dataset, DataLoader
from .config import Config, ConfigError

class DatasetError(Exception):
    """Dataset-related error."""
    pass

class ColonyDataset(Dataset):
    """Enhanced colony detection dataset."""
    
    def __init__(
        self,
        data_root: str,
        transforms=None,
        train: bool = True,
        config: Optional[Union[Dict, Config]] = None,
        cache_images: bool = False
    ):
        """
        Initialize dataset.
        
        Args:
            data_root: Root directory containing images and annotations
            transforms: Optional transforms to apply to images
            train: Whether this is training set
            config: Optional configuration override
            cache_images: Whether to cache images in memory
        """
        self.data_root = Path(data_root)
        self.transforms = transforms
        self.train = train
        self.cache_images = cache_images
        
        # Load configuration
        if isinstance(config, dict):
            self.config = config
        elif isinstance(config, Config):
            self.config = config.get_data_config()
        else:
            self.config = Config().get_data_config()
            
        # Initialize cache
        self.image_cache = {}
        
        # Load and validate samples
        self.samples = self._load_samples()
        if not self.samples:
            raise DatasetError(f"No valid samples found in {data_root}")
            
        print(f"Loaded {len(self.samples)} samples from {data_root}")
        if self.cache_images:
            self._cache_images()
    
    def _load_samples(self) -> List[Dict]:
        """
        Load and validate dataset samples.
        
        Returns:
            List of valid samples with image and annotation paths
        """
        samples = []
        img_files = sorted(self.data_root.glob("*.jpg"))
        
        for img_file in img_files:
            json_file = self.data_root / f"{img_file.stem}.json"
            if not json_file.exists():
                print(f"Warning: No annotation found for {img_file.name}")
                continue
                
            # Validate image
            try:
                img = cv2.imread(str(img_file))
                if img is None:
                    print(f"Warning: Failed to load image {img_file.name}")
                    continue
            except Exception as e:
                print(f"Error loading {img_file.name}: {e}")
                continue
                
            # Validate annotation
            try:
                with open(json_file, 'r') as f:
                    ann = json.load(f)
                if not self._validate_annotation(ann):
                    print(f"Warning: Invalid annotation in {json_file.name}")
                    continue
            except Exception as e:
                print(f"Error loading annotation {json_file.name}: {e}")
                continue
                
            samples.append({
                'image': str(img_file),
                'annotation': str(json_file),
                'image_id': img_file.stem
            })
                
        return samples
    
    def _validate_annotation(self, ann: Dict[str, Any]) -> bool:
        """
        Validate annotation format.
        
        Args:
            ann: Loaded annotation dictionary
            
        Returns:
            bool: Whether annotation is valid
        """
        required_keys = ["图片名称", "实际菌落数"]
        return all(key in ann for key in required_keys)
    
    def _cache_images(self) -> None:
        """Cache all images in memory."""
        print("Caching images...")
        for sample in self.samples:
            img_path = sample['image']
            if img_path not in self.image_cache:
                image = cv2.imread(img_path)
                image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                self.image_cache[img_path] = image
        print("Image caching complete")
    
    def __len__(self) -> int:
        """Get dataset size."""
        return len(self.samples)
    
    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor, Dict]:
        """
        Get dataset item.
        
        Args:
            idx: Item index
            
        Returns:
            tuple: (image, target, metadata)
        """
        sample = self.samples[idx]
        
        # Load or get cached image
        if self.cache_images:
            image = self.image_cache[sample['image']].copy()
        else:
            image = cv2.imread(sample['image'])
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Load annotation
        with open(sample['annotation'], 'r') as f:
            ann = json.load(f)
            
        # Create target mask
        # TODO: Implement colony location-based mask generation
        target = np.zeros((image.shape[0], image.shape[1]), dtype=np.float32)
        
        # Apply transforms
        if self.transforms is not None:
            transformed = self.transforms(image=image, mask=target)
            image = transformed['image']
            target = transformed['mask']
            
        # Convert to tensor
        image = torch.from_numpy(image).permute(2, 0, 1).float() / 255.0
        target = torch.from_numpy(target).float()
        
        # Prepare metadata
        metadata = {
            'image_id': sample['image_id'],
            'colony_count': ann['实际菌落数']
        }
        
        return image, target, metadata

def create_dataloader(
    data_root: str,
    batch_size: int,
    num_workers: int = 4,
    transforms = None,
    train: bool = True,
    config: Optional[Union[Dict, Config]] = None,
    cache_images: bool = False
) -> DataLoader:
    """
    Create enhanced data loader.
    
    Args:
        data_root: Dataset root directory
        batch_size: Batch size
        num_workers: Number of worker processes
        transforms: Optional transforms
        train: Whether this is training set
        config: Optional configuration
        cache_images: Whether to cache images
        
    Returns:
        DataLoader: PyTorch data loader
    """
    dataset = ColonyDataset(
        data_root=data_root,
        transforms=transforms,
        train=train,
        config=config,
        cache_images=cache_images
    )
    
    return DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=train,
        num_workers=num_workers,
        pin_memory=True,
        drop_last=train  # Drop incomplete batches during training
    )
