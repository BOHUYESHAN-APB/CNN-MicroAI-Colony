"""
分析 debug 中间图像并对 adaptiveThreshold 做多组参数试验。
默认对路径 opencv-circle-detection/test_outputs/debug/<image_basename>/ 下的 preproc_*.png 运行。
会在同目录下创建子目录 results_<param_name> 保存 mask、opened、closed 和 overlay 图。

用法：
python tools/analyze_debug_images.py --debug-dir "opencv-circle-detection/test_outputs/debug/OIP-C"

"""
import argparse
import os
import glob
import cv2
import numpy as np


def analyze(debug_dir: str):
    os.makedirs(debug_dir, exist_ok=True)
    preproc_files = glob.glob(os.path.join(debug_dir, 'preproc_*.png'))
    if not preproc_files:
        print('找不到 preproc_*.png，debug 目录：', debug_dir)
        return 2

    preproc_path = preproc_files[0]
    img = cv2.imread(preproc_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        print('无法读取预处理图像:', preproc_path)
        return 3

    # 三组参数：保守、中等、激进
    param_sets = [
        {'name': 'conservative', 'block': 51, 'C': 10, 'kernel': 3, 'circ_thresh': 0.45},
        {'name': 'moderate', 'block': 31, 'C': 8, 'kernel': 3, 'circ_thresh': 0.35},
        {'name': 'aggressive', 'block': 15, 'C': 4, 'kernel': 5, 'circ_thresh': 0.25}
    ]

    # radius bounds: 从经验值推测；可手动调整
    min_radius_px = 5
    max_radius_px = 80

    results = []

    for p in param_sets:
        name = p['name']
        out_dir = os.path.join(debug_dir, f'results_{name}')
        os.makedirs(out_dir, exist_ok=True)

        block = p['block']
        if block % 2 == 0:
            block += 1
        C = p['C']

        adaptive = cv2.adaptiveThreshold(img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                         cv2.THRESH_BINARY_INV, block, C)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (p['kernel'], p['kernel']))
        opened = cv2.morphologyEx(adaptive, cv2.MORPH_OPEN, kernel, iterations=1)
        closed = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, kernel, iterations=1)

        contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # overlay on color
        overlay = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        candidate_list = []

        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area <= 0:
                continue
            perim = cv2.arcLength(cnt, True)
            if perim == 0:
                continue
            circ = 4 * np.pi * area / (perim * perim)
            (cx, cy), r = cv2.minEnclosingCircle(cnt)
            r_i = int(r)
            if r_i < min_radius_px or r_i > max_radius_px:
                continue
            # area threshold relative to min_radius
            if area < np.pi * (max(3, min_radius_px * 0.5) ** 2):
                continue
            if circ < p['circ_thresh']:
                continue
            candidate_list.append({'center': (int(cx), int(cy)), 'radius': r_i, 'circ': circ, 'area': area})
            cv2.drawContours(overlay, [cnt], -1, (0, 255, 0), 1)
            cv2.circle(overlay, (int(cx), int(cy)), r_i, (0, 0, 255), 2)

        # Save images
        cv2.imwrite(os.path.join(out_dir, f'adaptive_{name}.png'), adaptive)
        cv2.imwrite(os.path.join(out_dir, f'opened_{name}.png'), opened)
        cv2.imwrite(os.path.join(out_dir, f'closed_{name}.png'), closed)
        cv2.imwrite(os.path.join(out_dir, f'overlay_{name}.png'), overlay)

        results.append({'name': name, 'candidates': candidate_list, 'count': len(candidate_list), 'params': p})

        print(f"Params {name}: block={block}, C={C}, kernel={p['kernel']}, circ_thresh={p['circ_thresh']} -> candidates={len(candidate_list)}")
        if candidate_list:
            for c in candidate_list:
                print(f" - center={c['center']} r={c['radius']} circ={c['circ']:.2f} area={int(c['area'])}")

    # pick best by count (then by avg circularity)
    best = None
    for r in results:
        if best is None:
            best = r
            continue
        if r['count'] > best['count']:
            best = r
        elif r['count'] == best['count']:
            # tiebreaker: mean circularity
            mean_r = np.mean([c['circ'] for c in r['candidates']]) if r['candidates'] else 0
            mean_b = np.mean([c['circ'] for c in best['candidates']]) if best['candidates'] else 0
            if mean_r > mean_b:
                best = r

    print('\n== Summary ==')
    for r in results:
        print(f"{r['name']}: {r['count']} candidates")
    if best:
        print(f"Best: {best['name']} (count={best['count']}) params={best['params']} )")
        # copy overlay to best_overlay.png
        try:
            best_overlay = os.path.join(debug_dir, f'results_{best['name']}', f'overlay_{best['name']}.png')
            out_best = os.path.join(debug_dir, '..', f'out_best_{os.path.basename(debug_dir)}.png')
            out_best = os.path.normpath(out_best)
            cv2.imwrite(out_best, cv2.imread(best_overlay))
            print('Saved best overlay to', out_best)
        except Exception as e:
            print('无法保存 best overlay:', e)

    return 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--debug-dir', help='debug 目录路径', default='opencv-circle-detection/test_outputs/debug/OIP-C')
    args = parser.parse_args()
    analyze(args.debug_dir)
