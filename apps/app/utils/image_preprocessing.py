"""
Image preprocessing utilities
图像预处理工具
"""
import cv2
import numpy as np
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def load_image(path):
    """Load image in RGB format
    
    Args:
        path (str): Image file path
        
    Returns:
        numpy.ndarray: RGB image array, or None if failed
    """
    try:
        # Convert path to proper Path object
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

def preprocess_image(image):
    """Preprocess image for colony detection
    
    Args:
        image (numpy.ndarray): RGB image array
        
    Returns:
        numpy.ndarray: Preprocessed image
    """
    try:
        if image is None:
            return None
            
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        
        # Apply Gaussian blur
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Use adaptive thresholding
        thresh = cv2.adaptiveThreshold(
            blurred,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV,
            11,
            2
        )
        
        return thresh
        
    except Exception as e:
        logger.error(f"Error preprocessing image: {str(e)}")
        return None

def draw_detections(image, detections, color=(0, 255, 0)):
    """Draw colony detections on image
    
    Args:
        image (numpy.ndarray): RGB image to draw on
        detections (list): List of detection dictionaries
        color (tuple): RGB color for drawings
        
    Returns:
        numpy.ndarray: Image with detections drawn
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
