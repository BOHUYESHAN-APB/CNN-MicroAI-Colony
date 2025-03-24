"""
Image data class implementation
图像数据类实现
"""
import cv2
import numpy as np

class ImageData:
    """Container for image data and metadata"""
    
    def __init__(self, image, path=None):
        """Initialize image data
        
        Args:
            image: OpenCV image (numpy array)
            path: Image file path
        """
        self.image = image
        self.path = path
        self.preprocessing_config = None
        self.detections = None
        
    @property
    def width(self):
        """Get image width"""
        return self.image.shape[1] if self.image is not None else 0
        
    @property
    def height(self):
        """Get image height"""
        return self.image.shape[0] if self.image is not None else 0
        
    @property
    def channels(self):
        """Get number of image channels"""
        return self.image.shape[2] if self.image is not None else 0
        
    def clone(self):
        """Create a deep copy"""
        image_copy = self.image.copy() if self.image is not None else None
        copy = ImageData(image_copy, self.path)
        return copy
    
    def resize(self, width=None, height=None, scale=None, interpolation=cv2.INTER_AREA):
        """Resize image
        
        Args:
            width: Target width
            height: Target height
            scale: Scale factor (overrides width/height)
            interpolation: OpenCV interpolation method
            
        Returns:
            Resized image data
        """
        if self.image is None:
            return None
        
        if scale is not None:
            width = int(self.width * scale)
            height = int(self.height * scale)
        elif width is None or height is None:
            return None
            
        resized = cv2.resize(self.image, (width, height), interpolation=interpolation)
        return ImageData(resized, self.path)
        
    def apply_preprocessing(self, config=None):
        """Apply preprocessing config
        
        Args:
            config: PreprocessingConfig instance
            
        Returns:
            Preprocessed image data
        """
        if config is None:
            config = self.preprocessing_config
            
        if config is None or self.image is None:
            return self.clone()
            
        result = config.apply(self.image)
        processed = ImageData(result, self.path)
        processed.preprocessing_config = config
        return processed
            
    def to_rgb(self):
        """Convert to RGB format
        
        Returns:
            RGB image data
        """
        if self.image is None:
            return None
            
        rgb = cv2.cvtColor(self.image, cv2.COLOR_BGR2RGB)
        return ImageData(rgb, self.path)
        
    def to_bgr(self):
        """Convert to BGR format
        
        Returns:
            BGR image data
        """
        if self.image is None:
            return None
            
        bgr = cv2.cvtColor(self.image, cv2.COLOR_RGB2BGR)
        return ImageData(bgr, self.path)
        
    def to_grayscale(self):
        """Convert to grayscale
        
        Returns:
            Grayscale image data
        """
        if self.image is None:
            return None
            
        gray = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
        return ImageData(gray, self.path)
