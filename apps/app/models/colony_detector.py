"""
Colony detection model implementation
菌落检测模型实现
"""
import cv2
import numpy as np
import logging
from ..utils.image_preprocessing import preprocess_image

logger = logging.getLogger(__name__)

class ColonyDetector:
    """Colony detection and analysis"""
    
    def __init__(self):
        self.initialized = False
        
    def initialize(self):
        """Initialize detector"""
        # TODO: Load actual ML model
        self.initialized = True
        return True
        
    def detect_colonies(self, image):
        """Detect colonies in image
        
        Args:
            image (numpy.ndarray): RGB input image
            
        Returns:
            list: List of detection dictionaries
        """
        try:
            # Preprocess image
            processed = preprocess_image(image)
            if processed is None:
                return None
                
            # Find contours
            contours, _ = cv2.findContours(
                processed,
                cv2.RETR_EXTERNAL,
                cv2.CHAIN_APPROX_SIMPLE
            )
            
            # Filter and analyze contours
            detections = []
            min_size = 5  # Minimum diameter in pixels
            max_size = 100  # Maximum diameter in pixels
            
            for contour in contours:
                try:
                    # Get bounding circle
                    (x, y), radius = cv2.minEnclosingCircle(contour)
                    diameter = radius * 2
                    
                    # Filter by size
                    if diameter < min_size or diameter > max_size:
                        continue
                        
                    # Calculate circularity safely
                    area = cv2.contourArea(contour)
                    circle_area = np.pi * radius * radius
                    
                    # Avoid division by zero
                    if area <= 0 or circle_area <= 0:
                        continue
                        
                    # Calculate circularity (1.0 means perfect circle)
                    area_ratio = area / circle_area
                    if area_ratio > 1:
                        circularity = circle_area / area
                    else:
                        circularity = area_ratio
                        
                    # Filter by circularity
                    if circularity < 0.6:  # Threshold for circular shape
                        continue
                    
                    # Create bounding box
                    x1 = int(x - radius)
                    y1 = int(y - radius)
                    x2 = int(x + radius)
                    y2 = int(y + radius)
                    
                    # Add detection
                    detection = {
                        "box": [x1, y1, x2, y2],
                        "center": (x, y),
                        "diameter": diameter,
                        "confidence": circularity,
                        "area": area
                    }
                    detections.append(detection)
                    
                except Exception as e:
                    logger.debug(f"Skipped invalid contour: {str(e)}")
                    continue
            
            return detections
            
        except Exception as e:
            logger.error(f"Colony detection failed: {str(e)}")
            return None
            
    def get_statistics(self, detections, image_shape):
        """Calculate detection statistics
        
        Args:
            detections (list): List of detection dictionaries
            image_shape (tuple): Image height and width
            
        Returns:
            dict: Statistics dictionary
        """
        try:
            if not detections:
                return {
                    "count": 0,
                    "avg_size": 0.0,
                    "min_size": 0.0,
                    "max_size": 0.0,
                    "avg_confidence": 0.0,
                    "total_area": 0.0,
                    "density": 0.0,
                    "size_distribution": []
                }
                
            # Basic statistics
            count = len(detections)
            sizes = [d["diameter"] for d in detections]
            areas = [d["area"] for d in detections]
            confidences = [d["confidence"] for d in detections]
            
            # Calculate statistics safely
            avg_size = float(np.mean(sizes))
            min_size = float(np.min(sizes))
            max_size = float(np.max(sizes))
            avg_confidence = float(np.mean(confidences))
            total_area = float(sum(areas))
            
            # Calculate density (colonies per cm²)
            # Assuming standard petri dish size (90mm diameter)
            dish_diameter_mm = 90.0
            dish_area_cm2 = np.pi * (dish_diameter_mm/20)**2  # Convert to cm²
            density = count / max(dish_area_cm2, 1)  # Avoid division by zero
            
            # Calculate size distribution safely
            if sizes:
                bins = min(10, len(sizes))  # Adjust bins based on data size
                hist, edges = np.histogram(sizes, bins=bins)
                size_dist = [
                    {"range": f"{edges[i]:.1f}-{edges[i+1]:.1f}", "count": int(hist[i])}
                    for i in range(bins) if hist[i] > 0
                ]
            else:
                size_dist = []
            
            return {
                "count": count,
                "avg_size": avg_size,
                "min_size": min_size,
                "max_size": max_size,
                "avg_confidence": avg_confidence,
                "total_area": total_area,
                "density": density,
                "size_distribution": size_dist
            }
            
        except Exception as e:
            logger.error(f"Failed to calculate statistics: {str(e)}")
            return None
