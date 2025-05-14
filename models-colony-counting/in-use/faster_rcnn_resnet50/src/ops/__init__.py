# Make ops a package
from .nms import nms_wrapper
from .roi_align import roi_align_wrapper

def apply_patches():
    # Patch torchvision ops
    import torchvision.ops as ops
    
    # Patch NMS
    def nms_patch(*args, **kwargs):
        return nms_wrapper(*args, **kwargs)
    ops.nms = nms_patch
    ops.boxes.nms = nms_patch
    
    # Patch ROI Align
    def roi_align_patch(*args, **kwargs):
        return roi_align_wrapper(*args, **kwargs)
    ops.roi_align = roi_align_patch
    ops.RoIAlign.forward = staticmethod(roi_align_patch)
