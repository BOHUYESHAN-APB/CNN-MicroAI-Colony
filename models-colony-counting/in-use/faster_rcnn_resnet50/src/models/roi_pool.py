import torch
import torch.nn as nn
import torch.nn.functional as F
from ..ops.roi_align import roi_align_wrapper

class CustomMultiScaleRoIAlign(nn.Module):
    """Custom ROI Align implementation"""
    def __init__(self, featmap_names, output_size, sampling_ratio):
        super().__init__()
        self.featmap_names = featmap_names
        self.output_size = output_size if isinstance(output_size, (list, tuple)) else (output_size, output_size)
        self.sampling_ratio = sampling_ratio
        
    def forward(self, x, boxes, image_shapes):
        """
        Args:
            x (dict): feature maps {name: tensor}
            boxes (list[Tensor]): ROI boxes for each image
            image_shapes (list[tuple]): image shapes
        """
        num_images = len(boxes)
        if not isinstance(x, dict):
            x = {str(i): feat for i, feat in enumerate(x)}
            
        num_channels = x[self.featmap_names[0]].shape[1]
        
        dtype, device = x[self.featmap_names[0]].dtype, x[self.featmap_names[0]].device
        result = torch.zeros(
            (num_images,) + (num_channels,) + self.output_size,
            dtype=dtype,
            device=device
        )
        
        for i in range(num_images):
            per_image_boxes = boxes[i]
            if per_image_boxes.numel() == 0:
                continue
                
            image_size = image_shapes[i]
            features = [x[name][i:i+1] for name in self.featmap_names]
            
            aligned_features = roi_align_wrapper(
                features,
                per_image_boxes,
                self.output_size,
                spatial_scale=1.0
            )
            
            result[i] = aligned_features
            
        return result
