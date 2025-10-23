"""Grid search for dark_blob parameters with overlays saved for manual inspection.
Saves results to tools/tune_blob_grid_results.csv and overlays to tools/tune_blob_grid_outputs/
"""
import os
import sys
import cv2
import csv
import math
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from core.detector import CircleDetector
from utils.config import Config

IMG = os.path.join(ROOT, 'test_images', 'OIP-C.jpg')
OUT_DIR = os.path.join(os.path.dirname(__file__), 'tune_blob_grid_outputs')
CSV_OUT = os.path.join(os.path.dirname(__file__), 'tune_blob_grid_results.csv')

os.makedirs(OUT_DIR, exist_ok=True)

cfg = Config.default()
cd = CircleDetector()

img = cv2.imread(IMG)
if img is None:
    raise SystemExit('cannot load image: ' + IMG)

# detect dish to set px/mm and dish center
dishes = cd.detect_petri_dishes(img)
if not dishes:
    raise SystemExit('no dishes found')

dish = dishes[0]
cd.px_per_mm = cd.px_per_mm or 4.0

# choose ROI: full dish area (crop)
dx, dy = dish.center
roi_r = int(dish.radius * 0.9)
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
roi, ox, oy = cd._get_roi_with_offset(gray, dx, dy, roi_r)
orig_roi_color, _, _ = cd._get_roi_with_offset(img, dx, dy, roi_r)

# parameter grid
tophat_choices = [(7,7),(9,9),(11,11),(15,15)]
clahe_choices = [1.0, 1.5, 2.0]
minArea_choices = [20,50,80]
minCirc_choices = [0.12, 0.2, 0.3]

combos = []
for tk in tophat_choices:
    for cc in clahe_choices:
        for ma in minArea_choices:
            for mc in minCirc_choices:
                combos.append({'tophat_kernel': tk, 'clahe_clip': cc, 'minArea': ma, 'minCircularity': mc})

print(f'Running {len(combos)} combos...')

results = []
for i, p in enumerate(combos):
    profile = {
        'tophat_kernel': p['tophat_kernel'],
        'clahe_clip': p['clahe_clip'],
        'minArea': p['minArea'],
        'maxArea': int(p['minArea'] * 200),
        'minCircularity': p['minCircularity'],
        'minInertiaRatio': 0.05
    }
    # set temporary profile
    cfg.profiles['dark_blob'] = profile

    # call detector helper
    ev = cd._blob_evidence_for_candidate(roi, (roi.shape[1]//2, roi.shape[0]//2), max(6, int(6*cd.px_per_mm)))

    # metrics
    count = ev['count']
    near_center = 1 if ev['near_center'] else 0
    on_ring = 1 if ev['on_ring'] else 0

    # draw overlay on color roi
    overlay = orig_roi_color.copy() if orig_roi_color is not None else cv2.cvtColor(roi, cv2.COLOR_GRAY2BGR)
    # run preproc+detector again to get keypoints for plotting
    # emulate _blob_evidence_for_candidate internal steps
    tk = tuple(profile['tophat_kernel'])
    old_clip = getattr(cd.processor, 'clahe_clip_limit', None)
    try:
        cd.processor.clahe_clip_limit = profile['clahe_clip']
        pre = cd.processor.preprocess_for_hole(roi.copy(), tophat_kernel=tk)
    finally:
        if old_clip is not None:
            cd.processor.clahe_clip_limit = old_clip
    params = cv2.SimpleBlobDetector_Params()
    params.minThreshold = 5
    params.maxThreshold = 255
    params.filterByArea = True
    params.minArea = int(profile['minArea'])
    params.maxArea = int(profile['maxArea'])
    params.filterByCircularity = True
    params.minCircularity = float(profile['minCircularity'])
    params.filterByInertia = True
    params.minInertiaRatio = float(profile['minInertiaRatio'])
    params.filterByConvexity = False
    detector = cv2.SimpleBlobDetector_create(params)
    kps = detector.detect(pre)

    # plot keypoints
    for kp in kps:
        x = int(kp.pt[0]) + ox
        y = int(kp.pt[1]) + oy
        cv2.circle(overlay, (int(kp.pt[0]), int(kp.pt[1])), int(kp.size//2), (0,0,255), 2)
    # center marker
    cv2.circle(overlay, (overlay.shape[1]//2, overlay.shape[0]//2), 3, (0,255,0), -1)

    fn = f"tk{tk[0]}_cc{profile['clahe_clip']}_ma{profile['minArea']}_mc{profile['minCircularity']}.png"
    cv2.imwrite(os.path.join(OUT_DIR, fn), overlay)

    results.append((p, count, near_center, on_ring, fn))
    if (i+1) % 10 == 0:
        print(f'{i+1}/{len(combos)} done')

# write CSV
with open(CSV_OUT, 'w', newline='', encoding='utf-8') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(['tophat_kernel', 'clahe_clip', 'minArea', 'minCircularity', 'count', 'near_center', 'on_ring', 'overlay'])
    for r in results:
        p, count, near_center, on_ring, fn = r
        writer.writerow([p['tophat_kernel'], p['clahe_clip'], p['minArea'], p['minCircularity'], count, near_center, on_ring, fn])

# sort and print top combos (prefer near_center then count then fewer kps)
sorted_res = sorted(results, key=lambda x: (x[2], x[1], -x[1]), reverse=True)
print('Top 6 combos:')
for r in sorted_res[:6]:
    print(r)

# pick best (first) and update Config file by writing to utils/config.py
best = sorted_res[0][0]
from pathlib import Path
config_py = Path(ROOT) / 'utils' / 'config.py'
# simplistic edit: replace dark_blob block by string substitution
text = config_py.read_text(encoding='utf-8')
old_block_start = "'dark_blob': {"
start_idx = text.find(old_block_start)
if start_idx != -1:
    end_idx = text.find('}', start_idx)
    # find the closing } of that dict by searching forward for the next '}' on its own line; rough replacement
    # we will instead replace the known lines between the keys
    new_profile = f"'dark_blob': {{\n                'tophat_kernel': {best['tophat_kernel']},\n                'clahe_clip': {best['clahe_clip']},\n                'minArea': {best['minArea']},\n                'maxArea': {int(best['minArea']*200)},\n                'minCircularity': {best['minCircularity']},\n                'minInertiaRatio': 0.05\n            }}"
    # naive replace: find the closing of the dictionary by matching the first '}' after start_idx
    # find the position of the closing '}' that ends the profiles dict entry by scanning
    profiles_pos = text.find("self.profiles = {", 0)
    if profiles_pos != -1:
        # find the end of the profiles dict by locating the matching '}' after profiles_pos
        pstart = text.find('{', profiles_pos)
        depth = 0
        pind = -1
        for idx in range(pstart, len(text)):
            if text[idx] == '{':
                depth += 1
            elif text[idx] == '}':
                depth -= 1
                if depth == 0:
                    pind = idx
                    break
        if pind != -1:
            # create new profiles text by replacing existing content between the first { and pind
            new_profiles = "{\n            'dark_blob': {\n                'tophat_kernel': %s,\n                'clahe_clip': %s,\n                'minArea': %s,\n                'maxArea': %s,\n                'minCircularity': %s,\n                'minInertiaRatio': 0.05\n            }\n        }" % (best['tophat_kernel'], best['clahe_clip'], best['minArea'], int(best['minArea']*200), best['minCircularity'])
            new_text = text[:pstart+1] + '\n            ' + new_profiles + text[pind+1:]
            config_py.write_text(new_text, encoding='utf-8')
            print('Updated utils/config.py with best dark_blob profile')
        else:
            print('Could not locate end of profiles block to update config.py')
else:
    print('Could not find dark_blob block to update in config.py')

print('Done.')
