"""
YOLOv11 model implementation for colony detection.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F

class ConvBlock(nn.Module):
    """Basic convolutional block with batch normalization and activation."""
    def __init__(self, in_channels, out_channels, kernel_size=3, stride=1, padding=1):
        super().__init__()
        self.conv = nn.Conv2d(in_channels, out_channels, kernel_size, stride, padding, bias=False)
        self.bn = nn.BatchNorm2d(out_channels)
        self.act = nn.SiLU()

    def forward(self, x):
        return self.act(self.bn(self.conv(x)))

class YOLO11Neck(nn.Module):
    """YOLOv11 neck module with improved feature pyramid network."""
    def __init__(self, channels):
        super().__init__()
        self.lateral = nn.Conv2d(channels, channels//2, 1)
        self.fpn = nn.Sequential(
            ConvBlock(channels//2, channels//2),
            ConvBlock(channels//2, channels//2),
            nn.Upsample(scale_factor=2, mode='bilinear', align_corners=True)
        )
        self.post_fpn = ConvBlock(channels//2, channels//2)

    def forward(self, x):
        feat = self.lateral(x)
        feat = self.fpn(feat)
        return self.post_fpn(feat)

class YOLO11Head(nn.Module):
    """YOLOv11 detection head with multi-scale feature fusion."""
    def __init__(self, in_channels, num_classes):
        super().__init__()
        self.conv1 = ConvBlock(in_channels, in_channels)
        self.conv2 = ConvBlock(in_channels, in_channels)
        self.attention = nn.Sequential(
            nn.AdaptiveAvgPool2d(1),
            nn.Conv2d(in_channels, in_channels//16, 1),
            nn.ReLU(inplace=True),
            nn.Conv2d(in_channels//16, in_channels, 1),
            nn.Sigmoid()
        )
        self.out_conv = nn.Conv2d(in_channels, num_classes, kernel_size=1)
        
    def forward(self, x):
        feat = self.conv1(x)
        feat = self.conv2(feat)
        # Apply channel attention
        attention = self.attention(feat)
        feat = feat * attention
        return self.out_conv(feat)

class YOLO11Detector(nn.Module):
    """YOLOv11 colony detection model."""
    
    def __init__(self, num_classes=1):
        """Initialize YOLOv11 model."""
        super().__init__()
        self.num_classes = num_classes
        
        # Advanced backbone with residual connections
        self.backbone = nn.Sequential(
            # Initial conv block
            ConvBlock(3, 32, stride=2),
            ConvBlock(32, 64, stride=2),
            
            # First residual stage
            self._make_stage(64, 128, 2, stride=2),
            
            # Second residual stage
            self._make_stage(128, 256, 3, stride=2),
            
            # Third residual stage
            self._make_stage(256, 512, 3),
            
            # Final convolutions
            ConvBlock(512, 512),
            ConvBlock(512, 512)
        )
        
        # Feature pyramid neck
        self.neck = YOLO11Neck(512)
        
        # Detection head
        self.head = YOLO11Head(256, num_classes)
        
        # Initialize weights
        self._initialize_weights()

    def _make_stage(self, in_channels, out_channels, num_blocks, stride=1):
        """Create a stage of residual blocks."""
        layers = []
        layers.append(ConvBlock(in_channels, out_channels, stride=stride))
        for _ in range(num_blocks - 1):
            layers.append(ConvBlock(out_channels, out_channels))
        return nn.Sequential(*layers)

    def forward(self, x):
        """Forward pass."""
        # Extract features
        features = self.backbone(x)
        
        # FPN neck
        neck_out = self.neck(features)
        
        # Detection head
        detections = self.head(neck_out)
        
        return detections

    def _initialize_weights(self):
        """Initialize model weights."""
        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                nn.init.kaiming_normal_(m.weight, mode='fan_out', nonlinearity='relu')
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.BatchNorm2d):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)

    def get_loss(self, predictions, targets):
        """Calculate loss."""
        loss = F.binary_cross_entropy_with_logits(predictions, targets)
        return loss, None # Return loss and None for loss_components
