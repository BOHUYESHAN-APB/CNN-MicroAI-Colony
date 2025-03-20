"""
Image preprocessing utilities for colony detection
"""
import cv2
import numpy as np
import logging

logger = logging.getLogger(__name__)

def find_petri_dish(image):
    """
    Detect the petri dish circle in the image and create a mask.
    
    Args:
        image (numpy.ndarray): Input image
        
    Returns:
        tuple: (mask, circle_params) where mask is binary mask and 
               circle_params is (x, y, radius) or None if no dish detected
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (9, 9), 2)
    
    circles = cv2.HoughCircles(
        blurred,
        cv2.HOUGH_GRADIENT,
        dp=1,
        minDist=max(gray.shape) // 2,
        param1=50,
        param2=30,
        minRadius=min(gray.shape) // 4,
        maxRadius=min(gray.shape) // 2
    )
    
    mask = np.zeros_like(gray)
    circle_params = None
    
    if circles is not None:
        circles = np.uint16(np.around(circles))
        x, y, r = circles[0][0]
        cv2.circle(mask, (x, y), r, 255, -1)
        circle_params = (x, y, r)
        
    return mask, circle_params

def remove_glare(image, threshold=220):
    """
    Remove glare from image by inpainting bright regions.
    
    Args:
        image (numpy.ndarray): Input image
        threshold (int): Brightness threshold (0-255)
        
    Returns:
        numpy.ndarray: Image with reduced glare
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, mask = cv2.threshold(gray, threshold, 255, cv2.THRESH_BINARY)
    kernel = np.ones((5,5), np.uint8)
    mask = cv2.dilate(mask, kernel, iterations=1)
    return cv2.inpaint(image, mask, 3, cv2.INPAINT_TELEA)

def normalize_lighting(image, mask=None):
    """
    Normalize lighting in the image, optionally within a mask area.
    
    Args:
        image (numpy.ndarray): Input image
        mask (numpy.ndarray): Optional binary mask
        
    Returns:
        numpy.ndarray: Lighting normalized image
    """
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    
    clahe = cv2.createCLAHE(clipLimit=4.0, tileGridSize=(16, 16))
    cl = clahe.apply(l)
    
    min_val = np.min(cl)
    max_val = np.max(cl)
    cl = np.clip(((cl - min_val) * (255.0/(max_val - min_val))), 0, 255).astype(np.uint8)
    
    if mask is not None:
        cl = cv2.bitwise_and(cl, cl, mask=mask)
        l = cv2.bitwise_and(l, l, mask=mask)
        
    limg = cv2.merge((cl, a, b))
    normalized = cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)
    
    if mask is not None:
        mask_inv = cv2.bitwise_not(mask)
        bg = cv2.bitwise_and(image, image, mask=mask_inv)
        normalized = cv2.add(bg, normalized)
    
    return normalized

def clahe(image, clip_limit=2.0, tile_grid_size=(8, 8)):
    """
    Apply Contrast Limited Adaptive Histogram Equalization.
    
    Args:
        image (numpy.ndarray): Input image
        clip_limit (float): Contrast limit for CLAHE
        tile_grid_size (tuple): Size of grid for histogram equalization
        
    Returns:
        numpy.ndarray: CLAHE enhanced image
    """
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    
    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid_size)
    cl = clahe.apply(l)
    
    limg = cv2.merge((cl, a, b))
    return cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)

def gaussian_blur(image, kernel_size=5):
    """
    Apply Gaussian blur for noise reduction.
    
    Args:
        image (numpy.ndarray): Input image
        kernel_size (int): Size of Gaussian kernel
        
    Returns:
        numpy.ndarray: Blurred image
    """
    return cv2.GaussianBlur(image, (kernel_size, kernel_size), 0)

def adaptive_thresholding(image, block_size=11, C=2):
    """
    Apply adaptive thresholding.
    
    Args:
        image (numpy.ndarray): Input image
        block_size (int): Size of pixel neighborhood for thresholding
        C (int): Constant subtracted from mean
        
    Returns:
        numpy.ndarray: Thresholded image
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        block_size,
        C
    )

def morphological_operations(image, operation='open', kernel_size=5):
    """
    Apply morphological operations to the image.
    
    Args:
        image (numpy.ndarray): Input image
        operation (str): Operation type ('open', 'close', 'dilate', 'erode')
        kernel_size (int): Size of the structuring element
        
    Returns:
        numpy.ndarray: Processed image
    """
    kernel = np.ones((kernel_size, kernel_size), np.uint8)
    if operation == 'open':
        return cv2.morphologyEx(image, cv2.MORPH_OPEN, kernel)
    elif operation == 'close':
        return cv2.morphologyEx(image, cv2.MORPH_CLOSE, kernel)
    elif operation == 'dilate':
        return cv2.dilate(image, kernel)
    elif operation == 'erode':
        return cv2.erode(image, kernel)
    else:
        raise ValueError(f"Unknown operation: {operation}")

def watershed_segmentation(image):
    """
    Apply watershed segmentation to separate overlapping colonies.
    
    Args:
        image (numpy.ndarray): Input image
        
    Returns:
        numpy.ndarray: Segmented image
    """
    # Convert to grayscale if needed
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()
    
    # Apply thresholding
    ret, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    
    # Noise removal
    kernel = np.ones((3,3), np.uint8)
    opening = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=2)
    
    # Sure background
    sure_bg = cv2.dilate(opening, kernel, iterations=3)
    
    # Finding sure foreground
    dist_transform = cv2.distanceTransform(opening, cv2.DIST_L2, 5)
    ret, sure_fg = cv2.threshold(dist_transform, 0.7*dist_transform.max(), 255, 0)
    
    sure_fg = np.uint8(sure_fg)
    unknown = cv2.subtract(sure_bg, sure_fg)
    
    # Marker labelling
    ret, markers = cv2.connectedComponents(sure_fg)
    markers = markers + 1
    markers[unknown==255] = 0
    
    markers = cv2.watershed(cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR), markers)
    return markers

def optimize_parameters(image):
    """
    Automatically optimize preprocessing parameters based on image analysis.
    
    Args:
        image (numpy.ndarray): Input image
        
    Returns:
        dict: Optimized parameters
    """
    # Calculate image statistics
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
    mean_val = np.mean(gray)
    std_val = np.std(gray)
    laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
    
    # Fast colony detection for density estimation
    thresh = cv2.threshold(gray, mean_val, 255, cv2.THRESH_BINARY)[1]
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    density = len(contours) / (image.shape[0] * image.shape[1])
    
    # Optimize parameters based on image characteristics
    params = {
        'remove_glare': True,
        'normalize_lighting': True,
        'clahe': True,
        'gaussian_blur': False,
        'adaptive_thresholding': False,
        'glare_threshold': min(220, mean_val + 2*std_val),
        'clahe_clip_limit': 2.0 + (std_val / 128.0),
        'clahe_grid_size': int(8 + (16 * density)),
        'blur_kernel_size': 3 if laplacian_var > 500 else 5,
        'adaptive_thresh_block_size': int(11 + (20 * density)),
        'adaptive_thresh_c': 2 + int(std_val / 32.0)
    }
    
    return params

def canny_edge_detection(image, low_threshold=100, high_threshold=200):
    """
    Apply Canny edge detection.
    
    Args:
        image (numpy.ndarray): Input image
        low_threshold (int): Lower threshold for edge detection
        high_threshold (int): Higher threshold for edge detection
        
    Returns:
        numpy.ndarray: Edge image
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    return cv2.Canny(blurred, low_threshold, high_threshold)

def load_image(file_path):
    """Load image with OpenCV handling Unicode paths"""
    try:
        # Read file bytes and decode
        with open(file_path, 'rb') as f:
            buffer = f.read()
        array = np.frombuffer(buffer, dtype=np.uint8)
        image = cv2.imdecode(array, cv2.IMREAD_COLOR)
        
        if image is None:
            raise ValueError("Invalid image data or format")
        return image
    except Exception as e:
        logger.error(f"Error loading image: {str(e)}")
        logger.debug(f"Attempted path: {file_path}", exc_info=True)
        raise

def preprocess_image(image, config=None, auto_optimize=False):
    """
    Apply preprocessing steps to image with support for default, manual, and auto modes.
    
    Args:
        image (numpy.ndarray): Input image
        config (dict): Manual preprocessing configuration (optional)
        auto_optimize (bool): Whether to use automatic parameter optimization
        
    Returns:
        tuple: (processed_image, mask, circle_params, config)
            - processed_image: Preprocessed image
            - mask: Petri dish mask or None
            - circle_params: (x, y, radius) of petri dish or None
            - config: Dictionary of parameters actually used
    """
    # Default configuration
    default_config = {
        "remove_glare": True,
        "normalize_lighting": True,
        "clahe": True,
        "gaussian_blur": False,
        "adaptive_thresholding": False,
        "morphological_op": None,
        "watershed": False,
        "glare_threshold": 220,
        "clahe_clip_limit": 2.0,
        "clahe_grid_size": 8,
        "blur_kernel_size": 5,
        "adaptive_thresh_block_size": 11,
        "adaptive_thresh_c": 2,
        "morph_kernel_size": 5
    }
    
    # Determine which configuration to use
    if auto_optimize:
        config = optimize_parameters(image)
    elif config is None:
        config = default_config
    
    # Find petri dish
    mask, circle_params = find_petri_dish(image)
    processed = image.copy()
    
    try:
        # Apply enabled preprocessing steps
        if config.get("remove_glare", True):
            processed = remove_glare(processed, config.get("glare_threshold", 220))
            
        if config.get("normalize_lighting", True):
            processed = normalize_lighting(processed, mask if circle_params else None)
            
        if config.get("clahe", True):
            clip_limit = config.get("clahe_clip_limit", 2.0)
            grid_size = config.get("clahe_grid_size", 8)
            processed = clahe(processed, clip_limit, (grid_size, grid_size))
            
        if config.get("gaussian_blur", False):
            kernel = config.get("blur_kernel_size", 5)
            processed = gaussian_blur(processed, kernel)
            
        if config.get("morphological_op"):
            kernel_size = config.get("morph_kernel_size", 5)
            processed = morphological_operations(processed, 
                                              config["morphological_op"], 
                                              kernel_size)
            
        if config.get("watershed", False):
            markers = watershed_segmentation(processed)
            processed = cv2.applyColorMap((markers * 255 / markers.max()).astype(np.uint8), 
                                        cv2.COLORMAP_JET)
            
        if config.get("adaptive_thresholding", False):
            block_size = config.get("adaptive_thresh_block_size", 11)
            c = config.get("adaptive_thresh_c", 2)
            processed = adaptive_thresholding(processed, block_size, c)
            
    except Exception as e:
        logger.error(f"Error during image preprocessing: {str(e)}")
        return image, None, None
        
    return processed, mask, circle_params
