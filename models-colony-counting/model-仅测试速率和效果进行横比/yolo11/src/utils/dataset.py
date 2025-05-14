"""
Enhanced dataset utilities for YOLOv11.

This module provides advanced data loading and preprocessing functionality.
"""

import os
import cv2
import json
import torch
import numpy as np
from pathlib import Path
from typing import List, Tuple, Dict, Optional, Union, Any
from torch.utils.data import Dataset, DataLoader
from .config import Config

class DatasetError(Exception):
    """Dataset-related error."""
    pass

import logging

logger = logging.getLogger(__name__)


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
        logger.info("ColonyDataset __init__ started")
        logger.info(f"ColonyDataset data_root: {data_root}")
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
            self.config = config['data']
        else:
            self.config = Config("yolo11/config.yaml")['data']
        logger.debug(f"Dataset config: {self.config}")

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
        """Load and validate dataset samples, reading ground truth from result.json."""
        logger.info("ColonyDataset _load_samples started")
        samples = []
        self.data_root = Path(os.path.abspath(str(self.data_root)))
        logger.info(f"Absolute data root: {self.data_root}")

        # Load ground truth data from result.json
        gt_path = self.data_root / 'result.json'
        if not gt_path.exists():
            raise DatasetError(f"Ground truth file not found: {gt_path}")
        with open(gt_path, 'r', encoding='utf-8') as f: # Specify encoding
            ground_truth = json.load(f)
        gt_dict = {item["图片名称"]: item for item in ground_truth} # Create dict for easy lookup

        img_files = sorted([f for f in self.data_root.glob("*.jpg") if f.name != 'result.json']) # Exclude result.json
        logger.info(f"Found {len(img_files)} images in {self.data_root}")

        for img_file in img_files:
            image_name = img_file.name
            if image_name not in gt_dict:
                print(f"Warning: No ground truth data found for {image_name} in result.json")
                continue

            # Validate image loading
            try:
                print(f"Attempting to load image: {img_file}")  # Print image path
                # Ensure file path is decoded as UTF-8 for OpenCV
                img = cv2.imread(str(img_file).encode('utf-8').decode('utf-8'))
                if img is None:
                    print(f"Warning: Failed to load image {img_file.name}")
                    continue
            except Exception as e:
                print(f"Error loading {img_file.name}: {e}")
                continue


            samples.append({
                'image': str(img_file),
                'annotation': gt_dict[image_name], # Store GT data directly
                'image_id': img_file.stem
            })

        logger.info(f"Loaded {len(samples)} samples from {self.data_root}")
        logger.info("ColonyDataset _load_samples finished")
        return samples

    def _validate_annotation(self, ann: Dict[str, Any]) -> bool:
        """No longer validating individual annotation files."""
        return True  # Always return True as validation is now on result.json
    
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

        # Load annotation - already loaded in _load_samples
        ann = sample['annotation']

        # Create target mask
        # TODO: Implement colony location-based mask generation
        target = np.zeros((image.shape[0], image.shape[1]), dtype=np.float32)

        # Apply transforms
        if self.transforms is not None:
            transformed = self.transforms(image=image, mask=target)
            image = transformed['image']
            target = transformed['mask']

        resized_size = (28, 28)  # Model output grid size, 맞춰야 error: Target size (torch.Size([16 1 80 80])) must be the same as input size (torch.Size([16 1 28 28])) 해결
        target = cv2.resize(target, resized_size, interpolation=cv2.INTER_LINEAR)

        target = np.expand_dims(target, axis=0)  # Add channel dimension

        # Convert to tensor
        image = torch.from_numpy(image).permute(2, 0, 1).float() / 255.0
        target = torch.from_numpy(target).float()

        # Prepare metadata
        metadata = {
            'image_id': sample['image_id'],
            'colony_count': ann['colonies_number']  # Use correct English key
        }

        return image, target, metadata


def create_dataloader(data_root: str,
                        batch_size: int,
                        num_workers: int = 4,
                        transforms = None,
                        train: bool = True,
                        config: Optional[Union[Dict, Config]] = None,
                        cache_images: bool = False) -> DataLoader:
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
    logger.info("create_dataloader started")  # Add log
    logger.info(f"create_dataloader data_root: {data_root}")  # Add log
    dataset = ColonyDataset(data_root=data_root,
                            transforms=transforms,
                            train=train,
                            config=config,
                            cache_images=cache_images)
    logger.info("ColonyDataset created")  # Add log

    data_loader =  DataLoader(dataset,
                                batch_size=batch_size,
                                shuffle=train,
                                num_workers=num_workers,
                                 pin_memory=True,
                                 drop_last=False)  # DO NOT drop incomplete batches during training
    logger.info("DataLoader created")  # Add log
    logger.info("create_dataloader finished")  # Add log
    return data_loader
