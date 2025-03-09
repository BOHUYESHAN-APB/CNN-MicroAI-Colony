"""
Colony Detection Core
"""
import cv2
import numpy as np
import logging
from typing import Dict, List, Any, Optional
from time import time
from pathlib import Path

logger = logging.getLogger(__name__)

class ColonyDetector:
    """Colony detection and analysis"""
    
    def __init__(self):
        self._min_size = 5
        self._max_size = 100
        self._confidence = 0.5
        self._use_gpu = False
        
    def analyze(self, image_path: str, **kwargs) -> Dict[str, Any]:
        """Analyze image for colonies
        
        Args:
            image_path: Path to image file
            **kwargs: Analysis parameters
                confidence: Detection confidence threshold (0-1)
                min_size: Minimum colony size in pixels
                max_size: Maximum colony size in pixels
                use_gpu: Use GPU acceleration if available
                
        Returns:
            Dictionary containing:
                colonies: List of detected colonies
                    [{"x": x, "y": y, "radius": r, "confidence": conf}, ...]
                count: Total colony count
                density: Colony density (colonies per unit area)
                area: Total colony area coverage
                time: Processing time in seconds
        """
        start_time = time()
        
        # Get parameters
        self._confidence = kwargs.get('confidence', 0.5)
        self._min_size = kwargs.get('min_size', 5)
        self._max_size = kwargs.get('max_size', 100)
        self._use_gpu = kwargs.get('use_gpu', False)
        
        try:
            # Read image
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"Failed to read image: {image_path}")
                
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Apply Gaussian blur
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            
            # Adaptive thresholding
            thresh = cv2.adaptiveThreshold(
                blurred,
                255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY_INV,
                11,
                2
            )
            
            # Find contours
            contours, _ = cv2.findContours(
                thresh,
                cv2.RETR_EXTERNAL,
                cv2.CHAIN_APPROX_SIMPLE
            )
            
            # Process colonies
            colonies = []
            total_area = 0
            
            for contour in contours:
                # Get bounding circle
                (x, y), radius = cv2.minEnclosingCircle(contour)
                radius = int(radius)
                
                # Filter by size
                if not (self._min_size <= radius * 2 <= self._max_size):
                    continue
                    
                # Calculate circularity
                area = cv2.contourArea(contour)
                perimeter = cv2.arcLength(contour, True)
                circularity = 4 * np.pi * area / (perimeter * perimeter)
                
                # Filter by shape
                if circularity < 0.7:  # Not circular enough
                    continue
                    
                # Calculate confidence based on shape metrics
                confidence = min(circularity, 1.0)
                
                # Add if confidence threshold met
                if confidence >= self._confidence:
                    colonies.append({
                        "x": int(x),
                        "y": int(y),
                        "radius": radius,
                        "confidence": float(confidence)
                    })
                    total_area += area
                    
            # Calculate metrics
            image_area = gray.shape[0] * gray.shape[1]
            density = len(colonies) / (image_area / 1000000)  # per mm²
            area_coverage = total_area / image_area
            
            # Prepare results
            results = {
                "colonies": colonies,
                "count": len(colonies),
                "density": density,
                "area": area_coverage,
                "time": time() - start_time
            }
            
            return results
            
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            raise
