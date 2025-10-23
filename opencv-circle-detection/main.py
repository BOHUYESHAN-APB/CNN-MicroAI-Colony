import sys
import argparse
from pathlib import Path
import cv2
import numpy as np
from PySide6.QtWidgets import QApplication

from gui.main_window import MainWindow
from core.detector import CircleDetector


def run_headless(image_path: str, output_path: str = 'out_annotated.jpg') -> int:
    """
    在无 GUI 的模式下运行检测管线，使用已有的 CircleDetector.process_image_pipeline。
    返回非零表示出错。
    """
    img = cv2.imdecode(np.fromfile(image_path, dtype=np.uint8), cv2.IMREAD_UNCHANGED)
    if img is None:
        print(f"无法读取图像: {image_path}")
        return 2

    detector = CircleDetector()
    # 如果存在输出路径，基于输入图像名创建 debug 目录
    try:
        image_basename = Path(image_path).stem
        debug_dir = Path('opencv-circle-detection') / 'test_outputs' / 'debug' / image_basename
        detector.debug_dir = str(debug_dir)
    except Exception:
        detector.debug_dir = None
    annotated, results, info = detector.process_image_pipeline(img)

    # 保存带标注的图像（使用 imencode + tofile 支持 Windows 路径）
    ext = Path(output_path).suffix or '.jpg'
    ok, buf = cv2.imencode(ext, annotated)
    if ok:
        try:
            buf.tofile(output_path)
            print(f"已保存带标注图像: {output_path}")
        except Exception as e:
            print(f"保存图像失败: {e}")
            return 3
    else:
        print("图像编码失败，无法保存输出图像")
        return 4

    # 简要打印检测结果统计
    print("检测摘要:")
    print(f"- 培养皿数: {info.get('petri_dishes_detected', 0)}")
    print(f"- 物质总数: {info.get('substances_detected_total', 0)}")
    print(f"- 抑菌圈数: {info.get('inhibition_zones_detected_total', 0)}")
    return 0


def main():
    parser = argparse.ArgumentParser(description='opencv-circle-detection 主程序 (GUI 或 headless)')
    parser.add_argument('--image', help='如果提供，则以无 GUI 模式运行检测，输入图像路径')
    parser.add_argument('--output', help='无 GUI 模式下的输出图像路径', default='out_annotated.jpg')
    args, remaining = parser.parse_known_args()

    if args.image:
        exit_code = run_headless(args.image, args.output)
        sys.exit(exit_code)

    # 否则启动 GUI
    try:
        app = QApplication(sys.argv)
        app.setStyle('Fusion')
        window = MainWindow()
        window.show()
        sys.exit(app.exec())
    except Exception as e:
        print(f"程序运行出错: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    main()