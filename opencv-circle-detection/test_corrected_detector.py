import cv2
import numpy as np
from pathlib import Path
import logging
from core.corrected_detector import CorrectedDetector
import time

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_corrected_detector():
    """测试修正后的检测器"""
    logger.info("开始修正检测器测试")
    
    test_dir = Path(__file__).parent / "test_images"
    if not test_dir.is_dir():
        logger.error(f"测试图像目录不存在: {test_dir}")
        return
    
    image_files = list(test_dir.glob("*.jpg")) + list(test_dir.glob("*.png"))
    if not image_files:
        logger.warning("未找到测试图像")
        return
    
    logger.info(f"找到 {len(image_files)} 个测试图像")
    
    detector = CorrectedDetector()
    
    for img_file in image_files:
        logger.info(f"\n{'='*60}")
        logger.info(f"测试图像: {img_file.name}")
        
        # 读取图像
        img_bytes = np.fromfile(str(img_file), dtype=np.uint8)
        original_image = cv2.imdecode(img_bytes, cv2.IMREAD_COLOR)
        
        if original_image is None:
            logger.error(f"无法读取图像: {img_file}")
            continue
        
        # 根据图像名称判断应该使用的检测方法
        if "OIP-C" in img_file.name:
            test_image_type = "transparent_holes"
            expected_count = 4
            logger.info(f"图像类型: 透明挖孔法 (预期: {expected_count}个挖孔)")
        elif "R-C" in img_file.name:
            test_image_type = "filter_papers"
            expected_count = "未知数量"
            logger.info(f"图像类型: 滤纸片法 (预期: {expected_count}个滤纸片)")
        else:
            test_image_type = "unknown"
            expected_count = "未知"
            logger.info(f"图像类型: 未知")
        
        # 1. 培养皿检测
        logger.info("--- 步骤1: 培养皿检测 ---")
        start_time = time.time()
        dishes = detector.detect_petri_dishes_robust(original_image.copy())
        dish_time = time.time() - start_time
        
        logger.info(f"培养皿检测用时: {dish_time:.3f}秒")
        logger.info(f"检测到培养皿: {len(dishes)}个")
        
        if not dishes:
            logger.error("❌ 培养皿检测失败，无法继续")
            
            # 请用户确认培养皿检测结果
            print(f"\n❓ 请确认 {img_file.name} 的培养皿检测结果:")
            print("   系统未检测到培养皿，这是否正确？")
            print("   如果图像中有培养皿但未检测到，我们需要进一步调整算法")
            user_input = input("   培养皿检测是否正确？(y/n): ")
            
            if user_input.lower() != 'y':
                print("   ⚠️  培养皿检测需要改进")
            continue
        
        dish = dishes[0]
        logger.info(f"✅ 培养皿: 中心{dish.center}, 半径{dish.radius}px")
        logger.info(f"✅ 标定比例: {detector.px_per_mm:.2f}px/mm")
        
        # 2. 物质检测
        logger.info("--- 步骤2: 物质检测 ---")
        start_time = time.time()
        
        if test_image_type == "transparent_holes":
            substances = detector.detect_transparent_holes_corrected(original_image.copy(), dish)
            method_name = "透明挖孔检测"
        elif test_image_type == "filter_papers":
            substances = detector.detect_filter_papers_corrected(original_image.copy(), dish)
            method_name = "滤纸片检测"
        else:
            # 尝试两种方法
            holes = detector.detect_transparent_holes_corrected(original_image.copy(), dish)
            papers = detector.detect_filter_papers_corrected(original_image.copy(), dish)
            substances = holes if len(holes) > len(papers) else papers
            method_name = f"自动选择({'挖孔' if len(holes) > len(papers) else '滤纸片'}检测)"
        
        detection_time = time.time() - start_time
        
        logger.info(f"{method_name}用时: {detection_time:.3f}秒")
        logger.info(f"检测到物质: {len(substances)}个")
        
        # 详细显示检测结果
        for i, substance in enumerate(substances):
            logger.info(f"  物质 #{i+1}: 中心{substance.center}, 半径{substance.radius}px, "
                       f"类型{substance.substance_type.name}, 得分{substance.detection_score:.3f}")
        
        # 3. 可视化结果
        result_image = visualize_corrected_results(
            original_image.copy(), dish, substances, img_file.name, 
            test_image_type, expected_count
        )
        
        # 4. 请用户确认检测结果
        print(f"\n🔍 请仔细查看 {img_file.name} 的检测结果:")
        print(f"   预期: {expected_count} (类型: {test_image_type})")
        print(f"   检测: {len(substances)}个")
        print("   请查看弹出的图像窗口，检查检测位置是否准确")
        
        # 等待用户查看图像
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        
        # 用户反馈
        print("\n📝 请评估检测结果:")
        correct_count = input(f"   实际正确检测了多少个? (0-{len(substances)}): ")
        
        try:
            correct_count = int(correct_count)
            accuracy = correct_count / len(substances) if len(substances) > 0 else 0
            logger.info(f"用户反馈: {correct_count}/{len(substances)} 正确, 准确率: {accuracy:.1%}")
            
            if accuracy >= 0.8:
                print("   ✅ 检测效果良好")
            elif accuracy >= 0.5:
                print("   ⚠️  检测效果一般，需要改进")
            else:
                print("   ❌ 检测效果较差，需要重新调整算法")
        except ValueError:
            print("   输入无效，跳过评估")
        
        # 询问是否继续
        user_input = input(f"\n继续测试下一张图像？(y/n): ")
        if user_input.lower() != 'y':
            break
    
    logger.info("修正检测器测试完成")

def visualize_corrected_results(image: np.ndarray, dish, substances, image_name: str,
                               test_type: str, expected_count) -> np.ndarray:
    """可视化修正检测结果"""
    result = image.copy()
    
    # 绘制培养皿
    cv2.circle(result, dish.center, dish.radius, (0, 255, 0), 3)
    cv2.putText(result, f"Dish R={dish.radius}px", 
                (dish.center[0]-80, dish.center[1]-dish.radius-20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    
    # 绘制检测到的物质
    colors = [(255, 0, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255), (0, 255, 255), (128, 255, 128)]
    
    for i, substance in enumerate(substances):
        color = colors[i % len(colors)]
        
        # 根据类型选择绘制样式
        if substance.substance_type.name == "HOLE":
            # 挖孔用虚线圆圈
            angles = np.linspace(0, 2*np.pi, 32)
            for j in range(0, len(angles)-1, 2):
                x1 = int(substance.center[0] + substance.radius * np.cos(angles[j]))
                y1 = int(substance.center[1] + substance.radius * np.sin(angles[j]))
                x2 = int(substance.center[0] + substance.radius * np.cos(angles[j+1]))
                y2 = int(substance.center[1] + substance.radius * np.sin(angles[j+1]))
                cv2.line(result, (x1, y1), (x2, y2), color, 2)
        else:
            # 滤纸片用实线圆圈
            cv2.circle(result, substance.center, substance.radius, color, 2)
        
        # 绘制中心点
        cv2.circle(result, substance.center, 3, color, -1)
        
        # 添加编号和得分
        label = f"#{i+1}"
        score_label = f"{substance.detection_score:.2f}"
        
        cv2.putText(result, label, 
                    (substance.center[0]+substance.radius+5, substance.center[1]-5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        cv2.putText(result, score_label, 
                    (substance.center[0]+substance.radius+5, substance.center[1]+15),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)
    
    # 添加总体信息
    info_lines = [
        f"Corrected Detection: {len(substances)} substances",
        f"Type: {test_type}",
        f"Expected: {expected_count}"
    ]
    
    for i, line in enumerate(info_lines):
        cv2.putText(result, line, (10, 30 + i * 25), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    
    # 添加说明文字
    instruction = "Please check if detections are accurate"
    cv2.putText(result, instruction, (10, result.shape[0] - 20), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
    
    # 显示结果
    window_title = f"Corrected Detection - {image_name}"
    
    # 调整窗口大小以适应屏幕
    screen_height = 800  # 假设屏幕高度
    if result.shape[0] > screen_height:
        scale = screen_height / result.shape[0]
        new_width = int(result.shape[1] * scale)
        new_height = int(result.shape[0] * scale)
        result = cv2.resize(result, (new_width, new_height))
    
    cv2.imshow(window_title, result)
    
    return result

def main():
    """主函数"""
    print("🚀 修正检测器测试")
    print("=" * 60)
    print("本测试将验证基于用户反馈修正的检测算法")
    print("请仔细查看每个检测结果并提供准确的反馈")
    print("=" * 60)
    
    test_corrected_detector()

if __name__ == "__main__":
    main()