"""
Image preprocessing utilities
图像预处理工具
"""
import cv2
import numpy as np

def load_image(image_path):
    """Load image from path, supports Chinese characters
    
    Args:
        image_path: Path to image file
        
    Returns:
        numpy.ndarray: Image data or None if failed
    """
    try:
        with open(image_path, 'rb') as f:
            image_bytes = bytearray(f.read())
            image_array = np.asarray(image_bytes, dtype=np.uint8)
            image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
            return image
    except Exception as e:
        print(f"Error loading image: {str(e)}")
        return None

def preprocess_image(image):
    """Apply basic preprocessing to image
    
    Args:
        image: numpy.ndarray, input image
        
    Returns:
        numpy.ndarray: Preprocessed image
    """
    # Convert to RGB
    if len(image.shape) == 2:  # Grayscale
        image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    elif image.shape[2] == 4:  # RGBA
        image = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
        
    return image
