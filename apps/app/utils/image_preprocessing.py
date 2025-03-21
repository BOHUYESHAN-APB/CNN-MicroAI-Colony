"""
Image preprocessing utilities
图像预处理工具
"""
import cv2
import numpy as np
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class PreprocessingConfig:
    """Image preprocessing configuration"""
    
    def __init__(self):
        # Default parameters
        self.remove_glare = True
        self.glare_threshold = 220
        
        self.normalize = True
        self.norm_min = 0
        self.norm_max = 255
        
        self.clahe = True
        self.clahe_clip = 2.0
        self.clahe_grid = 8
        
        self.gaussian_blur = True
        self.blur_kernel = 5
        
        self.adaptive_threshold = True
        self.block_size = 11
        self.c_value = 2
        
    @classmethod
    def from_dict(cls, config: Dict[str, Any]) -> 'PreprocessingConfig':
        """Create config from dictionary"""
        conf = cls()
        if config:
            if 'auto_optimize' in config:
                # TODO: Implement auto parameter optimization
                pass
            else:
                conf.remove_glare = config.get('remove_glare', True)
                conf.glare_threshold = config.get('glare_threshold', 220)
                conf.normalize = config.get('normalize', True)
                conf.clahe = config.get('clahe', True)
                conf.clahe_clip = config.get('clahe_clip', 2.0)
                conf.clahe_grid = config.get('clahe_grid', 8)
                conf.gaussian_blur = config.get('gaussian_blur', True)
                conf.blur_kernel = config.get('blur_kernel', 5)
                conf.adaptive_threshold = config.get('adaptive_threshold', True)
                conf.block_size = config.get('block_size', 11)
                conf.c_value = config.get('c_value', 2)
        return conf

def load_image(path: str) -> Optional[np.ndarray]:
    """Load image in RGB format
    
    Args:
        path: Image file path
        
    Returns:
        RGB image array, or None if failed
    """
    try:
        # Convert path to Path object
        img_path = Path(path)
        
        # Read image using numpy to handle Unicode paths
        with open(img_path, 'rb') as f:
            img_array = np.frombuffer(f.read(), dtype=np.uint8)
            image = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
            
        if image is None:
            logger.error(f"Failed to load image: {path}")
            return None
            
        # Convert to RGB
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        return image
        
    except Exception as e:
        logger.error(f"Error loading image {path}: {str(e)}")
        return None

def preprocess_image(image: np.ndarray, config: Optional[PreprocessingConfig] = None) -> Optional[np.ndarray]:
    """Preprocess image for colony detection
    
    Args:
        image: RGB input image
        config: Optional preprocessing configuration
        
    Returns:
        Preprocessed image
    """
    try:
        if image is None:
            return None
            
        # Use default config if none provided
        if config is None:
            config = PreprocessingConfig()
            
        # Make a copy to avoid modifying original
        processed = image.copy()
            
        # Convert to grayscale
        if len(processed.shape) == 3:
            gray = cv2.cvtColor(processed, cv2.COLOR_RGB2GRAY)
        else:
            gray = processed
        
        # Remove glare
        if config.remove_glare:
            mask = gray < config.glare_threshold
            gray = cv2.multiply(gray, mask.astype(gray.dtype))
            
        # Normalize lighting
        if config.normalize:
            gray = cv2.normalize(
                gray, 
                None,
                config.norm_min,
                config.norm_max,
                cv2.NORM_MINMAX
            )
            
        # Apply CLAHE
        if config.clahe:
            clahe = cv2.createCLAHE(
                clipLimit=config.clahe_clip,
                tileGridSize=(config.clahe_grid, config.clahe_grid)
            )
            gray = clahe.apply(gray)
            
        # Apply Gaussian blur
        if config.gaussian_blur:
            kernel_size = config.blur_kernel
            if kernel_size % 2 == 0:
                kernel_size += 1  # Must be odd
            gray = cv2.GaussianBlur(gray, (kernel_size, kernel_size), 0)
            
        # Apply adaptive threshold
        if config.adaptive_threshold:
            block_size = config.block_size
            if block_size % 2 == 0:
                block_size += 1  # Must be odd
            gray = cv2.adaptiveThreshold(
                gray,
                255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY_INV,
                block_size,
                config.c_value
            )
            
        # Convert back to RGB for display if needed
        if len(image.shape) == 3:
            processed = cv2.cvtColor(gray, cv2.COLOR_GRAY2RGB)
        else:
            processed = gray
            
        return processed
        
    except Exception as e:
        logger.error(f"Error preprocessing image: {str(e)}")
        logger.debug("Error details:", exc_info=True)
        return None

def draw_detections(image: np.ndarray, detections: list, color: tuple = (0, 255, 0)) -> Optional[np.ndarray]:
    """Draw colony detections on image
    
    Args:
        image: RGB image to draw on
        detections: List of detection dictionaries
        color: RGB color for drawings
        
    Returns:
        Image with detections drawn
    """
    try:
        if image is None:
            return None
            
        # Make copy for drawing
        result = image.copy()
        
        # Draw each detection
        for det in detections:
            # Get detection info
            box = det.get("box", [0, 0, 0, 0])
            center = det.get("center", (0, 0))
            diameter = det.get("diameter", 0)
            confidence = det.get("confidence", 0)
            
            # Draw bounding box
            cv2.rectangle(result,
                         (int(box[0]), int(box[1])),
                         (int(box[2]), int(box[3])),
                         color, 2)
            
            # Draw center point and circle
            cv2.circle(result, 
                      (int(center[0]), int(center[1])),
                      3, color, -1)
            cv2.circle(result,
                      (int(center[0]), int(center[1])),
                      int(diameter/2), color, 2)
            
            # Add confidence text
            cv2.putText(result,
                       f"{confidence:.2f}",
                       (int(box[0]), int(box[1]-5)),
                       cv2.FONT_HERSHEY_SIMPLEX,
                       0.6, color, 2)
                       
        return result
        
    except Exception as e:
        logger.error(f"Error drawing detections: {str(e)}")
        return image
