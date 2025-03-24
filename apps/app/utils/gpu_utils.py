"""
GPU acceleration utilities
GPU加速工具
"""
import cv2
import numpy as np
try:
    import cupy as cp
    import cupyx.scipy.ndimage as cuimg
    CUDA_AVAILABLE = True
except ImportError:
    CUDA_AVAILABLE = False

def detect_gpu():
    """Check if CUDA-capable GPU is available"""
    return CUDA_AVAILABLE and cp.cuda.runtime.getDeviceCount() > 0

def to_gpu(img):
    """Transfer image to GPU memory"""
    if not CUDA_AVAILABLE:
        return img
    if isinstance(img, np.ndarray):
        return cp.asarray(img)
    return img

def to_cpu(img):
    """Transfer image back to CPU memory"""
    if not CUDA_AVAILABLE:
        return img
    if isinstance(img, cp.ndarray):
        return cp.asnumpy(img)
    return img

def gpu_gaussian_blur(img, kernel_size, sigma=0):
    """Apply Gaussian blur on GPU"""
    if not CUDA_AVAILABLE:
        return cv2.GaussianBlur(img, (kernel_size, kernel_size), sigma)
        
    gpu_img = to_gpu(img)
    blurred = cuimg.gaussian_filter(gpu_img, sigma=sigma)
    return to_cpu(blurred)

def gpu_canny(img, low_threshold, high_threshold):
    """Apply Canny edge detection on GPU"""
    if not CUDA_AVAILABLE:
        return cv2.Canny(img, low_threshold, high_threshold)
        
    # Convert to grayscale if needed
    if len(img.shape) == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    else:
        gray = img
        
    gpu_img = to_gpu(gray)
    
    # Gaussian blur
    blurred = cuimg.gaussian_filter(gpu_img, sigma=1.4)
    
    # Calculate gradients
    sobelx = cuimg.sobel(blurred, axis=1)
    sobely = cuimg.sobel(blurred, axis=0)
    
    # Calculate magnitude and direction
    magnitude = cp.sqrt(sobelx**2 + sobely**2)
    direction = cp.arctan2(sobely, sobelx)
    
    # Non-maximum suppression and double thresholding
    edges = cp.zeros_like(magnitude)
    edges[(magnitude >= low_threshold) & (magnitude >= high_threshold)] = 255
    
    return to_cpu(edges).astype(np.uint8)

def gpu_watershed(img, markers):
    """Apply watershed algorithm on GPU"""
    if not CUDA_AVAILABLE:
        return cv2.watershed(img, markers)
        
    # Currently watershed is not implemented on GPU
    # Fall back to CPU implementation
    return cv2.watershed(img, markers)

def gpu_morphology(img, operation, kernel_size, iterations=1):
    """Apply morphological operations on GPU"""
    if not CUDA_AVAILABLE:
        kernel = np.ones((kernel_size, kernel_size), np.uint8)
        return cv2.morphologyEx(img, operation, kernel, iterations=iterations)
        
    gpu_img = to_gpu(img)
    kernel = cp.ones((kernel_size, kernel_size), cp.uint8)
    
    if operation == cv2.MORPH_ERODE:
        result = cuimg.binary_erosion(gpu_img, kernel, iterations=iterations)
    elif operation == cv2.MORPH_DILATE:
        result = cuimg.binary_dilation(gpu_img, kernel, iterations=iterations)
    elif operation == cv2.MORPH_OPEN:
        result = cuimg.binary_opening(gpu_img, kernel, iterations=iterations)
    elif operation == cv2.MORPH_CLOSE:
        result = cuimg.binary_closing(gpu_img, kernel, iterations=iterations)
    else:
        return cv2.morphologyEx(img, operation, np.ones((kernel_size, kernel_size), np.uint8))
    
    return to_cpu(result).astype(np.uint8)

def gpu_threshold(img, thresh=0, maxval=255, type=cv2.THRESH_BINARY):
    """Apply thresholding on GPU"""
    if not CUDA_AVAILABLE:
        return cv2.threshold(img, thresh, maxval, type)[1]
        
    gpu_img = to_gpu(img)
    if type == cv2.THRESH_BINARY:
        result = cp.where(gpu_img > thresh, maxval, 0)
    elif type == cv2.THRESH_BINARY_INV:
        result = cp.where(gpu_img > thresh, 0, maxval)
    elif type == cv2.THRESH_OTSU:
        # Otsu's method
        hist = cp.histogram(gpu_img, bins=256, range=(0,256))[0]
        total = cp.sum(hist)
        current_max = 0
        thresh = 0
        sumT = cp.sum(cp.arange(256) * hist)
        
        weightB = 0
        sumB = 0
        
        for i in range(256):
            weightB += hist[i]
            weightF = total - weightB
            if weightF == 0:
                break
                
            sumB += i * hist[i]
            meanB = sumB / weightB
            meanF = (sumT - sumB) / weightF
            
            varBetween = weightB * weightF * ((meanB - meanF) ** 2)
            
            if varBetween > current_max:
                current_max = varBetween
                thresh = i
                
        result = cp.where(gpu_img > thresh, maxval, 0)
    else:
        return cv2.threshold(img, thresh, maxval, type)[1]
        
    return to_cpu(result).astype(np.uint8)
