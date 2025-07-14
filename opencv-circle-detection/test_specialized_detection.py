import cv2
import numpy as np
from pathlib import Path
import logging
from core.specialized_detector import SpecializedInhibitionDetector, DetectionChallenge
from core.enhanced_detector import EnhancedCircleDetector
import time

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def analyze_image_challenges(image_path: str) -> DetectionChallenge:
    """
    分析图像特征，自动判断主要检测挑战类型
    """
    img_bytes = np.fromfile(image_path, dtype=np.uint8)
    image = cv2.imdecode(img_bytes, cv2.IMREAD_COLOR)
    
    if image is None:
        return DetectionChallenge.TRANSPARENT_HOLE_AND_ZONE
    
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # 分析图像特征
    mean_brightness = np.mean(gray)
    std_brightness = np.std(gray)
    
    # 检测圆形结构的数量（可能的气泡）
    circles = cv2.HoughCircles(
        gray, cv2.HOUGH_GRADIENT, dp=1, minDist=30,
        param1=50, param2=30, minRadius=5, maxRadius=50
    )
    
    bubble_count = len(circles[0]) if circles is not None else 0
    
    # 分析颜色变化（有色菌落背景）
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    color_variance = np.var(hsv[:,:,1])  # 饱和度方差
    
    # 判断主要挑战类型
    if bubble_count > 10:
        logger.info(f"检测到大量圆形结构({bubble_count}个)，判断为气泡干扰")
        return DetectionChallenge.BUBBLE_INTERFERENCE
    elif color_variance > 800:
        logger.info(f"检测到高颜色变化(方差{color_variance:.1f})，判断为有色背景菌落")
        return DetectionChallenge.COLORED_BACKGROUND_COLONIES
    elif std_brightness < 15:
        logger.info(f"检测到低对比度(标准差{std_brightness:.1f})，判断为透明目标")
        return DetectionChallenge.TRANSPARENT_HOLE_AND_ZONE
    else:
        logger.info(f"检测到多层次对比度，判断为多级梯度透明")
        return DetectionChallenge.MULTI_GRADIENT_TRANSPARENCY

def test_specialized_detection(image_path: str):
    """
    测试针对特殊挑战的检测算法
    """
    logger.info(f"开始专门检测测试: {image_path}")
    
    # 读取图像
    img_bytes = np.fromfile(image_path, dtype=np.uint8)
    original_image = cv2.imdecode(img_bytes, cv2.IMREAD_COLOR)
    
    if original_image is None:
        logger.error(f"无法读取图像: {image_path}")
        return
    
    # 分析图像挑战类型
    challenge_type = analyze_image_challenges(image_path)
    logger.info(f"识别的主要挑战: {challenge_type.name}")
    
    # 首先使用增强检测器检测培养皿
    enhanced_detector = EnhancedCircleDetector()
    dishes = enhanced_detector.detect_petri_dishes(original_image.copy())
    
    if not dishes:
        logger.warning("未检测到培养皿，无法继续专门检测")
        return
    
    dish = dishes[0]
    px_per_mm = enhanced_detector.px_per_mm
    
    logger.info(f"培养皿: 中心{dish.center}, 半径{dish.radius}px, 标定{px_per_mm:.2f}px/mm")
    
    # 使用专门检测器
    specialized_detector = SpecializedInhibitionDetector(px_per_mm)
    
    start_time = time.time()
    detection_result = specialized_detector.detect_with_challenge_awareness(
        original_image.copy(), challenge_type, dish
    )
    detection_time = time.time() - start_time
    
    logger.info(f"专门检测用时: {detection_time:.2f}秒")
    
    substances = detection_result.get('substances', [])
    zones = detection_result.get('zones', [])
    confidence = detection_result.get('confidence', 0.0)
    
    logger.info(f"检测结果: {len(substances)}个物质, {len(zones)}个抑菌圈, 置信度{confidence:.3f}")
    
    # 详细报告
    for i, substance in enumerate(substances):
        logger.info(f"  物质 #{i+1}: 中心{substance.center}, 半径{substance.radius}px, "
                   f"类型{substance.substance_type.name}, 得分{substance.detection_score:.3f}")
    
    for i, zone in enumerate(zones):
        logger.info(f"  抑菌圈 #{i+1}: 中心{zone['center']}, 半径{zone['radius']}px, "
                   f"直径{zone['diameter_mm']:.2f}mm, 置信度{zone['confidence']:.3f}")
    
    # 可视化结果
    result_image = visualize_specialized_results(
        original_image.copy(), dish, substances, zones, challenge_type
    )
    
    return result_image, len(substances), len(zones), confidence

def visualize_specialized_results(image: np.ndarray, dish, substances, zones, 
                                challenge_type: DetectionChallenge) -> np.ndarray:
    """可视化专门检测的结果"""
    result = image.copy()
    
    # 绘制培养皿
    cv2.circle(result, dish.center, dish.radius, (0, 255, 0), 3)
    
    # 绘制挑战类型标识
    challenge_color = {
        DetectionChallenge.TRANSPARENT_HOLE_AND_ZONE: (255, 255, 0),
        DetectionChallenge.MULTI_GRADIENT_TRANSPARENCY: (255, 0, 255),
        DetectionChallenge.BUBBLE_INTERFERENCE: (0, 255, 255),
        DetectionChallenge.COLORED_BACKGROUND_COLONIES: (128, 255, 128)
    }
    
    color = challenge_color.get(challenge_type, (255, 255, 255))
    cv2.putText(result, f"Challenge: {challenge_type.name}", 
                (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
    
    # 绘制检测到的物质（使用特殊颜色标识透明目标）
    for i, substance in enumerate(substances):
        # 透明目标使用虚线圆圈
        if challenge_type == DetectionChallenge.TRANSPARENT_HOLE_AND_ZONE:
            # 绘制虚线圆圈
            angles = np.linspace(0, 2*np.pi, 32)
            points = []
            for j, angle in enumerate(angles):
                if j % 2 == 0:  # 每隔一个点绘制，形成虚线效果
                    x = int(substance.center[0] + substance.radius * np.cos(angle))
                    y = int(substance.center[1] + substance.radius * np.sin(angle))
                    points.append((x, y))
            
            for j in range(0, len(points)-1, 2):
                cv2.line(result, points[j], points[j+1], (0, 255, 255), 2)
        else:
            cv2.circle(result, substance.center, substance.radius, (255, 0, 0), 2)
        
        # 标记中心
        cv2.circle(result, substance.center, 3, (0, 0, 255), -1)
        
        # 添加标签
        label = f"S{i+1}:{substance.detection_score:.2f}"
        cv2.putText(result, label, 
                    (substance.center[0]+substance.radius+5, substance.center[1]),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    
    # 绘制抑菌圈（使用半透明覆盖）
    overlay = result.copy()
    for i, zone in enumerate(zones):
        center = zone['center']
        radius = zone['radius']
        confidence = zone.get('confidence', 0.5)
        
        # 根据置信度调整颜色透明度
        alpha = min(confidence, 0.7)
        cv2.circle(overlay, center, radius, (0, 255, 0), 2)
        cv2.circle(overlay, center, radius, (0, 255, 0), -1)
        
        # 添加抑菌圈信息
        zone_label = f"Z{i+1}:{zone['diameter_mm']:.1f}mm"
        cv2.putText(result, zone_label, 
                    (center[0]+radius+5, center[1]+15),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
    
    # 混合半透明抑菌圈
    if zones:
        result = cv2.addWeighted(result, 0.7, overlay, 0.3, 0)
    
    # 添加检测统计信息
    stats_text = f"Substances: {len(substances)}, Zones: {len(zones)}"
    cv2.putText(result, stats_text, (10, 60), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    
    # 显示结果
    window_title = f"Specialized Detection - {Path(image_path).name}"
    cv2.imshow(window_title, result)
    cv2.waitKey(0)
    cv2.destroyWindow(window_title)
    
    return result

def compare_detection_methods(image_path: str):
    """
    比较标准检测和专门检测的效果
    """
    logger.info(f"=== 检测方法比较: {Path(image_path).name} ===")
    
    # 读取图像
    img_bytes = np.fromfile(image_path, dtype=np.uint8)
    original_image = cv2.imdecode(img_bytes, cv2.IMREAD_COLOR)
    
    if original_image is None:
        logger.error(f"无法读取图像: {image_path}")
        return
    
    # 增强检测器（标准方法）
    logger.info("--- 标准增强检测 ---")
    enhanced_detector = EnhancedCircleDetector()
    dishes = enhanced_detector.detect_petri_dishes(original_image.copy())
    
    if not dishes:
        logger.warning("标准方法未检测到培养皿")
        return
    
    dish = dishes[0]
    _, _, standard_substances = enhanced_detector.analyze_dish_contents(original_image.copy(), dish)
    
    logger.info(f"标准方法检测到 {len(standard_substances)} 个物质")
    
    # 专门检测器
    logger.info("--- 专门挑战检测 ---")
    challenge_type = analyze_image_challenges(image_path)
    specialized_detector = SpecializedInhibitionDetector(enhanced_detector.px_per_mm)
    
    specialized_result = specialized_detector.detect_with_challenge_awareness(
        original_image.copy(), challenge_type, dish
    )
    
    specialized_substances = specialized_result.get('substances', [])
    specialized_zones = specialized_result.get('zones', [])
    
    logger.info(f"专门方法检测到 {len(specialized_substances)} 个物质, {len(specialized_zones)} 个抑菌圈")
    
    # 比较结果
    logger.info("--- 方法比较总结 ---")
    logger.info(f"标准方法物质检测: {len(standard_substances)}")
    logger.info(f"专门方法物质检测: {len(specialized_substances)}")
    logger.info(f"专门方法抑菌圈检测: {len(specialized_zones)}")
    
    # 计算改进程度
    if len(standard_substances) > 0:
        substance_improvement = (len(specialized_substances) - len(standard_substances)) / len(standard_substances) * 100
        logger.info(f"物质检测改进: {substance_improvement:+.1f}%")
    else:
        if len(specialized_substances) > 0:
            logger.info("物质检测改进: 从0个提升到有检测结果")
        else:
            logger.info("物质检测改进: 两种方法都未检测到")

def main():
    """主测试函数"""
    logger.info("开始专门检测算法测试")
    
    test_dir = Path(__file__).parent / "test_images"
    if not test_dir.is_dir():
        logger.error(f"测试图像目录不存在: {test_dir}")
        return
    
    image_files = list(test_dir.glob("*.jpg")) + list(test_dir.glob("*.png"))
    if not image_files:
        logger.warning("未找到测试图像")
        return
    
    logger.info(f"找到 {len(image_files)} 个测试图像")
    
    total_substances = 0
    total_zones = 0
    total_confidence = 0.0
    processed_images = 0
    
    for img_file in image_files:
        try:
            logger.info(f"\n{'='*50}")
            logger.info(f"处理图像: {img_file.name}")
            
            # 专门检测测试
            result_image, substance_count, zone_count, confidence = test_specialized_detection(str(img_file))
            
            total_substances += substance_count
            total_zones += zone_count
            total_confidence += confidence
            processed_images += 1
            
            # 比较不同方法
            compare_detection_methods(str(img_file))
            
            # 询问是否继续
            user_input = input(f"\n已处理 '{img_file.name}'. 按 Enter 继续, 'q' 退出: ")
            if user_input.lower() == 'q':
                break
                
        except Exception as e:
            logger.error(f"处理图像 {img_file.name} 时发生错误: {e}")
            continue
    
    # 输出总结
    if processed_images > 0:
        avg_substances = total_substances / processed_images
        avg_zones = total_zones / processed_images
        avg_confidence = total_confidence / processed_images
        
        logger.info(f"\n{'='*50}")
        logger.info(f"=== 专门检测算法测试总结 ===")
        logger.info(f"处理图像数量: {processed_images}")
        logger.info(f"总物质检测数量: {total_substances}")
        logger.info(f"总抑菌圈检测数量: {total_zones}")
        logger.info(f"平均每张图像物质检测: {avg_substances:.2f}")
        logger.info(f"平均每张图像抑菌圈检测: {avg_zones:.2f}")
        logger.info(f"平均检测置信度: {avg_confidence:.3f}")
    
    cv2.destroyAllWindows()
    logger.info("专门检测算法测试完成")

if __name__ == "__main__":
    main()