"""
Colony Detection Model Architecture
"""
import torch
import torch.nn as nn
import torchvision.models.detection as detection_models
from torchvision.models.detection.faster_rcnn import FastRCNNPredictor

class ColonyDetectionModel(nn.Module):
    def __init__(self, num_classes=2):  # 2 classes: background and colony
        super().__init__()
        
        # Load pre-trained model
        self.model = detection_models.fasterrcnn_resnet50_fpn(pretrained=True)
        
        # Replace the classifier with a new one
        in_features = self.model.roi_heads.box_predictor.cls_score.in_features
        self.model.roi_heads.box_predictor = FastRCNNPredictor(in_features, num_classes)
        
    def forward(self, images, targets=None, nms_threshold=0.3, score_threshold=0.0):
        """Forward pass with configurable thresholds"""
        if targets is not None:
            return self.model(images, targets)
        
        # Store original values
        original_nms_thresh = self.model.roi_heads.nms_thresh
        original_score_thresh = self.model.roi_heads.score_thresh
        
        try:
            # Configure thresholds for inference
            self.model.roi_heads.nms_thresh = nms_threshold
            self.model.roi_heads.score_thresh = score_threshold
            
            # Run inference with modified parameters
            detections = self.model(images)
            
            # Process detections to handle overlapping boxes
            if len(detections) > 0 and len(detections[0]['boxes']) > 0:
                # Get overlapping boxes
                boxes = detections[0]['boxes']
                scores = detections[0]['scores']
                labels = detections[0]['labels']
                
                # Calculate box areas for aspect ratio filtering
                widths = boxes[:, 2] - boxes[:, 0]
                heights = boxes[:, 3] - boxes[:, 1]
                aspects = widths / heights
                
                # Size-based filtering first
                areas = widths * heights
                area_mean = areas.mean()
                area_std = areas.std()
                
                # Use more strict size thresholds
                valid_size = (areas >= (area_mean - area_std)) & (areas <= (area_mean + 2 * area_std))
                
                # Apply size filter first
                boxes = boxes[valid_size]
                scores = scores[valid_size]
                labels = labels[valid_size]
                
                if len(boxes) > 0:
                    # Recalculate metrics for remaining boxes
                    widths = boxes[:, 2] - boxes[:, 0]
                    heights = boxes[:, 3] - boxes[:, 1]
                    aspects = widths / heights
                    areas = widths * heights
                    
                    # Strict aspect ratio for remaining boxes
                    normal_aspect = (aspects >= 0.95) & (aspects <= 1.05)
                    
                    # Identify potential merged colonies
                    merged_colonies = ~normal_aspect & (areas > area_mean)
                    
                    # Only split colonies that are significantly elongated
                    needs_split = merged_colonies & (aspects > 1.3)
                    
                    # Store original indices for updating
                    split_indices = torch.where(needs_split)[0]
                
                # Split merged detections
                if len(split_indices) > 0:
                    for idx in split_indices:
                        box = boxes[idx]
                        # Calculate potential split points
                        width = box[2] - box[0]
                        x_center = (box[0] + box[2]) / 2
                        y_center = (box[1] + box[3]) / 2
                        
                        # Add two new boxes for split colonies
                        radius = min(width / 4, (box[3] - box[1]) / 2)
                        offset = radius * 1.5  # Space between split colonies
                        
                        # Left colony
                        new_box1 = torch.tensor([
                            x_center - offset - radius, y_center - radius,
                            x_center - offset + radius, y_center + radius
                        ]).to(boxes.device)
                        
                        # Right colony
                        new_box2 = torch.tensor([
                            x_center + offset - radius, y_center - radius,
                            x_center + offset + radius, y_center + radius
                        ]).to(boxes.device)
                        
                        # Add new boxes
                        boxes = torch.cat([boxes, new_box1.unsqueeze(0), new_box2.unsqueeze(0)])
                        scores = torch.cat([scores, scores[idx].repeat(2)])  # Use same score for split colonies
                        labels = torch.cat([labels, labels[idx].repeat(2)])  # Use same label for split colonies
                
                detections[0]['boxes'] = boxes
                detections[0]['scores'] = scores
                detections[0]['labels'] = labels
            
            return detections
            
        finally:
            # Restore original values
            self.model.roi_heads.nms_thresh = original_nms_thresh
            self.model.roi_heads.score_thresh = original_score_thresh

def create_model(num_classes=2):
    """Create model instance"""
    model = ColonyDetectionModel(num_classes=num_classes)
    return model
