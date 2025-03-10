import torch
import torch.nn as nn
from torchvision.ops import MultiScaleRoIAlign as _MultiScaleRoIAlign
from src.ops.roi_align import roi_align_wrapper

class CustomMultiScaleRoIAlign(_MultiScaleRoIAlign):
    """Multi-scale ROI align using custom implementation while maintaining torchvision compatibility"""
    
    def __init__(self, featmap_names, output_size, sampling_ratio):
        super().__init__(featmap_names, output_size, sampling_ratio)
        
    def forward(self, x, boxes, image_shapes):
        """
        Arguments:
            x (dict[str, Tensor]): feature maps for each level
            boxes (List[Tensor[N, 4]]): boxes to pool over for each image
            image_shapes (List[Tuple[H, W]]): image shapes
        """
        num_levels = len(self.featmap_names)
        dtype, device = x[self.featmap_names[0]].dtype, x[self.featmap_names[0]].device
        
        if num_levels == 1:
            return roi_align_wrapper(
                x[self.featmap_names[0]],
                self._convert_to_roi_format(boxes),
                self.output_size,
                spatial_scale=1.0 / 4.0  # Fixed scale for single level
            )
            
        num_boxes = sum(boxes_per_image.shape[0] for boxes_per_image in boxes)
        num_channels = x[self.featmap_names[0]].shape[1]
        
        result = torch.zeros(
            (num_boxes, num_channels) + self.output_size,
            dtype=dtype,
            device=device
        )
        
        # Convert list of boxes to single tensor with batch indices
        rois = self._convert_to_roi_format(boxes)
        
        # Determine feature level for each box
        levels = self._map_levels(boxes)
        
        # Process each level
        for level, featmap_name in enumerate(self.featmap_names):
            idx_in_level = torch.where(levels == level)[0]
            if idx_in_level.numel() > 0:
                rois_per_level = rois[idx_in_level]
                
                # Calculate scale for this level
                scale = 1.0 / (2.0 ** (level + 2))  # P2 -> 1/4, P3 -> 1/8, etc.
                
                result_idx_in_level = roi_align_wrapper(
                    x[featmap_name],
                    rois_per_level,
                    self.output_size,
                    spatial_scale=scale
                )
                
                result[idx_in_level] = result_idx_in_level
                
        return result
        
    def _convert_to_roi_format(self, boxes):
        """Convert list of boxes to ROI format with batch indices"""
        concat_boxes = []
        for batch_id, boxes_in_image in enumerate(boxes):
            if boxes_in_image.numel() > 0:
                batch_indices = torch.full_like(
                    boxes_in_image[:, :1],
                    batch_id,
                    dtype=torch.float32,
                    device=boxes_in_image.device
                )
                concat_boxes.append(torch.cat((batch_indices, boxes_in_image), dim=1))
        
        if len(concat_boxes) == 0:
            return torch.zeros((0, 5), dtype=torch.float32, device=boxes[0].device)
        return torch.cat(concat_boxes, dim=0)
    
    def _map_levels(self, boxes):
        """Determine which feature level each ROI should be assigned to"""
        areas = torch.cat([box.prod(dim=1) for box in boxes])
        
        # Equation from the Feature Pyramid Networks paper
        levels = torch.floor(4.0 + torch.log2(torch.sqrt(areas) / 224.0))
        levels = levels.clamp(min=0, max=len(self.featmap_names) - 1).to(torch.int64)
        
        return levels
