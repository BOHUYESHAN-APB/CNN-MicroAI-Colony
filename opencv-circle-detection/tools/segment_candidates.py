"""
针对 analyze_debug_images 的候选，尝试不同的分割策略（OTSU、INV-OTSU、adaptive small/large），
并对每个候选在 ROI 上计算评分（圆度 + 面积/距离权重），选择最优分割结果并保存 overlay。

用法示例：
python tools/segment_candidates.py --debug-dir "opencv-circle-detection/test_outputs/debug/OIP-C"

输出：
- 在 debug 目录下保存每个 candidate 的最佳分割 overlay，比如 results_aggressive/best_seg_cand0.png
- 在 debug 目录上级保存合成 best_overlays_to_root 文件 e.g. out_best_seg_OIP-C.png
"""

import argparse
import os
import glob
import cv2
import numpy as np


def score_contour(contour, substance_center_rel, min_zone_radius_px):
    area = cv2.contourArea(contour)
    perim = cv2.arcLength(contour, True)
    if perim == 0:
        return 0
    circ = 4 * np.pi * area / (perim * perim)
    (x_rel, y_rel), r = cv2.minEnclosingCircle(contour)
    dist = np.sqrt((x_rel - substance_center_rel[0])**2 + (y_rel - substance_center_rel[1])**2)
    # score: prefer higher circularity, larger area, closer to substance center
    score = circ * (area / (np.pi * (min_zone_radius_px**2))) * (1.0 / (1.0 + dist))
    return score, circ, area, r, (int(x_rel), int(y_rel))


def process_debug(debug_dir: str):
    # load preproc and results folder
    preproc_list = glob.glob(os.path.join(debug_dir, 'preproc_*.png'))
    if not preproc_list:
        print('没有找到 preproc 文件')
        return 2
    preproc_path = preproc_list[0]
    preproc = cv2.imread(preproc_path, cv2.IMREAD_GRAYSCALE)

    # read candidate overlay from results directories (any results_*) and parse candidate centers from overlay texts is hard
    # instead, run simple contour detection on closed images in each results_* to gather candidate centers
    result_dirs = [d for d in glob.glob(os.path.join(debug_dir, 'results_*')) if os.path.isdir(d)]
    all_candidates = []
    for rd in result_dirs:
        closed_files = glob.glob(os.path.join(rd, 'closed_*.png'))
        overlay_files = glob.glob(os.path.join(rd, 'overlay_*.png'))
        for cf in closed_files:
            closed = cv2.imread(cf, cv2.IMREAD_GRAYSCALE)
            contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            for cnt in contours:
                area = cv2.contourArea(cnt)
                if area < 10:
                    continue
                (cx, cy), r = cv2.minEnclosingCircle(cnt)
                cx_i, cy_i, r_i = int(cx), int(cy), int(r)
                all_candidates.append({'center': (cx_i, cy_i), 'radius': r_i, 'result_dir': rd})

    print('找到候选数量 (来自结果目录轮廓聚合):', len(all_candidates))
    if not all_candidates:
        print('没有候选，结束')
        return 0

    # 对每个 candidate 在 preproc 图上采 ROI 并尝试多种分割
    outputs = []
    h, w = preproc.shape[:2]
    for idx, cand in enumerate(all_candidates):
        cx, cy = cand['center']
        r = max(10, int(cand['radius'] * 4))  # search radius for zone detection
        x1 = max(0, cx - r)
        y1 = max(0, cy - r)
        x2 = min(w, cx + r)
        y2 = min(h, cy + r)
        roi = preproc[y1:y2, x1:x2]
        if roi is None or roi.size == 0:
            continue

        strategies = []
        # OTSU
        _, otsu = cv2.threshold(roi, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        strategies.append(('otsu', otsu))
        # INV OTSU
        _, inv_otsu = cv2.threshold(roi, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        strategies.append(('inv_otsu', inv_otsu))
        # adaptive small
        bl = 15 if roi.shape[0] > 50 else 7
        if bl % 2 == 0: bl += 1
        adapt_small = cv2.adaptiveThreshold(roi, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, bl, 4)
        strategies.append(('adapt_small', adapt_small))
        # adaptive large
        bl2 = 31 if roi.shape[0] > 100 else 15
        if bl2 % 2 == 0: bl2 += 1
        adapt_large = cv2.adaptiveThreshold(roi, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, bl2, 8)
        strategies.append(('adapt_large', adapt_large))

        best_score = 0
        best_img = None
        best_detail = None

        for name, mask in strategies:
            # morphology to clean
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3,3))
            closed = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
            contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            for cnt in contours:
                sc = score_contour(cnt, (roi.shape[1]/2, roi.shape[0]/2), max(5, int(r*0.2)))
                if sc:
                    score, circ, area, r_cont, center_rel = sc
                    if score > best_score:
                        best_score = score
                        # create overlay on full image coordinates
                        overlay_full = cv2.cvtColor(preproc, cv2.COLOR_GRAY2BGR)
                        # draw candidate region
                        cv2.circle(overlay_full, (cx, cy), int(r), (255,0,0), 1)
                        # draw contour at absolute positions
                        cnt_abs = cnt + np.array([[[x1, y1]]])
                        cv2.drawContours(overlay_full, [cnt_abs], -1, (0,255,0), 2)
                        # mark center
                        cx_abs = x1 + center_rel[0]
                        cy_abs = y1 + center_rel[1]
                        cv2.circle(overlay_full, (cx_abs, cy_abs), int(r_cont), (0,0,255), 2)
                        best_img = overlay_full
                        best_detail = (name, score, circ, area, (cx_abs, cy_abs), int(r_cont))

        if best_img is not None:
            out_dir = os.path.join(debug_dir, 'candidate_best')
            os.makedirs(out_dir, exist_ok=True)
            out_path = os.path.join(out_dir, f'best_cand_{idx}.png')
            cv2.imwrite(out_path, best_img)
            outputs.append({'idx': idx, 'best': best_detail, 'path': out_path})
            print(f'cand {idx} best: {best_detail} saved {out_path}')
        else:
            print(f'cand {idx} no valid segmentation')

    # 合并所有最佳 overlay 到一个图
    if outputs:
        merged = None
        for o in outputs:
            im = cv2.imread(o['path'])
            if merged is None:
                merged = im
            else:
                # put side by side
                merged = np.hstack((merged, im)) if merged.shape[0]==im.shape[0] else merged
        if merged is not None:
            out_root = os.path.normpath(os.path.join(debug_dir, '..', f'out_best_seg_{os.path.basename(debug_dir)}.png'))
            cv2.imwrite(out_root, merged)
            print('Saved merged best overlays to', out_root)

    return 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--debug-dir', default='opencv-circle-detection/test_outputs/debug/OIP-C')
    args = parser.parse_args()
    process_debug(args.debug_dir)
