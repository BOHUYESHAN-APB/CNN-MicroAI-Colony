"""
Colony Detection Core
"""
import cv2
import torch
import numpy as np
import logging
from typing import Dict, List, Any, Optional
from time import time
from pathlib import Path

from .utils.path_manager import get_checkpoints_dir

logger = logging.getLogger(__name__)

class ColonyDetector:
    """Colony detection and analysis"""
    
    def __init__(self):
        self._min_size = 5
        self._max_size = 100
        self._confidence = 0.5
        self._use_gpu = False
        self._model = None
        self._device = None
        
        # Initialize model
        self.load_model()
        
    def load_model(self):
        """Load detection model"""
        try:
            model_path = Path(get_checkpoints_dir()) / "checkpoint_epoch_31.pth"
            logger.info(f"Loading model from: {model_path}")
            
            if not model_path.exists():
                raise FileNotFoundError(f"Model file not found: {model_path}")
                
            # Set device
            self._device = torch.device("cuda" if torch.cuda.is_available() and self._use_gpu else "cpu")
            logger.info(f"Using device: {self._device}")
            
            # Create and load model
            from .models import create_model
            logger.info("Creating model...")
            self._model = create_model()
            
            logger.info("Loading checkpoint...")
            checkpoint = torch.load(model_path, map_location=self._device)
            logger.info(f"Checkpoint contents: {checkpoint.keys() if isinstance(checkpoint, dict) else 'Not a dict'}")
            
            # Load checkpoint and extract state dict
            if isinstance(checkpoint, dict):
                if 'model_state_dict' in checkpoint:
                    logger.info("Found model_state_dict key")
                    state_dict = checkpoint['model_state_dict']
                elif 'state_dict' in checkpoint:
                    logger.info("Found state_dict key")
                    state_dict = checkpoint['state_dict']
                else:
                    logger.info("Using checkpoint as state dict")
                    state_dict = checkpoint
            else:
                logger.info("Checkpoint is not a dict, using directly")
                state_dict = checkpoint

            # Load weights into model's internal model
            logger.info("Loading state dict into model...")
            try:
                # Remove "model." prefix from keys
                clean_state_dict = {
                    k[6:]: v for k, v in state_dict.items()
                    if k.startswith("model.")
                }
                
                # Load the cleaned state dict
                self._model.model.load_state_dict(clean_state_dict)
                logger.info("Successfully loaded state dict into model")
                
            except Exception as e:
                logger.error(f"Failed to load state dict directly: {e}")
                logger.info("Trying partial loading...")
                try:
                    # Handle backbone weights
                    backbone_state_dict = {
                        k[len("model.backbone."):]: v 
                        for k, v in state_dict.items() 
                        if k.startswith("model.backbone.")
                    }
                    self._model.model.backbone.load_state_dict(backbone_state_dict)
                    logger.info("Successfully loaded backbone weights")
                    
                    # Handle RPN weights
                    rpn_state_dict = {
                        k[len("model.rpn."):]: v 
                        for k, v in state_dict.items() 
                        if k.startswith("model.rpn.")
                    }
                    self._model.model.rpn.load_state_dict(rpn_state_dict)
                    logger.info("Successfully loaded RPN weights")
                    
                    # Handle ROI heads weights
                    roi_state_dict = {
                        k[len("model.roi_heads."):]: v 
                        for k, v in state_dict.items() 
                        if k.startswith("model.roi_heads.")
                    }
                    self._model.model.roi_heads.load_state_dict(roi_state_dict)
                    logger.info("Successfully loaded ROI heads weights")
                    
                except Exception as e2:
                    logger.error(f"Failed to load weights: {e2}")
                    raise
                
            self._model = self._model.to(self._device)
            self._model.eval()
            logger.info("Model loaded and set to eval mode")
            
            logger.info(f"Model loaded successfully from {model_path}")
            logger.info(f"Using device: {self._device}")
            
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            self._model = None
            raise
        
    def preprocess_image(self, image: np.ndarray) -> torch.Tensor:
        """Preprocess image for model input"""
        # Convert BGR to RGB
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Convert to float32
        image = image.astype(np.float32) / 255.0
        
        # Convert to tensor and add batch dimension
        image = torch.from_numpy(image).permute(2, 0, 1)
        
        return image.to(self._device)
        
    def postprocess_detections(self, detections: List[Dict], orig_size: tuple) -> List[Dict]:
        """Convert model output to colony detections"""
        colonies = []
        
        if not detections or not detections[0]["boxes"].shape[0]:
            return colonies
            
        # Get boxes, scores and labels
        boxes = detections[0]["boxes"].cpu().numpy()
        scores = detections[0]["scores"].cpu().numpy()
        labels = detections[0]["labels"].cpu().numpy()
        
        for box, score, label in zip(boxes, scores, labels):
            # Only process colony detections (label 1) with confidence above threshold
            if label == 1 and score >= self._confidence:
                x1, y1, x2, y2 = box
                
                # Calculate center and dimensions
                x = int((x1 + x2) / 2)
                y = int((y1 + y2) / 2)
                w = int(x2 - x1)
                h = int(y2 - y1)
                
                # Calculate radius as average of width and height
                radius = int((w + h) / 4)
                
                # Filter by size
                if self._min_size <= radius * 2 <= self._max_size:
                    colonies.append({
                        "x": x,
                        "y": y,
                        "radius": radius,
                        "confidence": float(score)
                    })
                    
        return colonies

    def analyze(self, image_path: str, **kwargs) -> Dict[str, Any]:
        """Analyze image for colonies"""
        start_time = time()
        
        # Get parameters
        self._confidence = kwargs.get('confidence', 0.5)
        self._min_size = kwargs.get('min_size', 5)
        self._max_size = kwargs.get('max_size', 100)
        self._use_gpu = kwargs.get('use_gpu', False)
        
        try:
            # Check if model is loaded
            if self._model is None:
                self.load_model()
            
            # Read image
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"Failed to read image: {image_path}")

            # Get original size
            orig_size = image.shape[:2]

            # Custom preprocessing based on image type
            image_name = Path(image_path).name
            if "R-C" in image_name:
                # Convert to grayscale
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

                # CLAHE (Contrast Limited Adaptive Histogram Equalization)
                clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(12, 12)) # Increased clipLimit and tileGridSize
                gray = clahe.apply(gray)

                # Gaussian blur (slightly larger kernel)
                blurred = cv2.GaussianBlur(gray, (7, 7), 0)

                # Top-hat filtering (for extracting small bright objects)
                kernel = np.ones((9,9), np.uint8)  # Larger kernel
                tophat = cv2.morphologyEx(blurred, cv2.MORPH_TOPHAT, kernel)

                # Add tophat result to the blurred image (enhances bright regions)
                enhanced = cv2.add(blurred, tophat)

                # Adaptive thresholding (larger block size for uneven illumination)
                thresh = cv2.adaptiveThreshold(enhanced, 255, cv2.ADAPTIVE_THRESH_MEAN_C, 
                                              cv2.THRESH_BINARY_INV, 25, 3) # Larger blockSize and adjusted C
                
                # Morphological operations (experiment with different combinations)
                kernel = np.ones((3,3),np.uint8)
                opening = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations = 1) # Reduced iterations
                closing = cv2.morphologyEx(opening, cv2.MORPH_CLOSE, kernel, iterations = 1) # Added closing

                # Convert back to BGR
                image = cv2.cvtColor(closing, cv2.COLOR_GRAY2BGR) # Use closing result

            # Preprocess image for the model
            tensor_image = self.preprocess_image(image)
            
            # Pass image with path info
            input_data = {'image': tensor_image, 'image_path': str(image_path)}

            # Model inference
            self._model.eval()
            with torch.no_grad():
                detections = self._model(
                    input_data,
                    nms_threshold=kwargs.get('nms_threshold', 0.3),
                    score_threshold=kwargs.get('score_threshold', 0.1)
                )
                logger.info(f"Inference completed with NMS threshold: {kwargs.get('nms_threshold', 0.3)}, score threshold: {kwargs.get('score_threshold', 0.1)}")

            # Postprocess detections
            colonies = self.postprocess_detections(detections, orig_size)
            
            # Calculate metrics
            total_area = sum([np.pi * c["radius"]**2 for c in colonies])
            image_area = orig_size[0] * orig_size[1]
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
