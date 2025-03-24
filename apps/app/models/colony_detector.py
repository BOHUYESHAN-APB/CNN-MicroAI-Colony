"""
Colony detection model implementation
菌落检测模型实现
"""
import cv2
import numpy as np
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class ColonyDetector:
    """Colony detection model"""
    
    def __init__(self):
        self.initialized = False
        self.model = None
        
    def initialize(self):
        """Initialize the model"""
        try:
            # TODO: Load actual ML model
            self.initialized = True
            return True
        except Exception as e:
            logger.error(f"Model initialization failed: {str(e)}")
            return False
            
    def detect_colonies(self, image):
        """Detect colonies in image
        
        Args:
            image: Grayscale input image (CV_8UC1)
            
        Returns:
            List of detection dictionaries, or None if failed
        """
        try:
            # Ensure image is grayscale
            if len(image.shape) > 2:
                image = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
                
            # Simple blob detection for testing
            params = cv2.SimpleBlobDetector_Params()
            
            # Filter by area
            params.filterByArea = True
            params.minArea = 20
            params.maxArea = 500
            
            # Filter by circularity
            params.filterByCircularity = True
            params.minCircularity = 0.1
            
            # Filter by convexity
            params.filterByConvexity = True
            params.minConvexity = 0.87
            
            # Filter by inertia
            params.filterByInertia = True
            params.minInertiaRatio = 0.01
            
            # Create detector
            detector = cv2.SimpleBlobDetector_create(params)
            
            # Detect blobs
            keypoints = detector.detect(image)
            
            # Convert keypoints to detections
            detections = []
            for kp in keypoints:
                x, y = kp.pt
                r = kp.size / 2
                detection = {
                    "box": [int(x-r), int(y-r), int(x+r), int(y+r)],
                    "center": (int(x), int(y)),
                    "diameter": int(kp.size),
                    "confidence": float(kp.response if kp.response else 1.0)
                }
                detections.append(detection)
                
            return detections
            
        except Exception as e:
            logger.error(f"Colony detection failed: {str(e)}")
            return None
            
    def get_statistics(self, detections, image_shape, process_time=0.0):
        """Calculate detection statistics
        
        Args:
            detections: List of detection dictionaries
            image_shape: (height, width) of image
            process_time: Processing time in seconds
            
        Returns:
            Statistics dictionary
        """
        try:
            if not detections:
                return {
                    "count": 0,
                    "density": 0,
                    "avg_size": 0,
                    "min_size": 0, 
                    "max_size": 0,
                    "avg_confidence": 0,
                    "total_area": 0,
                    "process_time": process_time,
                    "parameters": self._get_current_parameters(),
                    "size_distribution": [],
                    "confidence_distribution": []
                }
                
            # Calculate basic statistics
            count = len(detections)
            image_area = image_shape[0] * image_shape[1]
            density = count / (image_area / 1000000)  # colonies per square mm
            
            # Size statistics
            sizes = [d["diameter"] for d in detections]
            avg_size = sum(sizes) / len(sizes)
            min_size = min(sizes)
            max_size = max(sizes)
            
            # Area statistics
            total_area = sum([(d["diameter"]/2)**2 * 3.14159 for d in detections])
            area_percentage = (total_area / image_area) * 100
            
            # Confidence statistics
            confidences = [d["confidence"] for d in detections]
            avg_confidence = sum(confidences) / len(confidences)
            
            # Size distribution (10 bins)
            size_hist, size_edges = np.histogram(sizes, bins=10)
            size_distribution = []
            for i in range(len(size_hist)):
                range_str = f"{int(size_edges[i])}-{int(size_edges[i+1])}px"
                size_distribution.append({
                    "range": range_str,
                    "count": int(size_hist[i])
                })
                
            # Confidence distribution (10 bins)
            conf_hist, conf_edges = np.histogram(confidences, bins=10, range=(0, 1))
            conf_distribution = []
            for i in range(len(conf_hist)):
                range_str = f"{conf_edges[i]:.1f}-{conf_edges[i+1]:.1f}"
                conf_distribution.append({
                    "range": range_str,
                    "count": int(conf_hist[i])
                })
            
            return {
                "count": count,
                "density": density,
                "avg_size": avg_size,
                "min_size": min_size,
                "max_size": max_size,
                "avg_confidence": avg_confidence,
                "total_area": total_area,
                "area_percentage": area_percentage,
                "process_time": process_time,
                "parameters": self._get_current_parameters(),
                "size_distribution": size_distribution,
                "confidence_distribution": conf_distribution
            }
            
        except Exception as e:
            logger.error(f"Error calculating statistics: {str(e)}")
            logger.debug("Error details:", exc_info=True)
            return None
            
    def _get_current_parameters(self):
        """Get current detection parameters"""
        return {
            "min_area": 20,
            "max_area": 500,
            "min_circularity": 0.1,
            "min_convexity": 0.87,
            "min_inertia_ratio": 0.01
        }
