"""
Image processing steps implementation
图像处理步骤实现
"""
import cv2
import numpy as np

def auto_brightness_contrast(image):
    """Auto adjust brightness and contrast"""
    # Convert to LAB color space
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    
    # Apply CLAHE to L channel
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
    cl = clahe.apply(l)
    
    # Merge channels
    limg = cv2.merge((cl,a,b))
    
    # Convert back to BGR
    return cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)

def auto_white_balance(image):
    """Auto white balance"""
    result = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    avg_a = np.average(result[:, :, 1])
    avg_b = np.average(result[:, :, 2])
    result[:, :, 1] = result[:, :, 1] - ((avg_a - 128) * (result[:, :, 0] / 255.0) * 1.1)
    result[:, :, 2] = result[:, :, 2] - ((avg_b - 128) * (result[:, :, 0] / 255.0) * 1.1)
    return cv2.cvtColor(result, cv2.COLOR_LAB2BGR)

def denoise(image, strength=10):
    """Denoise image"""
    return cv2.fastNlMeansDenoisingColored(image, None, strength, strength, 7, 21)

def sharpen(image, amount=1.0):
    """Sharpen image"""
    kernel = np.array([[-1,-1,-1],
                      [-1, 9,-1],
                      [-1,-1,-1]])
    return cv2.filter2D(image, -1, kernel * amount)

def color_balance(image):
    """Color balance"""
    r, g, b = cv2.split(image)
    r_avg = cv2.mean(r)[0]
    g_avg = cv2.mean(g)[0]
    b_avg = cv2.mean(b)[0]
    
    # Find the gain of each channel
    k = (r_avg + g_avg + b_avg) / 3
    kr = k / r_avg
    kg = k / g_avg
    kb = k / b_avg
    
    r = cv2.multiply(r, kr)
    g = cv2.multiply(g, kg)
    b = cv2.multiply(b, kb)
    
    return cv2.merge([b, g, r])

def auto_optimize(image):
    """Auto optimize image"""
    # Apply sequence of optimizations
    image = auto_brightness_contrast(image)
    image = auto_white_balance(image)
    image = denoise(image, strength=5)
    image = color_balance(image)
    image = sharpen(image, amount=0.5)
    return image

def default_optimize(image):
    """Default optimization"""
    # Apply basic optimizations
    image = auto_brightness_contrast(image)
    image = denoise(image, strength=3)
    return image
