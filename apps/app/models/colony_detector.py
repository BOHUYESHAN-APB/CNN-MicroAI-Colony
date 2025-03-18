"""
Colony detection implementation
菌落检测实现
"""
import os
import cv2
import torch
import logging
import numpy as np
from torchvision.transforms import functional as F
from ..utils.image_preprocessing import preprocess_image

logger = logging.getLogger(__name__)

def create_model(model_type="faster_rcnn"):
    """Create colony detection model"""
    return FasterRCNNColonyDetectionModel()

class FasterRCNNColonyDetectionModel:
    """Colony detection using Faster R-CNN model"""
    
    def __init__(self):
        self.model = None
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
    def load_model(self):
        """Load the model from checkpoint"""
        if self.model is None:
            # TODO: Load actual model
            # For now just create a dummy model
            self.model = True
            
    def detect(self, image_path, preprocess_config=None, auto_optimize=False):
        """
        Detect colonies in image
        
        Args:
            image_path (str): Path to image file
            preprocess_config (dict): Preprocessing configuration
            auto_optimize (bool): Whether to auto optimize parameters
            
        Returns:
            dict: Detection results
        """
        try:
            # Normalize path
            image_path = os.path.normpath(image_path)
            
            # Load image
            logger.debug("Loading image...")
            image = cv2.imdecode(
                np.fromfile(image_path, dtype=np.uint8),
                cv2.IMREAD_COLOR
            )
            if image is None:
                raise ValueError("Failed to load image")

            # Preprocess image
            logger.debug("Preprocessing image...")
            processed, mask, circle_params = preprocess_image(
                image, 
                config=preprocess_config,
                auto_optimize=auto_optimize
            )
            
            if circle_params:
                logger.debug(f"Found petri dish: center=({circle_params[0]} {circle_params[1]}) radius={circle_params[2]}")
            
            # Get image shape
            height, width = processed.shape[:2]
            logger.debug(f"Image loaded and preprocessed shape: ({height} {width} {processed.shape[2]})")

            # Convert to model input format
            logger.debug("Converting color space...")
            processed = cv2.cvtColor(processed, cv2.COLOR_BGR2RGB)
            
            # Convert to tensor
            logger.debug("Converting to tensor...")
            image_tensor = F.to_tensor(processed)
            
            # Run inference
            logger.debug("Running model inference...")
            self.load_model()
            
            # TODO: Run actual model inference
            # For now just return dummy results
            results = self._dummy_detect(image, mask)
            logger.debug(f"Found {len(results['boxes'])} potential colonies")
            
            # Filter results
            filtered_results = self._filter_results(results, mask)
            logger.debug(f"After filtering: {len(filtered_results['boxes'])} colonies")
            
            # Count by confidence
            high = sum(1 for conf in filtered_results['scores'] if conf >= 0.9)
            med = sum(1 for conf in filtered_results['scores'] if 0.7 <= conf < 0.9)
            low = sum(1 for conf in filtered_results['scores'] if conf < 0.7)
            logger.info(f"Detection summary - High: {high} Medium: {med} Low: {low}")
            
            return filtered_results
            
        except Exception as e:
            logger.error(f"Error during detection: {str(e)}")
            raise
            
    def annotate_image(self, image_path, results):
        """
        Draw detection results on image
        
        Args:
            image_path (str): Path to image file
            results (dict): Detection results
            
        Returns:
            numpy.ndarray: Annotated image
        """
        try:
            logger.debug(f"Annotating image: {image_path}")
            
            # Normalize path and load image
            image_path = os.path.normpath(image_path)
            image = cv2.imdecode(
                np.fromfile(image_path, dtype=np.uint8),
                cv2.IMREAD_COLOR
            )
            if image is None:
                raise ValueError("Failed to load image")
                
            # Draw detections
            for i, (box, score) in enumerate(zip(results['boxes'], results['scores'])):
                x1, y1, x2, y2 = map(int, box)
                
                # Color based on confidence
                if score >= 0.9:
                    color = (0, 255, 0)  # Green
                elif score >= 0.7:
                    color = (0, 255, 255)  # Yellow
                else:
                    color = (0, 0, 255)  # Red
                    
                # Draw box
                cv2.rectangle(image, (x1, y1), (x2, y2), color, 2)
                
                # Draw label
                label = f"{i+1}: {score:.2f}"
                cv2.putText(image, label, (x1, y1-5),
                          cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
                
            return image
            
        except Exception as e:
            logger.error(f"Error annotating image: {str(e)}")
            raise
            
    def _dummy_detect(self, image, mask):
        """Generate dummy detection results for testing"""
        height, width = image.shape[:2]
        boxes = []
        scores = []
        
        # Generate some random boxes
        for _ in range(20):
            x1 = np.random.randint(0, width-50)
            y1 = np.random.randint(0, height-50)
            w = np.random.randint(20, 50)
            h = np.random.randint(20, 50)
            x2 = min(x1 + w, width)
            y2 = min(y1 + h, height)
            
            # Check if center is in mask
            center_x = (x1 + x2) // 2
            center_y = (y1 + y2) // 2
            if mask is None or mask[center_y, center_x] > 0:
                boxes.append([x1, y1, x2, y2])
                scores.append(np.random.uniform(0.7, 1.0))
        
        return {
            'boxes': boxes,
            'scores': scores
        }
        
    def _filter_results(self, results, mask=None):
        """Filter detection results"""
        filtered_boxes = []
        filtered_scores = []
        
        # Convert to numpy arrays
        boxes = np.array(results['boxes'])
        scores = np.array(results['scores'])
        
        # Sort by confidence
        indices = np.argsort(scores)[::-1]
        boxes = boxes[indices]
        scores = scores[indices]
        
        def get_iou(box1, box2):
            """Calculate IoU of two boxes"""
            x11, y11, x12, y12 = box1
            x21, y21, x22, y22 = box2
            
            xi1 = max(x11, x21)
            yi1 = max(y11, y21)
            xi2 = min(x12, x22)
            yi2 = min(y12, y22)
            
            inter_width = max(0, xi2 - xi1)
            inter_height = max(0, yi2 - yi1)
            inter_area = inter_width * inter_height
            
            box1_area = (x12 - x11) * (y12 - y11)
            box2_area = (x22 - x21) * (y22 - y21)
            
            union_area = box1_area + box2_area - inter_area
            
            return inter_area / union_area
        
        # Non-maximum suppression
        while len(boxes) > 0:
            box = boxes[0]
            filtered_boxes.append(box)
            filtered_scores.append(scores[0])
            
            other_boxes = boxes[1:]
            other_scores = scores[1:]
            
            # Remove overlapping boxes
            keep = []
            for i, other_box in enumerate(other_boxes):
                if get_iou(box, other_box) < 0.3:  # IoU threshold
                    keep.append(i)
                    
            boxes = other_boxes[keep]
            scores = other_scores[keep]
            
        return {
            'boxes': filtered_boxes,
            'scores': filtered_scores
        }
