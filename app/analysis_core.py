"""
Colony Detection Core - Optimized for Confidence and Accuracy
"""
import os
import cv2
import torch
import torch.cuda.amp
import numpy as np
import logging
import json
import time as time_module
from time import time
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

from .utils.path_manager import get_checkpoints_dir, get_project_root
from .utils.logger import setup_logging
import torchvision
from torchvision.models.detection.faster_rcnn import FastRCNNPredictor
from torchvision.models.detection import FasterRCNN_ResNet50_FPN_Weights

logger = setup_logging(log_file="app.log")

class ColonyDetector:
    """Enhanced colony detection and analysis with optimized confidence handling"""
    
    def __init__(self):
        self._min_size = 11  # Minimum colony size for filtering
        self._max_size = 88  # Maximum colony size for filtering
        self._confidence = 0.33  # Confidence threshold for initial detection
        self._use_gpu = False  # GPU usage flag
        self._model = None
        self._device = None
        self._weights = FasterRCNN_ResNet50_FPN_Weights.DEFAULT
        
        # Initialize model
        self.load_model()

    def visualize_results(self, image_path: str, colonies: List[Dict], 
                         count: int, inference_time: float, 
                         confidence_threshold: float,
                         ground_truth: Optional[int] = None,
                         error_rate: Optional[float] = None) -> np.ndarray:
        """Enhanced visualization with comprehensive statistics"""
        try:
            # Read and verify image
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"Could not load image: {image_path}")

            # Create visualization copy
            display = image.copy()
            h, w = display.shape[:2]

            # Calculate detailed statistics
            high_conf = 0
            med_conf = 0
            low_conf = 0

            # Draw colonies with enhanced visualization
            for colony in colonies:
                conf = colony['confidence']
                x, y = colony['x'], colony['y']
                radius = colony['radius']
                
                # Determine confidence level and color
                if conf > confidence_threshold * 0.9:
                    color = (0, 255, 0)  # Green
                    thickness = max(2, int(3 * (conf - confidence_threshold * 0.9) / 0.1))
                    high_conf += 1
                elif conf > confidence_threshold * 0.7:
                    color = (0, 255, 255)  # Yellow
                    thickness = 2
                    med_conf += 1
                else:
                    color = (0, 0, 255)  # Red
                    thickness = 1
                    low_conf += 1

                # Draw colony circle with anti-aliasing
                cv2.circle(display, (x, y), radius, color, thickness, cv2.LINE_AA)
                
                # Add confidence label
                label = f"{conf:.2f}"
                (text_w, text_h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.4, 1)
                
                # Semi-transparent background for text
                overlay = display.copy()
                cv2.rectangle(overlay, 
                            (x - text_w//2 - 2, y - radius - text_h - 4),
                            (x + text_w//2 + 2, y - radius),
                            (0, 0, 0), -1)
                cv2.addWeighted(overlay, 0.6, display, 0.4, 0, display)
                
                # Draw confidence text
                cv2.putText(display, label,
                           (x - text_w//2, y - radius - 4),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1, cv2.LINE_AA)

            # Add statistics overlay
            y = 30
            info_text = [
                f"Total Colonies: {count}",
                f"Processing Time: {inference_time:.2f}s"
            ]

            # Add ground truth comparison if available
            if ground_truth is not None:
                diff = count - ground_truth
                info_text.extend([
                    f"Ground Truth: {ground_truth}",
                    f"Difference: {diff:+d}",
                    f"Error Rate: {error_rate:.1f}%"
                ])

            # Add confidence distribution
            info_text.extend([
                f"Confidence Distribution:",
                f"  High (>{confidence_threshold*0.9:.2f}): {high_conf}",
                f"  Medium: {med_conf}",
                f"  Low (<{confidence_threshold*0.7:.2f}): {low_conf}"
            ])

            # Draw statistics with semi-transparent background
            for text in info_text:
                (text_w, text_h), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)
                
                overlay = display.copy()
                cv2.rectangle(overlay, (10, y - text_h - 5), (10 + text_w + 10, y + 5), 
                            (0, 0, 0), -1)
                cv2.addWeighted(overlay, 0.6, display, 0.4, 0, display)
                
                cv2.putText(display, text, (15, y),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                y += 30

            return display

        except Exception as e:
            logger.error(f"Visualization failed: {e}", exc_info=True)
            raise

    def load_model(self):
        """Load and configure the Faster R-CNN model with optimized settings"""
        try:
            # Device configuration and logging
            self._device = torch.device("cuda" if torch.cuda.is_available() and self._use_gpu else "cpu")
            logger.info(f"Using device: {self._device}")
            
            if self._device.type == 'cuda':
                logger.info(f"CUDA Device: {torch.cuda.get_device_name(0)}")
                logger.info(f"CUDA Memory - Allocated={torch.cuda.memory_allocated() / 1e6:.1f}MB, "
                          f"Cached={torch.cuda.memory_reserved() / 1e6:.1f}MB")
                torch.cuda.empty_cache()

            # Initialize model with colony-optimized configuration
            model_kwargs = {
                'min_size': 600, 'max_size': 1000,
                'box_score_thresh': 0.05, 'box_nms_thresh': 0.45,
                'rpn_pre_nms_top_n_test': 6000, 'rpn_post_nms_top_n_test': 3000,
                'rpn_score_thresh': 0.01, 'rpn_nms_thresh': 0.7,
                'box_detections_per_img': 500,
                'rpn_fg_iou_thresh': 0.6, 'rpn_bg_iou_thresh': 0.3,
                'box_fg_iou_thresh': 0.6, 'box_bg_iou_thresh': 0.3
            }

            # Create model with 2 classes (background + colony)
            self._model = torchvision.models.detection.fasterrcnn_resnet50_fpn(
                weights=None,  # Don't use pretrained weights
                num_classes=2,
                **model_kwargs
            ).double().to(self._device)

            # Replace box predictor with correct dimensions
            box_predictor = FastRCNNPredictor(
                in_channels=self._model.roi_heads.box_head.fc7.out_features,
                num_classes=2  # background + colony
            ).double()
            self._model.roi_heads.box_predictor = box_predictor

            # Fine-tune anchor generator
            self._model.rpn.anchor_generator.sizes = ((16,), (32,), (64,), (128,), (256,))
            self._model.rpn.anchor_generator.aspect_ratios = ((0.8, 1.0, 1.2),) * 5

            # Load trained weights
            checkpoint_path = os.path.join(get_project_root(), 'faster_rcnn_resnet50', 
                                         'checkpoints', 'checkpoint_epoch_31.pth')
            
            if os.path.exists(checkpoint_path):
                checkpoint = torch.load(checkpoint_path, map_location=self._device)
                state_dict = checkpoint.get('state_dict', checkpoint.get('model_state_dict', checkpoint))
                cleaned_state_dict = {k.replace('module.', ''): v.double() 
                                   for k, v in state_dict.items()}
                self._model.load_state_dict(cleaned_state_dict, strict=False)
                logger.info(f"Loaded weights from: {checkpoint_path}")
            else:
                logger.warning(f"Checkpoint not found at: {checkpoint_path}. Using pretrained weights.")

            self._model.eval()
            logger.info("Model initialized successfully")

        except Exception as e:
            logger.error(f"Failed to load model: {e}", exc_info=True)
            self._model = None
            raise

    def preprocess_image(self, image: np.ndarray) -> torch.Tensor:
        """Enhanced preprocessing with adaptive normalization"""
        try:
            # Convert to RGB and float64
            processed_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            processed_image = processed_image.astype(np.float64)

            # Adaptive contrast enhancement
            lab_image = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
            l_channel = lab_image[:, :, 0]
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced_l = clahe.apply(l_channel)
            lab_image[:, :, 0] = enhanced_l
            enhanced_image = cv2.cvtColor(lab_image, cv2.COLOR_LAB2RGB)
            enhanced_image = enhanced_image.astype(np.float64)

            # Adaptive normalization
            p1, p99 = np.percentile(enhanced_image, (1, 99))
            robust_scale = max(p99 - p1, 1e-8)
            normalized_image = np.clip((enhanced_image - p1) / robust_scale, 0, 1) * 255

            # Contrast-aware normalization
            gray = cv2.cvtColor(normalized_image.astype(np.uint8), cv2.COLOR_RGB2GRAY)
            local_std = cv2.GaussianBlur(gray, (0, 0), 2.0)
            contrast_mask = (local_std > local_std.mean())
            for c in range(3):
                channel = normalized_image[:, :, c]
                channel[contrast_mask] = np.clip(channel[contrast_mask] * 1.2, 0, 255)
                normalized_image[:, :, c] = channel

            # ImageNet normalization
            mean = np.array([0.485, 0.456, 0.406])
            std = np.array([0.229, 0.224, 0.225])
            processed_image = (normalized_image / 255.0 - mean) / std

            # Convert to tensor
            tensor_image = torch.from_numpy(processed_image.transpose(2, 0, 1))
            tensor_image = tensor_image.double().contiguous()
            tensor_image = tensor_image.to(self._device)

            return tensor_image

        except Exception as e:
            logger.error(f"Image preprocessing failed: {e}", exc_info=True)
            raise

    def _boost_confidence(self, boxes: np.ndarray, scores: np.ndarray) -> np.ndarray:
        """Boost confidence scores based on colony characteristics"""
        try:
            # Calculate box properties
            widths = boxes[:, 2] - boxes[:, 0]
            heights = boxes[:, 3] - boxes[:, 1]
            areas = widths * heights
            aspect_ratios = widths / heights
            centroids = np.column_stack([
                (boxes[:, 0] + boxes[:, 2]) / 2,
                (boxes[:, 1] + boxes[:, 3]) / 2
            ])

            # Size analysis
            median_area = np.median(areas)
            normalized_areas = areas / median_area

            # Size-based boost
            size_penalty = np.abs(np.log(normalized_areas))
            adaptive_scale = np.clip(0.25 / (np.std(normalized_areas) + 1e-6), 0.15, 0.3)
            size_boost = np.exp(-size_penalty) * adaptive_scale

            # Shape-based boost
            shape_penalty = np.abs(aspect_ratios - 1.0)
            circularity = 4 * np.pi * areas / ((widths + heights) ** 2)
            shape_boost = np.exp(-shape_penalty) * 0.2 * circularity

            # Distribution-based boost
            sorted_scores = np.sort(scores)
            percentiles = np.searchsorted(sorted_scores, scores) / len(scores)
            density_factor = np.exp(-np.std(normalized_areas))
            dist_boost = percentiles * 0.2 * density_factor

            # Spatial consistency boost
            dist_matrix = np.sqrt(((centroids[:, None] - centroids) ** 2).sum(axis=2))
            np.fill_diagonal(dist_matrix, np.inf)
            mean_dist = np.mean(dist_matrix[dist_matrix > 0])
            spatial_consistency = np.exp(-np.std(dist_matrix) / (mean_dist + 1e-6))
            spatial_boost = spatial_consistency * 0.1

            # Combine boosts
            boosted_scores = scores + size_boost + shape_boost + dist_boost + spatial_boost
            boosted_scores = np.clip(boosted_scores, 0.0, 1.0)

            logger.info(f"Confidence boosting stats:")
            logger.info(f"- Original scores: min={scores.min():.3f}, max={scores.max():.3f}")
            logger.info(f"- Boosted scores: min={boosted_scores.min():.3f}, max={boosted_scores.max():.3f}")

            return boosted_scores

        except Exception as e:
            logger.error(f"Confidence boosting failed: {e}", exc_info=True)
            return scores

    def postprocess_detections(self, detections: List[Dict], orig_size: tuple, 
                             tensor_image: torch.Tensor) -> List[Dict]:
        """Process detections with enhanced confidence handling"""
        colonies = []
        
        if not detections or not detections[0]["boxes"].shape[0]:
            logger.info("No detections found")
            return colonies

        # Get initial detections
        boxes = detections[0]["boxes"].cpu().numpy()
        scores = detections[0]["scores"].cpu().numpy()
        labels = detections[0]["labels"].cpu().numpy()

        # Initial filtering
        valid_mask = (labels == 1) & (scores >= 0.2)
        if not valid_mask.any():
            logger.info("No valid detections after filtering")
            return colonies

        filtered_boxes = boxes[valid_mask]
        filtered_scores = scores[valid_mask]

        # Apply confidence boosting
        boosted_scores = self._boost_confidence(filtered_boxes, filtered_scores)

        # Apply NMS
        keep_indices = torchvision.ops.nms(
            boxes=torch.from_numpy(filtered_boxes).double(),
            scores=torch.from_numpy(boosted_scores).double(),
            iou_threshold=0.45
        )

        # Scale detection boxes
        scale_h = orig_size[0] / tensor_image.shape[1]
        scale_w = orig_size[1] / tensor_image.shape[2]

        # Process detections
        for idx in keep_indices:
            box = filtered_boxes[idx]
            score = boosted_scores[idx]

            # Scale coordinates
            x1, y1, x2, y2 = box * [scale_w, scale_h, scale_w, scale_h]
            
            # Calculate dimensions
            x = int(round((x1 + x2) / 2))
            y = int(round((y1 + y2) / 2))
            width = int(round(x2 - x1))
            height = int(round(y2 - y1))
            radius = int((width + height) / 4)

            # Apply size filter
            if self._min_size <= radius * 2 <= self._max_size:
                colonies.append({
                    "x": x,
                    "y": y,
                    "radius": radius,
                    "confidence": float(score),
                    "width": width,
                    "height": height,
                    "area": float(width * height),
                    "aspect_ratio": float(width / height)
                })

        logger.info(f"Detected {len(colonies)} colonies")
        return colonies

    def analyze(self, image_path: str, **kwargs) -> Dict[str, Any]:
        """Analyze image for colony detection"""
        start_time = time()
        analysis_stats = {'timings': {}}

        try:
            # Update parameters
            self._confidence = kwargs.get('confidence', 0.33)
            self._min_size = kwargs.get('min_size', 11)
            self._max_size = kwargs.get('max_size', 88)
            self._use_gpu = kwargs.get('use_gpu', False)

            # Process image
            t0 = time()
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"Failed to read image: {image_path}")
            
            orig_size = image.shape[:2]
            analysis_stats['timings']['load'] = time() - t0

            # Model inference
            t0 = time()
            with torch.no_grad(), torch.cuda.amp.autocast(enabled=self._device.type=='cuda'):
                tensor_image = self.preprocess_image(image)
                detections = self._model([tensor_image])
            analysis_stats['timings']['inference'] = time() - t0

            # Process detections
            t0 = time()
            colonies = self.postprocess_detections(detections, orig_size, tensor_image)
            analysis_stats['timings']['postprocess'] = time() - t0

            # Load ground truth
            error_rate = None
            gt_count = None
            try:
                gt_path = os.path.join(os.path.dirname(image_path), "result.json")
                if os.path.exists(gt_path):
                    with open(gt_path, "r", encoding='utf-8') as f:
                        truth_data = json.load(f)
                        gt_data = next((item for item in truth_data 
                                    if item["图片名称"] == os.path.basename(image_path)), None)
                        if gt_data:
                            gt_count = gt_data["实际菌落数"]
                            error = abs(len(colonies) - gt_count)
                            error_rate = (error / gt_count * 100) if gt_count > 0 else 0
            except Exception as e:
                logger.warning(f"Ground truth comparison failed: {e}")

            # Save visualization
            t0 = time()
            output_dir = os.path.join(os.path.dirname(image_path), "outputs")
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, f"result_{os.path.basename(image_path)}")
            
            visualized = self.visualize_results(
                image_path=image_path,
                colonies=colonies,
                count=len(colonies),
                inference_time=time() - start_time,
                confidence_threshold=self._confidence,
                ground_truth=gt_count,
                error_rate=error_rate
            )
            cv2.imwrite(output_path, visualized)
            analysis_stats['timings']['visualization'] = time() - t0

            # Prepare results
            confidences = [c['confidence'] for c in colonies] if colonies else []
            return {
                "colonies": colonies,
                "count": len(colonies),
                "time": time() - start_time,
                "visualization_path": output_path,
                "ground_truth": gt_count,
                "error_rate": error_rate,
                "confidence_stats": {
                    "high": sum(1 for c in confidences if c > self._confidence * 0.9),
                    "medium": sum(1 for c in confidences if self._confidence * 0.7 < c['confidence'] <= self._confidence * 0.9),
                    "low": sum(1 for c in confidences if c['confidence'] <= self._confidence * 0.7),
                    "min": min(confidences) if confidences else 0,
                    "max": max(confidences) if confidences else 0,
                    "mean": np.mean(confidences) if confidences else 0
                },
                "size_stats": {
                    "area_mean": float(np.mean([c['area'] for c in colonies])) if colonies else 0,
                    "aspect_ratio_mean": float(np.mean([c['aspect_ratio'] for c in colonies])) if colonies else 0
                },
                "processing_info": {
                    "device": str(self._device),
                    "timings": analysis_stats['timings']
                }
            }

        except Exception as e:
            logger.error(f"Analysis failed: {e}", exc_info=True)
            raise
