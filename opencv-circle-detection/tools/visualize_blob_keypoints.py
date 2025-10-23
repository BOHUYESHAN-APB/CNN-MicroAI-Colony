import sys
import os
import cv2
import numpy as np
import argparse
import math

# add project root to path so imports like `utils` and `core` resolve when running from tools/
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from utils.config import Config
from core.detector import CircleDetector, SubstanceType


def visualize(image_path, out_path):
    cfg = Config.default()
    det = CircleDetector()

    img = cv2.imread(image_path)
    if img is None:
        raise RuntimeError(f"无法读取图像: {image_path}")

    dishes = det.detect_petri_dishes(img)
    if not dishes:
        raise RuntimeError("未检测到培养皿，无法继续可视化")
    dish = dishes[0]

    # 分析物质（会填充 det.detected_substances 或创建虚拟）
    det.px_per_mm = det.px_per_mm  # keep existing calibration
    mode, stype, subs = det.analyze_dish_contents(img, dish)

    subs_to_process = det.detected_substances if det.detected_substances else []
    if not subs_to_process:
        # create virtual center as pipeline does
        default_substance_radius_mm = det.hole_diameter_mm / 2
        if det.px_per_mm and det.px_per_mm > 0:
            default_substance_radius_px = int(default_substance_radius_mm * det.px_per_mm)
        else:
            default_substance_radius_px = 10
        from core.models import Colony
        center_substance = Colony(center=dish.center, radius=max(1, default_substance_radius_px), contour=det._create_circle_contour(dish.center, max(1, default_substance_radius_px)))
        subs_to_process = [center_substance]

    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    profile = cfg.profiles.get('dark_blob', {}) if hasattr(cfg, 'profiles') else {}
    tk = tuple(profile.get('tophat_kernel', (9, 9)))
    clahe_clip = float(profile.get('clahe_clip', getattr(det.processor, 'clahe_clip_limit', 2.0)))

    for idx, sub in enumerate(subs_to_process):
        x_sub, y_sub = sub.center
        search_roi_radius_px = max(sub.radius * 4, int(img.shape[0] / 5))
        roi_img, rx, ry = det._get_roi_with_offset(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), x_sub, y_sub, search_roi_radius_px)
        if roi_img is None:
            print(f"无法获取 ROI for substance {idx}")
            continue

        roi_color = img[ry:ry+roi_img.shape[0], rx:rx+roi_img.shape[1]].copy()

        # Preprocess same as _blob_evidence_for_candidate
        old_clip = getattr(det.processor, 'clahe_clip_limit', None)
        try:
            det.processor.clahe_clip_limit = clahe_clip
            pre = det.processor.preprocess_for_hole(roi_img.copy(), tophat_kernel=tk)
        finally:
            if old_clip is not None:
                det.processor.clahe_clip_limit = old_clip

        # Build blob detector params from profile
        params = cv2.SimpleBlobDetector_Params()
        params.minThreshold = int(profile.get('minThreshold', 5))
        params.maxThreshold = int(profile.get('maxThreshold', 255))
        params.filterByArea = True
        params.minArea = int(profile.get('minArea', max(10, np.pi * (max(1, sub.radius * 0.5) ** 2))))
        params.maxArea = int(profile.get('maxArea', max(1000, np.pi * ((sub.radius * 1.5) ** 2))))
        params.filterByCircularity = bool(profile.get('filterByCircularity', True))
        params.minCircularity = float(profile.get('minCircularity', 0.2))
        params.filterByInertia = bool(profile.get('filterByInertia', True))
        params.minInertiaRatio = float(profile.get('minInertiaRatio', 0.05))
        params.filterByConvexity = bool(profile.get('filterByConvexity', False))
        params.filterByColor = False

        detector = cv2.SimpleBlobDetector_create(params)
        keypoints = detector.detect(pre)

        # Convert candidate center to ROI-relative coords
        cx_rel = int(sub.center[0] - rx)
        cy_rel = int(sub.center[1] - ry)
        r_rel = float(sub.radius)

        # Draw candidate center and ring band
        overlay = roi_color.copy()
        cv2.circle(overlay, (int(cx_rel), int(cy_rel)), max(1, int(r_rel)), (0, 255, 255), 2)  # candidate circle
        # ring band
        inner = int(max(1, r_rel * 0.82))
        outer = int(max(2, r_rel * 1.18))
        cv2.circle(overlay, (int(cx_rel), int(cy_rel)), inner, (200, 200, 200), 1)
        cv2.circle(overlay, (int(cx_rel), int(cy_rel)), outer, (200, 200, 200), 1)

        # classify and draw keypoints
        for kp in keypoints:
            kp_x = int(kp.pt[0])
            kp_y = int(kp.pt[1])
            d = math.hypot(kp_x - cx_rel, kp_y - cy_rel)
            if d <= max(1, r_rel * 0.2):
                color = (0, 255, 0)  # green = near_center
                label = 'C'
            elif r_rel * 0.82 <= d <= r_rel * 1.18:
                color = (0, 0, 255)  # red = on_ring
                label = 'R'
            else:
                color = (255, 0, 0)  # blue = other
                label = 'O'
            cv2.circle(overlay, (kp_x, kp_y), max(1, int(kp.size//2)), color, -1)
            cv2.putText(overlay, label, (kp_x+3, kp_y+3), cv2.FONT_HERSHEY_SIMPLEX, 0.3, color, 1)

        out_fn = os.path.join(out_path, f"visual_{os.path.basename(image_path).split('.')[0]}_sub{idx}.png")
        cv2.imwrite(out_fn, overlay)
        print(f"保存可视化: {out_fn} (kp_total={len(keypoints)})")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--image', required=True, help='输入图像路径')
    parser.add_argument('--outdir', required=False, default='test_outputs', help='输出目录')
    args = parser.parse_args()

    visualize(args.image, args.outdir)
