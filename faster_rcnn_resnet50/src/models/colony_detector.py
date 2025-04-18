import torch
import torch.nn as nn
import torchvision
from torchvision.models.detection import FasterRCNN
from torchvision.models.detection.rpn import AnchorGenerator
from torchvision.models.detection.backbone_utils import BackboneWithFPN
from torchvision.ops.feature_pyramid_network import LastLevelMaxPool
from torchvision.ops import MultiScaleRoIAlign
from torchvision.models.detection.roi_heads import RoIHeads

class ColonyDetector(nn.Module):
    def __init__(self, num_classes=2, pretrained=True, trainable_backbone_layers=3):
        super().__init__()
        
        # Load a pre-trained ResNet50 model
        backbone = torchvision.models.resnet50(pretrained=pretrained)
        
        # Select the layers we want to use
        return_layers = {'layer1': '0', 'layer2': '1', 'layer3': '2', 'layer4': '3'}
        
        # Get the number of channels for each layer
        in_channels_stage2 = backbone.inplanes // 8
        in_channels_list = [
            in_channels_stage2,
            in_channels_stage2 * 2,
            in_channels_stage2 * 4,
            in_channels_stage2 * 8,
        ]
        out_channels = 256
        
        # Create backbone with FPN
        self.backbone = BackboneWithFPN(
            backbone,
            return_layers,
            in_channels_list,
            out_channels,
            extra_blocks=LastLevelMaxPool()
        )
        
        # Freeze layers based on trainable_backbone_layers
        if trainable_backbone_layers < 5:
            for name, parameter in self.backbone.named_parameters():
                if not any(layer in name for layer in ['layer4', 'layer3', 'layer2'][:trainable_backbone_layers]):
                    parameter.requires_grad_(False)

        # Define anchor generator for different scales
        anchor_generator = AnchorGenerator(
            sizes=((16,), (32,), (64,), (128,), (256,)),
            aspect_ratios=((0.5, 1.0, 2.0),) * 5
        )

        # Create ROI pooler using standard MultiScaleRoIAlign
        roi_pooler = MultiScaleRoIAlign(
            featmap_names=['0', '1', '2', '3'],
            output_size=7,
            sampling_ratio=2
        )

        # Create FasterRCNN model
        self.model = FasterRCNN(
            self.backbone,
            num_classes=num_classes,
            rpn_anchor_generator=anchor_generator,
            box_roi_pool=roi_pooler,
            min_size=512,
            max_size=1024,
            box_detections_per_img=300,
            box_nms_thresh=0.3,
            box_score_thresh=0.4,
            rpn_pre_nms_top_n_train=2000,
            rpn_post_nms_top_n_train=1000,
            rpn_pre_nms_top_n_test=1000,
            rpn_post_nms_top_n_test=500,
        )

        # Initialize box predictor weights
        for name, param in self.model.roi_heads.box_predictor.named_parameters():
            if "bias" in name:
                nn.init.zeros_(param)
            else:
                nn.init.normal_(param, std=0.01)

    def forward(self, images, targets=None):
        if self.training and targets is None:
            raise ValueError("In training mode, targets should be passed")
        
        device = next(self.parameters()).device
        images = [img.to(device) for img in images]
        
        if self.training:
            if targets is not None:
                targets = [{
                    'boxes': t['boxes'].to(device),
                    'labels': t['labels'].to(device)
                } for t in targets]
            return self.model(images, targets)
        else:
            return self.model(images)

    def predict(self, images):
        self.eval()
        device = next(self.parameters()).device
        images = [img.to(device) for img in images]
        
        with torch.no_grad():
            predictions = self.model(images)
        return predictions

    @staticmethod
    def get_colony_count(prediction, score_threshold=0.5):
        """Get colony count from model prediction"""
        scores = prediction['scores']
        return torch.sum(scores > score_threshold).item()
