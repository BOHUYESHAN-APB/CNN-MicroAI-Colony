"""
Faster R-CNN model implementation for colony detection
菌落检测的Faster R-CNN模型实现
"""
import torch
import torchvision
from torchvision.models.detection import FasterRCNN
from torchvision.models.detection.rpn import AnchorGenerator
from typing import Dict, Any

class FasterRCNNModel:
    def __init__(self, model_path: str = None):
        """
        Initialize Faster R-CNN model
        
        Args:
            model_path: Path to pretrained model weights
        """
        # Load pretrained backbone
        backbone = torchvision.models.resnet50(pretrained=True)
        backbone.out_channels = 2048
        
        # Define anchor generator
        anchor_generator = AnchorGenerator(
            sizes=((32, 64, 128, 256, 512),),
            aspect_ratios=((0.5, 1.0, 2.0),)
        )
        
        # Define ROI pooling
        roi_pooler = torchvision.ops.MultiScaleRoIAlign(
            featmap_names=['0'],
            output_size=7,
            sampling_ratio=2
        )
        
        # Create model
        self.model = FasterRCNN(
            backbone,
            num_classes=2,  # Background + colony
            rpn_anchor_generator=anchor_generator,
            box_roi_pool=roi_pooler
        )
        
        # Load custom weights if provided
        if model_path:
            self.load_weights(model_path)
            
    def load_weights(self, path: str):
        """Load model weights from file"""
        try:
            state_dict = torch.load(path)
            self.model.load_state_dict(state_dict)
        except Exception as e:
            raise ValueError(f"Failed to load model weights: {str(e)}")
            
    def detect(self, image) -> Dict[str, Any]:
        """
        Detect colonies in image
        
        Args:
            image: Input image tensor
            
        Returns:
            Dictionary containing detection results
        """
        if not isinstance(image, torch.Tensor):
            image = torch.from_numpy(image).float()
            
        if len(image.shape) == 2:  # Grayscale
            image = image.unsqueeze(0).repeat(3, 1, 1)
        elif len(image.shape) == 3:  # RGB
            image = image.permute(2, 0, 1)
            
        # Normalize and add batch dimension
        image = image.float() / 255.0
        image = image.unsqueeze(0)
        
        # Run detection
        with torch.no_grad():
            outputs = self.model(image)
            
        # Format results
        boxes = outputs[0]['boxes'].cpu().numpy()
        scores = outputs[0]['scores'].cpu().numpy()
        labels = outputs[0]['labels'].cpu().numpy()
        
        return {
            'boxes': boxes,
            'scores': scores,
            'labels': labels
        }
