import cv2
import numpy as np
from pathlib import Path
import logging
from core.detector import CircleDetector
# Colony and PetriDish models are still useful for type hinting if needed,
# but the main interaction will be with the dicts returned by the pipeline.
from core.models import SubstanceTypeEnum # Import this if you want to check substance types

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def process_image_and_display(image_path_str: str, detector_instance: CircleDetector):
    """
    处理单张图片，使用 detector 的 process_image_pipeline 方法，并显示结果。
    """
    logger.info(f"开始处理图片: {image_path_str}")

    # 使用 OpenCV 读取图像，确保能处理中文路径
    img_bytes = np.fromfile(image_path_str, dtype=np.uint8)
    original_image = cv2.imdecode(img_bytes, cv2.IMREAD_COLOR)

    if original_image is None:
        logger.error(f"无法读取或解码图像: {image_path_str}")
        return

    # 调用新的处理流程
    # process_image_pipeline returns: (绘制结果的图像, 检测结果列表, 附加信息)
    processed_image_output, detection_results_list, extra_info_dict = \
        detector_instance.process_image_pipeline(original_image.copy())

    if processed_image_output is None:
        logger.error(f"图像处理流程未能返回有效图像: {image_path_str}")
        # Fallback to show original image if processing failed to produce an output image
        cv2.imshow(f"Original Image (Processing Failed) - {Path(image_path_str).name}", original_image)
        cv2.waitKey(0)
        return

    # 打印一些摘要信息到控制台
    logger.info(f"--- 检测摘要 for {Path(image_path_str).name} ---")
    logger.info(f"培养皿检测数量: {extra_info_dict.get('petri_dishes_detected', 0)}")
    logger.info(f"总物质点检测数量: {extra_info_dict.get('substances_detected_total', 0)}")
    logger.info(f"总抑菌圈检测数量: {extra_info_dict.get('inhibition_zones_detected_total', 0)}")
    px_per_mm = extra_info_dict.get('px_per_mm')
    if px_per_mm:
        logger.info(f"标定像素/毫米: {px_per_mm:.2f}")
    else:
        logger.warning("像素/毫米 未能成功标定。")

    # 详细打印每个培养皿的信息
    active_dish_details = extra_info_dict.get('active_dish_details', [])
    if active_dish_details:
        for i, dish_detail in enumerate(active_dish_details):
            dish_info = dish_detail.get('dish_info', {})
            mode = dish_detail.get('detection_mode', 'N/A')
            s_type = dish_detail.get('substance_type', 'N/A')
            s_count = dish_detail.get('substances_count', 0)
            logger.info(
                f"  培养皿 #{i+1}: 中心({dish_info.get('center')}), R={dish_info.get('radius')}px | "
                f"模式: {mode} | 类型: {s_type} | 物质点: {s_count}"
            )
            zones_results_for_dish = dish_detail.get('zones_results', [])
            for z_idx, zone_res in enumerate(zones_results_for_dish):
                substance_info = zone_res.get('substance', {})
                primary_zone = zone_res.get('primary_zone')
                log_msg = f"    物质点 #{z_idx+1} at {substance_info.get('center')} R={substance_info.get('radius')}px: "
                if primary_zone:
                    log_msg += (f"抑菌圈 at {primary_zone.get('center')} R={primary_zone.get('radius')}px, "
                                f"Diam={primary_zone.get('diameter_mm', 0):.2f}mm")
                else:
                    log_msg += "未检测到主抑菌圈。"
                logger.info(log_msg)
    else:
         logger.info("未找到详细的培养皿处理信息。")


    # 显示带有所有绘制结果的图像
    # The processed_image_output already contains all drawings.
    window_title = f"Detection Result - {Path(image_path_str).name}"
    cv2.imshow(window_title, processed_image_output)
    cv2.waitKey(0) # 等待用户按键后关闭当前图像窗口
    try:
        cv2.destroyWindow(window_title) # 只关闭当前窗口
    except cv2.error as e:
        # 如果窗口已经被用户手动关闭，destroyWindow会报错，可以忽略或记录
        logger.warning(f"关闭窗口 '{window_title}' 时发生错误 (可能已被手动关闭): {e}")


def main():
    # 初始化检测器一次，可以传入参数
    detector = CircleDetector(plate_diameter_mm=90.0, filter_paper_diameter_mm=6.0, hole_diameter_mm=6.0)

    test_dir = Path(__file__).parent / "test_images" # More robust path to test_images
    if not test_dir.is_dir():
        logger.error(f"测试图像目录 '{test_dir}' 不存在或不是一个目录。请确保它在脚本同级目录下。")
        return

    image_files = list(test_dir.glob("*.jpg")) + list(test_dir.glob("*.png")) + list(test_dir.glob("*.bmp"))
    if not image_files:
        logger.warning(f"在 '{test_dir}' 中没有找到支持的图像文件 (jpg, png, bmp)。")
        return

    logger.info(f"找到 {len(image_files)} 个测试图像在 '{test_dir}'")

    for img_file_path in image_files:
        process_image_and_display(str(img_file_path), detector)
        
        # 询问是否继续处理下一张图片
        user_input = input(f"已处理 '{img_file_path.name}'. 按 Enter 继续下一张, 或输入 'q' 退出: ")
        if user_input.lower() == 'q':
            logger.info("用户选择退出。")
            break
    
    logger.info("所有测试图像处理完毕 (或用户提前退出)。")
    cv2.destroyAllWindows() # 关闭所有遗留的OpenCV窗口

if __name__ == "__main__":
    main()