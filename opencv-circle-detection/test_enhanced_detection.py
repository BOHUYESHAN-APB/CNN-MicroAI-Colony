import cv2
import numpy as np
from pathlib import Path
import logging
from core.enhanced_detector import EnhancedCircleDetector, SubstanceType
from core.models import SubstanceTypeEnum
import time

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def compare_detectors(image_path_str: str):
    """
    比较原始检测器和增强检测器的性能
    """
    logger.info(f"开始比较检测器性能: {image_path_str}")

    # 读取图像
    img_bytes = np.fromfile(image_path_str, dtype=np.uint8)
    original_image = cv2.imdecode(img_bytes, cv2.IMREAD_COLOR)

    if original_image is None:
        logger.error(f"无法读取图像: {image_path_str}")
        return

    # 初始化增强检测器
    enhanced_detector = EnhancedCircleDetector(
        plate_diameter_mm=90.0, 
        filter_paper_diameter_mm=6.0, 
        hole_diameter_mm=6.0
    )

    # 测试增强检测器
    logger.info("=== 增强检测器测试 ===")
    start_time = time.time()
    
    # 检测培养皿
    dishes = enhanced_detector.detect_petri_dishes(original_image.copy())
    detection_time = time.time() - start_time
    
    logger.info(f"培养皿检测用时: {detection_time:.2f}秒")
    logger.info(f"检测到培养皿数量: {len(dishes)}")
    
    if not dishes:
        logger.warning("未检测到培养皿，无法继续测试")
        return

    # 分析第一个培养皿
    dish = dishes[0]
    logger.info(f"培养皿中心: {dish.center}, 半径: {dish.radius}px")
    logger.info(f"标定比例: {enhanced_detector.px_per_mm:.2f}px/mm")

    # 分析培养皿内容
    start_time = time.time()
    detection_mode, substance_type, detected_substances = enhanced_detector.analyze_dish_contents(
        original_image.copy(), dish
    )
    analysis_time = time.time() - start_time
    
    logger.info(f"物质分析用时: {analysis_time:.2f}秒")
    logger.info(f"检测模式: {detection_mode.name}")
    logger.info(f"物质类型: {substance_type.name}")
    logger.info(f"检测到物质数量: {len(detected_substances)}")
    
    # 详细报告每个检测到的物质
    for i, substance in enumerate(detected_substances):
        logger.info(f"  物质 #{i+1}: 中心{substance.center}, 半径{substance.radius}px, "
                   f"类型{substance.substance_type.name}, 得分{substance.detection_score:.3f}")

    # 创建可视化结果
    result_image = visualize_detection_results(
        original_image.copy(), dish, detected_substances, 
        f"Enhanced Detection - {Path(image_path_str).name}"
    )
    
    return result_image, len(detected_substances)

def visualize_detection_results(image: np.ndarray, dish, substances, title: str) -> np.ndarray:
    """可视化检测结果"""
    result = image.copy()
    
    # 绘制培养皿
    cv2.circle(result, dish.center, dish.radius, (0, 255, 0), 3)
    cv2.putText(result, f"Dish R={dish.radius}px", 
                (dish.center[0]-50, dish.center[1]-dish.radius-10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
    
    # 绘制检测到的物质
    colors = [(255, 0, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255), (0, 255, 255)]
    
    for i, substance in enumerate(substances):
        color = colors[i % len(colors)]
        
        # 绘制物质圆圈
        cv2.circle(result, substance.center, substance.radius, color, 2)
        
        # 绘制中心点
        cv2.circle(result, substance.center, 3, color, -1)
        
        # 添加标签
        label = f"{substance.substance_type.name} #{i+1}"
        score_label = f"Score: {substance.detection_score:.2f}"
        
        cv2.putText(result, label, 
                    (substance.center[0]+substance.radius+5, substance.center[1]-10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        cv2.putText(result, score_label, 
                    (substance.center[0]+substance.radius+5, substance.center[1]+5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)
    
    # 添加总体信息
    info_text = f"Detected: {len(substances)} substances"
    cv2.putText(result, info_text, (10, 30), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    
    # 显示结果
    cv2.imshow(title, result)
    cv2.waitKey(0)
    cv2.destroyWindow(title)
    
    return result

def test_parameter_sensitivity():
    """测试参数敏感性"""
    logger.info("=== 参数敏感性测试 ===")
    
    test_dir = Path(__file__).parent / "test_images"
    if not test_dir.is_dir():
        logger.error(f"测试图像目录不存在: {test_dir}")
        return

    image_files = list(test_dir.glob("*.jpg")) + list(test_dir.glob("*.png"))
    if not image_files:
        logger.warning("未找到测试图像")
        return

    # 测试不同的参数配置
    param_configs = [
        {"filter_paper_diameter_mm": 6.0, "hole_diameter_mm": 6.0},
        {"filter_paper_diameter_mm": 5.0, "hole_diameter_mm": 5.0},
        {"filter_paper_diameter_mm": 7.0, "hole_diameter_mm": 7.0},
    ]
    
    results_summary = []
    
    for config in param_configs:
        logger.info(f"测试配置: {config}")
        config_results = []
        
        for img_file in image_files[:2]:  # 只测试前2张图像
            detector = EnhancedCircleDetector(**config)
            
            img_bytes = np.fromfile(str(img_file), dtype=np.uint8)
            image = cv2.imdecode(img_bytes, cv2.IMREAD_COLOR)
            
            if image is None:
                continue
                
            # 检测培养皿
            dishes = detector.detect_petri_dishes(image.copy())
            if not dishes:
                config_results.append(0)
                continue
                
            # 分析内容
            dish = dishes[0]
            _, _, substances = detector.analyze_dish_contents(image.copy(), dish)
            config_results.append(len(substances))
            
        avg_detections = np.mean(config_results) if config_results else 0
        results_summary.append((config, avg_detections))
        logger.info(f"平均检测数量: {avg_detections:.1f}")
    
    # 报告最佳配置
    best_config, best_score = max(results_summary, key=lambda x: x[1])
    logger.info(f"最佳配置: {best_config}, 平均检测数量: {best_score:.1f}")

def main():
    """主测试函数"""
    logger.info("开始增强检测器测试")
    
    test_dir = Path(__file__).parent / "test_images"
    if not test_dir.is_dir():
        logger.error(f"测试图像目录不存在: {test_dir}")
        return

    image_files = list(test_dir.glob("*.jpg")) + list(test_dir.glob("*.png"))
    if not image_files:
        logger.warning("未找到测试图像")
        return

    logger.info(f"找到 {len(image_files)} 个测试图像")

    total_detections = 0
    processed_images = 0

    for img_file in image_files:
        try:
            result_image, detection_count = compare_detectors(str(img_file))
            total_detections += detection_count
            processed_images += 1
            
            logger.info(f"图像 {img_file.name}: 检测到 {detection_count} 个物质")
            
            # 询问是否继续
            user_input = input(f"已处理 '{img_file.name}'. 按 Enter 继续, 'q' 退出, 's' 跳过参数测试: ")
            if user_input.lower() == 'q':
                break
            elif user_input.lower() == 's':
                continue
                
        except Exception as e:
            logger.error(f"处理图像 {img_file.name} 时发生错误: {e}")
            continue

    # 输出总结
    if processed_images > 0:
        avg_detections = total_detections / processed_images
        logger.info(f"=== 测试总结 ===")
        logger.info(f"处理图像数量: {processed_images}")
        logger.info(f"总检测数量: {total_detections}")
        logger.info(f"平均每张图像检测数量: {avg_detections:.2f}")
        
        # 运行参数敏感性测试
        if processed_images >= 2:
            test_parameter_sensitivity()
    
    cv2.destroyAllWindows()
    logger.info("增强检测器测试完成")

if __name__ == "__main__":
    main()