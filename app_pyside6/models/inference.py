import logging
from pathlib import Path
from typing import Dict, Any, Tuple, List
import random
import numpy as np
import cv2
import torch
import torch.nn as nn
from torchvision.transforms import functional as F

from src.models.colony_detector import ColonyDetector

logger = logging.getLogger(__name__)

class ModelInference:
    """Model inference class"""
    
    def __init__(self, config):
        self.config = config
        self.demo_mode = config.get('model.demo_mode', True)
        
        # Model related attributes
        self.model = None
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        # Preprocessing parameters
        self.edge_low = config.get('model.preprocess.edge_low', 50)
        self.edge_high = config.get('model.preprocess.edge_high', 150)
        self.min_area = config.get('model.preprocess.min_area', 50)
        self.watershed_threshold = config.get('model.preprocess.watershed_thresh', 0.7)
        
        if self.demo_mode:
            logger.info("Running in demo mode - using mock predictions")
        else:
            logger.info(f"Initializing model on device: {self.device}")
            self.load_model()
            
    def update_config(self, config):
        """Update configuration and reload model if necessary"""
        self.config = config
        
        # Check if demo mode changed
        new_demo_mode = config.get('model.demo_mode', True)
        if new_demo_mode != self.demo_mode:
            self.demo_mode = new_demo_mode
            if self.demo_mode:
                logger.info("Switching to demo mode - unloading model")
                self.model = None  # Unload model
            else:
                logger.info(f"Switching to model mode - loading model on device: {self.device}")
                self.load_model()  # Reload model
        
        # Update preprocessing parameters
        self.edge_low = config.get('model.preprocess.edge_low', 50)
        self.edge_high = config.get('model.preprocess.edge_high', 150)
        self.min_area = config.get('model.preprocess.min_area', 50)
        self.watershed_threshold = config.get('model.preprocess.watershed_thresh', 0.7)
            
    def _config_model(self):
        """Configure model settings"""
        try:
            # Set device
            logger.info(f"Using device: {self.device}")
            
            # Set to evaluation mode
            if self.model is not None:
                self.model.to(self.device)
                self.model.eval()
                
        except Exception as e:
            logger.error(f"Failed to configure model: {e}")
            raise
            
    def load_model(self):
        """Load model checkpoint"""
        try:
            checkpoint_dir = self.config.get('model.checkpoint_dir')
            if not checkpoint_dir:
                raise ValueError("Model checkpoint directory not specified")
                
            # Load checkpoint 31
            weights_path = Path(checkpoint_dir) / 'checkpoint_epoch_31.pth'
            if not weights_path.exists():
                raise ValueError(f"Model weights not found at {weights_path}")
                
            # Initialize model
            self.model = ColonyDetector(num_classes=2, pretrained=False)
            
            # Load weights
            checkpoint = torch.load(weights_path, map_location=self.device)
            if 'model_state_dict' in checkpoint:
                state_dict = checkpoint['model_state_dict']
            else:
                state_dict = checkpoint
            
            self.model.load_state_dict(state_dict)
            self.model.to(self.device)
            self.model.eval()
            
            logger.info(f"Successfully loaded model from {weights_path}")
            
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise
            
    def predict(self, image: np.ndarray) -> Dict[str, Any]:
        """Run inference on image"""
        try:
            if self.demo_mode:
                return self._mock_predict()
            
            if self.model is None:
                raise ValueError("Model not loaded")
            
            # Preprocess image
            processed = self._preprocess_image(image)
            
            # Convert to tensor format required by Faster R-CNN
            input_tensor = self._preprocess_image(image).unsqueeze(0).to(self.device)
            
            # Run model inference
            with torch.no_grad():
                predictions = self.model.predict([input_tensor])[0]  # Get first image predictions
            
            # Extract predictions
            boxes = predictions['boxes'].cpu().numpy()
            scores = predictions['scores'].cpu().numpy()
            labels = predictions['labels'].cpu().numpy()
            
            # Filter by confidence threshold
            confidence_threshold = self.config.get('model.confidence_threshold', 0.5)
            mask = scores > confidence_threshold
            boxes = boxes[mask]
            scores = scores[mask]
            labels = labels[mask]
            
            # Calculate count and statistics
            count = float(len(boxes))
            confidence = float(scores.mean()) if len(scores) > 0 else 0.0
            
            # Generate statistics
            stats = {
                'count_stats': {
                    'mean': count,
                    'std': float(np.std(scores)) if len(scores) > 0 else 0.0,
                    'cv': float(np.std(scores)/np.mean(scores)) if len(scores) > 0 else 0.0,
                    'min': float(scores.min()) if len(scores) > 0 else 0.0,
                    'max': float(scores.max()) if len(scores) > 0 else 0.0,
                    'median': float(np.median(scores)) if len(scores) > 0 else 0.0,
                    'q1': float(np.percentile(scores, 25)) if len(scores) > 0 else 0.0,
                    'q3': float(np.percentile(scores, 75)) if len(scores) > 0 else 0.0
                },
                'confidence_stats': {
                    'mean': confidence,
                    'std': float(np.std(scores)) if len(scores) > 0 else 0.0,
                    'min': float(scores.min()) if len(scores) > 0 else 0.0,
                    'max': float(scores.max()) if len(scores) > 0 else 0.0
                }
            }
            
            return {
                'count': count,
                'confidence': confidence,
                'boxes': boxes.tolist(),
                'scores': scores.tolist(),
                'statistics': stats
            }
            
        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            raise
            
    def _mock_predict(self) -> Dict[str, Any]:
        """Generate mock prediction results for demo mode"""
        try:
            count = float(random.randint(50, 200))
            confidence = float(random.uniform(0.8, 0.99))
            
            return {
                'count': float(count),
                'confidence': float(confidence),
                'boxes': [],  # Placeholder for detection boxes
                'scores': [],  # Placeholder for detection scores
                'statistics': {
                    'count_stats': {
                        'mean': float(count),
                        'std': 0.0,
                        'cv': 0.0,
                        'min': float(count),
                        'max': float(count),
                        'median': float(count),
                        'q1': float(count),
                        'q3': float(count)
                    },
                    'confidence_stats': {
                        'mean': float(confidence),
                        'std': 0.0,
                        'min': float(confidence),
                        'max': float(confidence)
                    }
                }
            }
        except Exception as e:
            logger.error(f"Mock prediction failed: {e}")
            raise ValueError("Failed to generate mock prediction")
            
    def _preprocess_image(self, image: np.ndarray) -> torch.Tensor:
        """Preprocess image for Faster R-CNN input"""
        try:
            # Convert BGR to RGB
            if len(image.shape) == 3:
                image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            else:
                # Convert grayscale to RGB
                image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
            
            # Convert to float32
            image = image.astype(np.float32)
            
            # Normalize to [0, 1]
            image = image / 255.0
            
            # Convert to tensor
            image = torch.from_numpy(image).permute(2, 0, 1)
            
            # Normalize using ImageNet mean and std
            normalize = torch.nn.functional.normalize
            mean = torch.tensor([0.485, 0.456, 0.406]).view(-1, 1, 1)
            std = torch.tensor([0.229, 0.224, 0.225]).view(-1, 1, 1)
            image = normalize(image, mean=mean, std=std)
            
            return image
            
        except Exception as e:
            logger.error(f"Image preprocessing failed: {e}")
            raise

    def _apply_watershed(self, binary: np.ndarray) -> np.ndarray:
        """Apply watershed algorithm for colony segmentation"""
        try:
            # Noise removal
            kernel = np.ones((3,3), np.uint8)
            opening = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel, iterations=2)
            
            # Sure background area
            sure_bg = cv2.dilate(opening, kernel, iterations=3)
            
            # Finding sure foreground area using distance transform
            dist = cv2.distanceTransform(opening, cv2.DIST_L2, 5)
            dist = cv2.normalize(dist, None, 0, 255, cv2.NORM_MINMAX)
            
            # Threshold for sure foreground
            _, sure_fg = cv2.threshold(dist, self.watershed_threshold*dist.max(), 255, 0)
            sure_fg = np.uint8(sure_fg)
            
            # Finding unknown region
            unknown = cv2.subtract(sure_bg, sure_fg)
            
            # Marker labelling
            ret, markers = cv2.connectedComponents(sure_fg)
            markers = markers + 1
            markers[unknown == 255] = 0
            
            # Apply watershed
            color_img = cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR)
            markers = cv2.watershed(color_img, markers)
            
            # Create result image
            result = np.zeros_like(binary)
            result[markers > 1] = 255
            
            return result
            
        except Exception as e:
            logger.error(f"Watershed algorithm failed: {e}")
            raise
