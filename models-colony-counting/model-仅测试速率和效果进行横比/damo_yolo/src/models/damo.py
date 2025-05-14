"""
DAMO-YOLO model implementation for colony detection.
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

class DAMONeck(nn.Module):
    """DAMO-YOLO neck module."""
    def __init__(self, channels):
        super().__init__()
        self.fpn = nn.Sequential(
            ConvBlock(channels, channels//2),
            ConvBlock(channels//2, channels//2),
            ConvBlock(channels//2, channels//2),
            nn.Upsample(scale_factor=2, mode='bilinear', align_corners=True)
        )

    def forward(self, x):
        return self.fpn(x)

class DAMOHead(nn.Module):
    """DAMO-YOLO detection head."""
    def __init__(self, in_channels, num_classes):
        super().__init__()
        self.conv1 = ConvBlock(in_channels, in_channels//2)
        self.conv2 = ConvBlock(in_channels//2, in_channels//2)
        self.out_conv = nn.Conv2d(in_channels//2, num_classes, kernel_size=1)
        
    def forward(self, x):
        x = self.conv1(x)
        x = self.conv2(x)
        return self.out_conv(x)

class DAMODetector(nn.Module):
    """DAMO-YOLO colony detection model."""
    
    def __init__(self, num_classes=1):
        """Initialize DAMO-YOLO model."""
        super().__init__()
        self.num_classes = num_classes
        
        # Backbone
        self.backbone = nn.Sequential(
            # Input conv block
            ConvBlock(3, 32, stride=2),
            ConvBlock(32, 64, stride=2),
            ConvBlock(64, 128, stride=2),
            ConvBlock(128, 256, stride=2),
            ConvBlock(256, 512),
            
            # Deep features
            ConvBlock(512, 512),
            ConvBlock(512, 512),
            ConvBlock(512, 512)
        )
        
        # Neck
        self.neck = DAMONeck(512)
        
        # Detection head
        self.head = DAMOHead(256, num_classes)

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
        return F.binary_cross_entropy_with_logits(predictions, targets)
