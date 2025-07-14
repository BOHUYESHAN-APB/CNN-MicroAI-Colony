import cv2
import numpy as np
from pathlib import Path
import logging
from core.enhanced_detector import EnhancedCircleDetector
import time

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_enhanced_vs_original():
    """
    比较原始检测器和增强检测器的性能
    """
    logger.info("开始增强检测器对比测试")
    
    test_dir = Path(__file__).parent / "test_images"
    if not test_dir.is_dir():
        logger.error(f"测试图像目录不存在: {test_dir}")
        return
    
    image_files = list(test_dir.glob("*.jpg")) + list(test_dir.glob("*.png"))
    if not image_files:
        logger.warning("未找到测试图像")
        return
    
    logger.info(f"找到 {len(image_files)} 个测试图像")
    
    # 测试结果统计
    results = []
    
    for img_file in image_files:
        logger.info(f"\n{'='*60}")
        logger.info(f"测试图像: {img_file.name}")
        
        # 读取图像
        img_bytes = np.fromfile(str(img_file), dtype=np.uint8)
        original_image = cv2.imdecode(img_bytes, cv2.IMREAD_COLOR)
        
        if original_image is None:
            logger.error(f"无法读取图像: {img_file}")
            continue
        
        # 测试增强检测器
        logger.info("--- 增强检测器测试 ---")
        enhanced_detector = EnhancedCircleDetector()
        
        # 检测培养皿
        start_time = time.time()
        dishes = enhanced_detector.detect_petri_dishes(original_image.copy())
        dish_time = time.time() - start_time
        
        logger.info(f"培养皿检测用时: {dish_time:.3f}秒")
        logger.info(f"检测到培养皿: {len(dishes)}个")
        
        if not dishes:
            logger.warning("未检测到培养皿，跳过该图像")
            continue
        
        dish = dishes[0]
        logger.info(f"培养皿: 中心{dish.center}, 半径{dish.radius}px")
        logger.info(f"标定比例: {enhanced_detector.px_per_mm:.2f}px/mm")
        
        # 分析培养皿内容
        start_time = time.time()
        detection_mode, substance_type, substances = enhanced_detector.analyze_dish_contents(
            original_image.copy(), dish
        )
        analysis_time = time.time() - start_time
        
        logger.info(f"物质分析用时: {analysis_time:.3f}秒")
        logger.info(f"检测模式: {detection_mode.name}")
        logger.info(f"物质类型: {substance_type.name}")
        logger.info(f"检测到物质: {len(substances)}个")
        
        # 详细显示每个检测到的物质
        for i, substance in enumerate(substances):
            logger.info(f"  物质 #{i+1}: 中心{substance.center}, 半径{substance.radius}px, "
                       f"类型{substance.substance_type.name}, 得分{substance.detection_score:.3f}")
        
        # 可视化结果
        result_image = visualize_enhanced_results(
            original_image.copy(), dish, substances, img_file.name
        )
        
        # 记录结果
        result = {
            'image': img_file.name,
            'dish_detected': len(dishes) > 0,
            'substance_count': len(substances),
            'detection_mode': detection_mode.name,
            'substance_type': substance_type.name,
            'dish_time': dish_time,
            'analysis_time': analysis_time,
            'total_time': dish_time + analysis_time
        }
        results.append(result)
        
        # 询问是否继续
        user_input = input(f"\n已处理 '{img_file.name}'. 按 Enter 继续下一张, 'q' 退出: ")
        if user_input.lower() == 'q':
            break
    
    # 输出总结报告
    logger.info(f"\n{'='*60}")
    logger.info("=== 增强检测器测试总结 ===")
    
    if results:
        total_images = len(results)
        successful_detections = sum(1 for r in results if r['substance_count'] > 0)
        total_substances = sum(r['substance_count'] for r in results)
        avg_time = np.mean([r['total_time'] for r in results])
        
        logger.info(f"测试图像总数: {total_images}")
        logger.info(f"成功检测图像: {successful_detections} ({successful_detections/total_images*100:.1f}%)")
        logger.info(f"总检测物质数: {total_substances}")
        logger.info(f"平均每张图像检测: {total_substances/total_images:.2f}个物质")
        logger.info(f"平均处理时间: {avg_time:.3f}秒/张")
        
        # 按图像显示详细结果
        logger.info("\n详细结果:")
        for result in results:
            logger.info(f"  {result['image']}: {result['substance_count']}个物质, "
                       f"{result['detection_mode']}, {result['substance_type']}, "
                       f"{result['total_time']:.3f}秒")
    
    cv2.destroyAllWindows()
    logger.info("测试完成")

def visualize_enhanced_results(image: np.ndarray, dish, substances, image_name: str) -> np.ndarray:
    """可视化增强检测结果"""
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
    info_text = f"Enhanced Detection: {len(substances)} substances"
    cv2.putText(result, info_text, (10, 30), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    
    # 显示结果
    window_title = f"Enhanced Detection - {image_name}"
    cv2.imshow(window_title, result)
    cv2.waitKey(0)
    cv2.destroyWindow(window_title)
    
    return result

def analyze_detection_challenges():
    """
    分析检测挑战和改进建议
    """
    logger.info("\n=== 检测挑战分析 ===")
    
    challenges = [
        "1. 透明挖孔检测：需要基于微弱对比度和纹理变化",
        "2. 透明抑菌圈检测：需要检测平缓的亮度梯度变化", 
        "3. 气泡干扰过滤：需要区分真实目标和气泡伪影",
        "4. 有色背景处理：需要在复杂背景中提取目标",
        "5. 多级梯度识别：需要识别滤纸片法的多层透明环"
    ]
    
    improvements = [
        "✓ 已实现多策略检测组合",
        "✓ 已实现自适应阈值验证", 
        "✓ 已实现质量评分系统",
        "✓ 已实现非极大值抑制",
        "→ 可进一步优化透明目标特征提取",
        "→ 可增加机器学习辅助验证",
        "→ 可添加用户交互式标注功能"
    ]
    
    for challenge in challenges:
        logger.info(challenge)
    
    logger.info("\n=== 已实现改进 ===")
    for improvement in improvements:
        logger.info(improvement)

if __name__ == "__main__":
    test_enhanced_vs_original()
    analyze_detection_challenges()