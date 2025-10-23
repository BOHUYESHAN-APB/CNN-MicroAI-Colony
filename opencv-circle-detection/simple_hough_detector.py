"""
简单的基于 OpenCV HoughCircles 的抑菌圈 / 挖空检测示例脚本

用法示例：
python simple_hough_detector.py --image test_images/OIP-C.jpg --method hole --px-per-mm 10 --output out.jpg

说明：
- 这个脚本提供最小可运行的预处理 + Hough 圆检测流程，便于根据样本快速调参。
- 参数含义：method=hole|filter_paper，两者在预处理和半径范围上有细微差别。
"""
import argparse
import cv2
import numpy as np
import os
from typing import Tuple


def preprocess(img: np.ndarray, method: str) -> np.ndarray:
    # 转为灰度
    if img.ndim == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    else:
        gray = img.copy()

    # 轻度去噪与对比度增强
    gray = cv2.GaussianBlur(gray, (9, 9), 2)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    gray = clahe.apply(gray)

    # 对于挖空（透明）目标，做一次顶帽增强边缘；对于滤纸片法（实体暗/亮区域），可使用开运算清理背景
    if method == 'hole':
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))
        tophat = cv2.morphologyEx(gray, cv2.MORPH_TOPHAT, kernel)
        combined = cv2.addWeighted(gray, 0.7, tophat, 0.3, 0)
        return combined
    else:
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        opened = cv2.morphologyEx(gray, cv2.MORPH_OPEN, kernel)
        closed = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, kernel)
        return closed


def detect_circles(img: np.ndarray, dp: float, minDist: float, param1: int, param2: int, minRadius: int, maxRadius: int):
    # HoughCircles 需要 8bit 灰度图
    img8 = img if img.dtype == np.uint8 else cv2.normalize(img, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    circles = cv2.HoughCircles(img8, cv2.HOUGH_GRADIENT, dp=dp, minDist=minDist,
                               param1=param1, param2=param2,
                               minRadius=minRadius, maxRadius=maxRadius)
    if circles is None:
        return []
    circles = np.round(circles[0, :]).astype(int)
    return circles.tolist()


def annotate_and_save(orig: np.ndarray, circles, output_path: str, px_per_mm: float = 0.0):
    out = orig.copy()
    for (x, y, r) in circles:
        cv2.circle(out, (x, y), r, (0, 255, 0), 2)
        cv2.circle(out, (x, y), 2, (0, 0, 255), 3)
        if px_per_mm and px_per_mm > 0:
            diameter_mm = (2 * r) / px_per_mm
            text = f"{diameter_mm:.2f} mm"
        else:
            text = f"r={r}px"
        cv2.putText(out, text, (x - r, y - r - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)
    cv2.imwrite(output_path, out)
    print(f"Saved annotated image to: {output_path}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--image', required=True, help='输入图像路径')
    parser.add_argument('--method', choices=['hole', 'filter_paper'], default='hole', help='样本类型，影响预处理和半径搜索')
    parser.add_argument('--px-per-mm', type=float, default=0.0, help='像素每毫米，用于换算直径（可选）')
    parser.add_argument('--output', default='out.jpg', help='输出带标注的图像路径')
    parser.add_argument('--dp', type=float, default=1.0, help='Hough dp 参数')
    parser.add_argument('--min-dist', type=float, default=50.0, help='最小圆心距离')
    parser.add_argument('--param1', type=int, default=100, help='Canny 高阈值')
    parser.add_argument('--param2', type=int, default=30, help='Hough 阈值(越小越多候选)')
    parser.add_argument('--min-radius', type=int, default=10, help='最小半径(px)')
    parser.add_argument('--max-radius', type=int, default=200, help='最大半径(px)')
    args = parser.parse_args()

    if not os.path.exists(args.image):
        print('图像文件不存在:', args.image)
        return

    img = cv2.imdecode(np.fromfile(args.image, dtype=np.uint8), cv2.IMREAD_UNCHANGED)
    if img is None:
        print('无法读取图像，请确认路径和文件格式')
        return

    pre = preprocess(img, args.method)

    circles = detect_circles(pre, dp=args.dp, minDist=args.min_dist, param1=args.param1,
                             param2=args.param2, minRadius=args.min_radius, maxRadius=args.max_radius)

    print(f"Detected {len(circles)} circles")
    for i, c in enumerate(circles, 1):
        x, y, r = c
        if args.px_per_mm and args.px_per_mm > 0:
            print(f"{i}: center=({x},{y}) r={r}px -> d={2*r/args.px_per_mm:.2f} mm")
        else:
            print(f"{i}: center=({x},{y}) r={r}px")

    annotate_and_save(img if img.ndim == 3 else cv2.cvtColor(img, cv2.COLOR_GRAY2BGR), circles, args.output, args.px_per_mm)


if __name__ == '__main__':
    main()
