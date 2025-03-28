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
        # Processing flags
        self.enable_processing = True  # Master switch for all processing
        
        # Glare removal
        self.remove_glare = True
        self.glare_threshold = 220
        
        # Normalization
        self.normalize = True
        self.norm_min = 0
        self.norm_max = 255
        
        # CLAHE
        self.clahe = True
        self.clahe_clip = 2.0
        self.clahe_grid = 8
        
        # Gaussian blur
        self.gaussian_blur = True
        self.blur_kernel = 5
        
        # Adaptive threshold
        self.adaptive_threshold = True
        self.block_size = 11
        self.c_value = 2
        
        # Edge detection
        self.edge_detection = False
        self.edge_type = 'canny'  # 'canny', 'sobel'
        self.canny_threshold1 = 100
        self.canny_threshold2 = 200
        self.sobel_dx = 1
        self.sobel_dy = 1
        self.sobel_ksize = 3
        
        # Morphological operations
        self.morphology = False
        self.morph_op = 'dilate'  # 'erode', 'dilate', 'open', 'close'
        self.morph_kernel = 3
        self.morph_iterations = 1
        
        # Auto optimization
        self.auto_optimize = False
        self.mask = None  # Will store the mask array
        
    @classmethod
    def from_dict(cls, config: Dict[str, Any]) -> 'PreprocessingConfig':
        """Create config from dictionary"""
        conf = cls()
        if config:
            if 'auto_optimize' in config:
                conf.auto_optimize = True
                # Auto-optimize parameters will be determined during processing
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
                conf.mask = config.get('mask', None)
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

def auto_optimize_params(image: np.ndarray) -> PreprocessingConfig:
    """Automatically optimize preprocessing parameters
    
    Args:
        image: Input image
        
    Returns:
        Optimized preprocessing configuration
    """
    config = PreprocessingConfig()
    
    # Convert to grayscale if needed
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    else:
        gray = image
        
    # Analyze image and set parameters
    mean_val = np.mean(gray)
    std_val = np.std(gray)
    
    # Adjust parameters based on image statistics
    if std_val < 30:  # Low contrast image
        config.clahe = True
        config.clahe_clip = 3.0
        config.clahe_grid = 8
    else:
        config.clahe = False
        
    if mean_val > 180:  # Bright image
        config.remove_glare = True
        config.glare_threshold = 200
    else:
        config.remove_glare = False
        
    config.gaussian_blur = True
    config.blur_kernel = 3 if std_val > 50 else 5
    
    return config

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
            
        # Auto-optimize parameters if requested
        if config.auto_optimize:
            config = auto_optimize_params(image)
            
        # Make a copy to avoid modifying original
        processed = image.copy()
            
        # Convert to grayscale
        if len(processed.shape) == 3:
            gray = cv2.cvtColor(processed, cv2.COLOR_RGB2GRAY)
        else:
            gray = processed
            
        # Apply mask if provided
        if config.mask is not None:
            # Ensure mask has same dimensions and type as image
            mask = config.mask.astype(gray.dtype)
            if mask.shape != gray.shape:
                mask = cv2.resize(mask, (gray.shape[1], gray.shape[0]))
            gray = cv2.multiply(gray, mask)
        
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
            
        # Edge detection
        if config.edge_detection and config.enable_processing:
            if config.edge_type == 'canny':
                gray = cv2.Canny(gray, config.canny_threshold1, config.canny_threshold2)
            elif config.edge_type == 'sobel':
                gray = cv2.Sobel(gray, cv2.CV_64F, config.sobel_dx, config.sobel_dy, ksize=config.sobel_ksize)
                gray = np.absolute(gray)
                gray = np.uint8(255 * gray / np.max(gray))
        
        # Morphological operations
        if config.morphology and config.enable_processing:
            kernel = np.ones((config.morph_kernel, config.morph_kernel), np.uint8)
            if config.morph_op == 'erode':
                gray = cv2.erode(gray, kernel, iterations=config.morph_iterations)
            elif config.morph_op == 'dilate':
                gray = cv2.dilate(gray, kernel, iterations=config.morph_iterations)
            elif config.morph_op == 'open':
                gray = cv2.morphologyEx(gray, cv2.MORPH_OPEN, kernel)
            elif config.morph_op == 'close':
                gray = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, kernel)
        
        # Convert back to RGB for display if needed
        if len(image.shape) == 3:
            processed = cv2.cvtColor(gray, cv2.COLOR_GRAY2RGB)
        else:
            processed = gray
            
        return processed if config.enable_processing else image.copy()
        
    except Exception as e:
        logger.error(f"Error preprocessing image: {str(e)}")
        logger.debug("Error details:", exc_info=True)
        return None
