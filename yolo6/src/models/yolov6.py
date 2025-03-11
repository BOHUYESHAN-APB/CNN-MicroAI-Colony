import torch
import torch.nn as nn

class ConvBlock(nn.Module):
    def __init__(self, in_channels, out_channels, kernel_size, stride, padding):
        super().__init__()
        self.conv = nn.Conv2d(in_channels, out_channels, kernel_size, stride, padding, bias=False)
        self.bn = nn.BatchNorm2d(out_channels)
        self.relu = nn.ReLU(inplace=True)

    def forward(self, x):
        return self.relu(self.bn(self.conv(x)))

class YOLOv6(nn.Module):
    def __init__(self, num_classes):
        super().__init__()
        self.num_classes = num_classes
        # Define a more complex convolutional backbone
        self.backbone = nn.Sequential(
            ConvBlock(3, 32, kernel_size=3, stride=1, padding=1),
            nn.MaxPool2d(2, 2),
            ConvBlock(32, 64, kernel_size=3, stride=1, padding=1),
            nn.MaxPool2d(2, 2),
            ConvBlock(64, 128, kernel_size=3, stride=1, padding=1),
            nn.MaxPool2d(2, 2),
            ConvBlock(128, 256, kernel_size=3, stride=1, padding=1),
            nn.MaxPool2d(2, 2),
            ConvBlock(256, 512, kernel_size=3, stride=1, padding=1),
            nn.MaxPool2d(2, 2),
            ConvBlock(512, 512, kernel_size=3, stride=1, padding=1),
            nn.MaxPool2d(2, 2)
        )
        # Feature dimensions calculation
        self.feat_channels = 512  # Last conv layer channels
        self.feat_size = 3       # Round down to 3x3 feature map
        
        # Calculate dimensions
        feat_dim = self.feat_channels * self.feat_size * self.feat_size
        out_dim = num_classes  # Each output represents one class
        
        print(f"\nModel Configuration:")
        print(f"- Input size: 224x224")
        print(f"- Feature map: {self.feat_size}x{self.feat_size}")
        print(f"- Feature channels: {self.feat_channels}")
        print(f"- Input dimension: {feat_dim}")
        print(f"- Output dimension: {out_dim}")
        
        # Create head layers for detection
        self.head = nn.Sequential(
            nn.Linear(self.feat_channels, 128),
            nn.ReLU(),
            nn.Linear(128, out_dim)
        )

    def forward(self, x):
        """Forward pass
        
        Args:
            x: Input tensor of shape (B, 3, H, W)
            
        Returns:
            Feature map of shape (B, H, W)
        """
        # Extract features (B, C, H, W)
        features = self.backbone(x)
        batch_size = features.size(0)
        
        # Process each spatial location
        feature_map = features  # (B, C, H, W)
        B, C, H, W = feature_map.shape
        
        # Reshape to process each spatial location
        feature_map = feature_map.permute(0, 2, 3, 1)  # (B, H, W, C)
        feature_map = feature_map.reshape(-1, C)  # (B*H*W, C)
        
        # Apply head to get predictions
        logits = self.head(feature_map)  # (B*H*W, 1)
        
        # Reshape back to spatial dimensions
        logits = logits.reshape(B, H, W)
        
        return logits

    def save(self, path: str) -> None:
        """Save model checkpoint to specified path.
        
        Args:
            path: Path where to save the checkpoint
            
        The checkpoint contains:
            - model state dict
            - number of classes
            - model configuration
        """
        import os
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        checkpoint = {
            'state_dict': self.state_dict(),
            'num_classes': self.num_classes,
            'model_config': {
                'backbone': [(m.__class__.__name__, m.state_dict()) for m in self.backbone],
                'head': self.head.state_dict()
            }
        }
        torch.save(checkpoint, path)
    
    @classmethod
    def load(cls, path: str) -> 'YOLOv6':
        """Load model checkpoint from specified path.
        
        Args:
            path: Path to the checkpoint file
            
        Returns:
            Loaded YOLOv6 model instance
        """
        checkpoint = torch.load(path)
        model = cls(num_classes=checkpoint['num_classes'])
        model.load_state_dict(checkpoint['state_dict'])
        return model
