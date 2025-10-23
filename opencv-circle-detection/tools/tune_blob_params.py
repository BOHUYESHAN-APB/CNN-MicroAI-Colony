import cv2
import numpy as np
import os
import sys
from pathlib import Path
import math

# Ensure opencv-circle-detection package path is on sys.path when script is run
ROOT = Path(__file__).parents[1].resolve()
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.processor import ImageProcessor

IMAGE_PATH = Path(__file__).parents[1] / 'test_images' / 'OIP-C.jpg'
OUT_DIR = Path(__file__).parents[1] / 'test_outputs' / 'tune_blob'
OUT_DIR.mkdir(parents=True, exist_ok=True)

img = cv2.imread(str(IMAGE_PATH))
if img is None:
    raise SystemExit('无法加载测试图像')

gray_orig = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

# grid
tophat_kernels = [(9,9), (15,15), (21,21)]
clahe_clip_limits = [1.5, 2.0, 3.0]
min_areas = [50, 80, 100, 150]
min_circularities = [0.2, 0.25, 0.3]

# expected approximate hole center (from earlier analysis) as proxy for hit scoring
expected_center = (223, 211)
hit_radius = 20  # px radius to count a detection as hit

def preprocess_for_tune(gray, tophat_kernel=(15,15), clahe_clip=2.0):
    # denoise
    denoised = cv2.GaussianBlur(gray, (9,9), 2.0)
    # tophat
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, tophat_kernel)
    tophat = cv2.morphologyEx(denoised, cv2.MORPH_TOPHAT, kernel)
    # laplacian
    lap = cv2.Laplacian(denoised, cv2.CV_64F, ksize=3)
    lap_normalized = cv2.normalize(lap, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    combined = cv2.addWeighted(denoised, 0.6, tophat, 0.2, 0)
    combined = cv2.addWeighted(combined, 0.7, lap_normalized, 0.3, 0)
    clahe = cv2.createCLAHE(clipLimit=clahe_clip, tileGridSize=(8,8))
    enhanced = clahe.apply(combined)
    return enhanced

results = []

for tk in tophat_kernels:
    for cc in clahe_clip_limits:
        pre = preprocess_for_tune(gray_orig, tophat_kernel=tk, clahe_clip=cc)
        for ma in min_areas:
            for mc in min_circularities:
                params = cv2.SimpleBlobDetector_Params()
                params.minThreshold = 5
                params.maxThreshold = 255
                params.filterByArea = True
                params.minArea = ma
                params.maxArea = 8000
                params.filterByCircularity = True
                params.minCircularity = mc
                params.filterByInertia = True
                params.minInertiaRatio = 0.05
                params.filterByConvexity = False

                detector = cv2.SimpleBlobDetector_create(params)
                kps = detector.detect(pre)

                # score: prefer combos that detect a kp near expected_center, and more kps overall
                hit = 0
                for kp in kps:
                    if math.hypot(kp.pt[0] - expected_center[0], kp.pt[1] - expected_center[1]) <= hit_radius:
                        hit = 1
                        break
                score = hit * 10 + len(kps) * 0.5

                # save visualization for manual review
                vis = cv2.cvtColor(pre, cv2.COLOR_GRAY2BGR)
                for kp in kps:
                    x, y = int(kp.pt[0]), int(kp.pt[1])
                    r = int(kp.size / 2)
                    cv2.circle(vis, (x, y), r, (0, 255, 0), 2)
                fn = OUT_DIR / f'res_tk{tk[0]}_cc{cc}_ma{ma}_mc{mc}.png'
                cv2.imwrite(str(fn), vis)
                results.append({'tophat': tk, 'clahe': cc, 'minArea': ma, 'minCircularity': mc, 'count': len(kps), 'hit': hit, 'score': score, 'file': fn})

# pick best by score then smallest false_positive proxy
results_sorted = sorted(results, key=lambda r: (-r['score'], -r['count']))
best = results_sorted[0]

with open(OUT_DIR / 'detailed_summary.txt', 'w', encoding='utf-8') as f:
    f.write('tophat\tclahe\tminArea\tminCircularity\tcount\thit\tscore\tfile\n')
    for r in results_sorted:
        f.write(f"{r['tophat']}\t{r['clahe']}\t{r['minArea']}\t{r['minCircularity']}\t{r['count']}\t{r['hit']}\t{r['score']}\t{r['file'].name}\n")
    f.write('\nBEST:\n')
    f.write(str(best) + '\n')

print('搜索完成，结果保存在', OUT_DIR)
print('最佳参数:', best)
