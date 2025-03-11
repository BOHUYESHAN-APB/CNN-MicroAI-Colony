import torch
import torch.nn.functional as F

def box_area(box):
    """Calculate area of box"""
    return (box[2] - box[0]) * (box[3] - box[1])

def box_to_grid(boxes, img_h, img_w, output_size):
    """Convert bounding boxes to sampling grid coordinates"""
    rois = boxes.float()
    
    # Normalize coordinates to [-1, 1]
    rois = torch.stack([
        (rois[:, 1] + rois[:, 3]) / 2 / img_w * 2 - 1,  # x center
        (rois[:, 2] + rois[:, 4]) / 2 / img_h * 2 - 1,  # y center
        (rois[:, 3] - rois[:, 1]) / img_w * 2,          # width
        (rois[:, 4] - rois[:, 2]) / img_h * 2,          # height
    ], dim=1)

    # Generate grid
    width_multiplier = torch.linspace(-0.5, 0.5, output_size[1], device=boxes.device)
    height_multiplier = torch.linspace(-0.5, 0.5, output_size[0], device=boxes.device)
    
    y_grid, x_grid = torch.meshgrid(height_multiplier, width_multiplier, indexing='ij')
    grid = torch.stack([x_grid, y_grid], dim=-1)  # [H, W, 2]
    
    # Scale grid by box dimensions
    box_wh = rois[:, 2:].view(-1, 1, 1, 2)  # [N, 1, 1, 2]
    box_center = rois[:, :2].view(-1, 1, 1, 2)  # [N, 1, 1, 2]
    
    grid = grid.unsqueeze(0).expand(rois.size(0), -1, -1, -1)  # [N, H, W, 2]
    grid = grid * box_wh + box_center
    
    return grid

def roi_align_wrapper(features, boxes, output_size, spatial_scale=1.0):
    """
    ROI Align implementation using grid_sample
    
    Args:
        features (torch.Tensor): Input feature map [B, C, H, W] or [C, H, W]
        boxes (torch.Tensor): ROI boxes [N, 5] (batch_idx, x1, y1, x2, y2)
        output_size (tuple): Output size (h, w)
        spatial_scale (float): Scale factor
    """
    if not isinstance(output_size, tuple):
        output_size = (output_size, output_size)

    # Handle feature map dimensions
    if len(features.shape) == 3:
        features = features.unsqueeze(0)  # Add batch dimension [1, C, H, W]
    
    batch_size, channels, height, width = features.shape
    
    # Scale boxes
    scaled_boxes = boxes.clone()
    scaled_boxes[:, 1:] = scaled_boxes[:, 1:] * spatial_scale
    
    # Process each batch index separately
    output_list = []
    for b_idx in range(batch_size):
        # Get boxes for this batch
        batch_mask = (boxes[:, 0] == b_idx)
        if not batch_mask.any():
            continue
            
        batch_boxes = scaled_boxes[batch_mask]
        batch_features = features[b_idx:b_idx+1]  # Keep batch dimension [1, C, H, W]
        
        # Generate sampling grid for these boxes
        grid = box_to_grid(batch_boxes, height, width, output_size)
        
        # Expand features to match grid batch size
        batch_features = batch_features.expand(grid.size(0), -1, -1, -1)
        
        # Sample features
        roi_features = F.grid_sample(
            batch_features,
            grid,
            mode='bilinear',
            padding_mode='zeros',
            align_corners=True
        )
        output_list.append(roi_features)
    
    if not output_list:
        return torch.zeros(0, channels, output_size[0], output_size[1],
                         dtype=features.dtype, device=features.device)
    
    return torch.cat(output_list, dim=0)
