import torch

def box_iou(boxes1, boxes2):
    """
    Return intersection-over-union (IoU) between two sets of boxes
    """
    def box_area(box):
        # box = 4xn
        return (box[2] - box[0]) * (box[3] - box[1])

    area1 = box_area(boxes1.T)
    area2 = box_area(boxes2.T)

    # Calculate intersection areas
    lt = torch.max(boxes1[:, None, :2], boxes2[:, :2])  # [N,M,2]
    rb = torch.min(boxes1[:, None, 2:], boxes2[:, 2:])  # [N,M,2]

    wh = (rb - lt).clamp(min=0)  # [N,M,2]
    inter = wh[:, :, 0] * wh[:, :, 1]  # [N,M]

    # Calculate IoU
    union = area1[:, None] + area2 - inter
    iou = inter / union
    return iou

def nms_wrapper(boxes, scores, iou_threshold):
    """
    Non-maximum suppression using PyTorch operations
    boxes: tensor(N, 4), format: (x1, y1, x2, y2)
    scores: tensor(N)
    iou_threshold: float
    """
    if len(boxes) == 0:
        return torch.zeros(0, dtype=torch.int64, device=boxes.device)

    # Sort boxes by scores
    _, order = scores.sort(descending=True)
    boxes = boxes[order]

    keep = []
    while order.numel() > 0:
        if order.numel() == 1:
            keep.append(order[0])
            break
        else:
            i = order[0]
            keep.append(i)

            # Calculate IoU of the kept box with the rest
            ious = box_iou(boxes[0:1], boxes[1:])  # shape: [1, rest]

            # Find boxes with IoU less than threshold
            mask = ious[0] <= iou_threshold
            order = order[1:][mask]
            boxes = boxes[1:][mask]

    return torch.tensor(keep, dtype=torch.int64, device=boxes.device)
