"""Local tuning script for dark_blob parameters on OIP-C image.
This is temporary and intended to be run from the repository root.
"""
import os
import sys
import cv2
import numpy as np
# ensure repo root is on path so core/ and utils/ can be imported
ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from core.detector import CircleDetector
from utils.config import Config

IMG = os.path.join(ROOT, 'test_images', 'OIP-C.jpg')

cfg = Config.default()
cd = CircleDetector()

img = cv2.imread(IMG)
if img is None:
    print('Failed to load', IMG)
    raise SystemExit(1)

# detect dish to get px_per_mm and center
dishes = cd.detect_petri_dishes(img)
if not dishes:
    print('No dishes found')
    raise SystemExit(1)

dish = dishes[0]
cd.px_per_mm = cd.px_per_mm or 4.0

# use a virtual substance at dish center if none detected
# create simple ROI around dish center
cx, cy = dish.center
roi_r = int(min(dish.radius * 0.6, 200))
roi, ox, oy = cd._get_roi_with_offset(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), cx, cy, roi_r)

param_grid = []
for tk in [(9,9),(15,15)]:
    for clahe in [1.0, 1.5, 2.0]:
        for minA in [30,50,80]:
            for minCirc in [0.15, 0.2, 0.25]:
                param_grid.append({'tophat_kernel': tk, 'clahe_clip': clahe, 'minArea': minA, 'minCircularity': minCirc})

results = []
for p in param_grid:
    # write profile temporarily to CFG
    cfg.profiles['dark_blob'] = p
    cd.processor = cd.processor  # ensure processor exists
    # call blob evidence assuming candidate center at center
    ev = cd._blob_evidence_for_candidate(roi, (roi.shape[1]//2, roi.shape[0]//2), max(6, int(6*cd.px_per_mm)))
    results.append((p, ev))

# sort by keypoint count desc then near_center
results_sorted = sorted(results, key=lambda x: (x[1]['count'], int(x[1]['near_center'])), reverse=True)
out = os.path.join(os.path.dirname(__file__), 'tune_blob_local_results.txt')
with open(out, 'w', encoding='utf-8') as f:
    for p, ev in results_sorted:
        f.write(f"{p} -> {ev}\n")

print('Written results to', out)
print(results_sorted[:6])
