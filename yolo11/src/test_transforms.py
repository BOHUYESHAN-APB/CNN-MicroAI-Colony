import os
import sys
import warnings
import cv2
import numpy as np
import albumentations as A
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f'transform_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)
logger = logging.getLogger(__name__)

# Set up warning capture
warnings.filterwarnings('always')
warnings.simplefilter('always')

def test_individual_transform(name, transform, image, mask=None):
    logger.info(f"\nTesting {name}...")
    try:
        kwargs = {'image': image}
        if mask is not None:
            kwargs['mask'] = mask
        result = transform(**kwargs)
        logger.info(f"{name} successful")
        logger.debug(f"{name} result shapes: {[v.shape for v in result.values()]}")
        return True
    except Exception as e:
        logger.error(f"{name} failed: {str(e)}")
        logger.error("Stack trace:", exc_info=True)
        return False

def main():
    logger.info("System Information:")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Albumentations version: {A.__version__}")
    logger.info(f"OpenCV version: {cv2.__version__}")
    logger.info(f"Current directory: {os.getcwd()}")
    logger.info(f"PYTHONPATH: {os.getenv('PYTHONPATH')}")
    
    logger.info("\nPython path:")
    for p in sys.path:
        logger.info(f"  {p}")
    
    try:
        logger.info("\nCreating test data...")
        input_size = 640
        image = np.random.randint(0, 255, (1024, 1024, 3), dtype=np.uint8)
        mask = np.zeros((1024, 1024), dtype=np.float32)
        logger.info(f"Created test image shape: {image.shape}")
        logger.info(f"Created test mask shape: {mask.shape}")
        
        # Test individual transforms
        transforms_to_test = [
            ('RandomResizedCrop', A.RandomResizedCrop(
                height=input_size,
                width=input_size,
                scale=(0.7, 1.0),
                ratio=(0.8, 1.2),
                p=1.0
            )),
            ('ShiftScaleRotate', A.ShiftScaleRotate(
                shift_limit=0.1,
                scale_limit=0.2,
                rotate_limit=45,
                p=1.0
            )),
            ('Normalize', A.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225],
                max_pixel_value=255.0,
                p=1.0
            ))
        ]
        
        for name, transform in transforms_to_test:
            test_individual_transform(name, transform, image, mask)
        
        # Test full pipeline
        logger.info("\nTesting full transform pipeline...")
        logger.info("Importing transforms module...")
        from utils.transforms import get_train_transforms, get_val_transforms
        
        logger.info("\nCreating train transforms...")
        train_transforms = get_train_transforms(input_size=input_size)
        logger.info("Train transforms created successfully")
        logger.debug(f"Train transforms config: {train_transforms}")
        
        logger.info("\nApplying train transforms...")
        transformed = train_transforms(image=image, mask=mask)
        logger.info("Train transforms applied successfully")
        logger.info(f"Transformed image shape: {transformed['image'].shape}")
        logger.info(f"Transformed mask shape: {transformed['mask'].shape}")
        
    except Exception as e:
        logger.error(f"Error occurred: {str(e)}", exc_info=True)
        raise

if __name__ == '__main__':
    with warnings.catch_warnings(record=True) as w:
        try:
            main()
            if len(w) > 0:
                logger.warning("\nWarnings caught:")
                for warning in w:
                    logger.warning(f"  {warning.message}")
        except Exception as e:
            logger.error("Test failed", exc_info=True)
