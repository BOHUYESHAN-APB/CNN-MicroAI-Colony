import cv2
import numpy as np
from pathlib import Path
import logging
from core.corrected_detector_fixed import CorrectedDetector
import time

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_fixed_detector():
    """测试修复版本的检测器，并请用户确认结果"""
    logger.info("开始修复版本检测器测试")
    
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
        
        # 根据图像名称判断类型和预期结果
        if "OIP-C" in img_file.name:
            test_type = "透明挖孔法"
            expected_description = "4个透明挖孔 + 1个气泡干扰"
            detection_method = "holes"
        elif "R-C" in img_file.name:
            test_type = "滤纸片法"
            expected_description = "若干滤纸片（比背景更亮）"
            detection_method = "papers"
        else:
            test_type = "未知类型"
            expected_description = "未知"
            detection_method = "auto"
        
        print(f"\n🔬 图像分析: {img_file.name}")
        print(f"   类型: {test_type}")
        print(f"   预期: {expected_description}")
        print("-" * 40)
        
        # 1. 培养皿检测
        print("🥽 步骤1: 培养皿检测")
        start_time = time.time()
        dishes = detector.detect_petri_dishes_robust(original_image.copy())
        dish_time = time.time() - start_time
        
        print(f"   耗时: {dish_time:.3f}秒")
        print(f"   结果: {len(dishes)}个培养皿")
        
        if not dishes:
            print("   ❌ 培养皿检测失败")
            user_confirm = input("   ❓ 图像中是否确实有培养皿？(y/n): ")
            if user_confirm.lower() == 'y':
                print("   ⚠️  需要改进培养皿检测算法")
            else:
                print("   ✅ 确认图像中没有培养皿")
            continue
        
        dish = dishes[0]
        print(f"   ✅ 培养皿: 中心{dish.center}, 半径{dish.radius}px")
        print(f"   ✅ 标定: {detector.px_per_mm:.2f}px/mm")
        
        # 2. 物质检测
        print("\n🔍 步骤2: 抑菌物质检测")
        start_time = time.time()
        
        if detection_method == "holes":
            substances = detector.detect_transparent_holes_corrected(original_image.copy(), dish)
            method_name = "透明挖孔检测"
        elif detection_method == "papers":
            substances = detector.detect_filter_papers_corrected(original_image.copy(), dish)
            method_name = "滤纸片检测"
        else:
            # 尝试两种方法，选择结果更好的
            holes = detector.detect_transparent_holes_corrected(original_image.copy(), dish)
            papers = detector.detect_filter_papers_corrected(original_image.copy(), dish)
            if len(holes) > len(papers):
                substances = holes
                method_name = "透明挖孔检测（自动选择）"
            else:
                substances = papers
                method_name = "滤纸片检测（自动选择）"
        
        detection_time = time.time() - start_time
        
        print(f"   方法: {method_name}")
        print(f"   耗时: {detection_time:.3f}秒")
        print(f"   结果: {len(substances)}个物质")
        
        # 显示每个检测结果
        for i, substance in enumerate(substances):
            print(f"   物质#{i+1}: 中心{substance.center}, 半径{substance.radius}px, "
                  f"类型{substance.substance_type.name}, 得分{substance.detection_score:.2f}")
        
        # 3. 可视化结果
        print("\n📺 步骤3: 显示检测结果")
        result_image = visualize_detection_with_feedback(
            original_image.copy(), dish, substances, img_file.name, 
            test_type, expected_description
        )
        
        # 等待用户查看
        print("   请仔细查看弹出的检测结果图像...")
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        
        # 4. 用户反馈
        print("\n📝 步骤4: 用户反馈")
        print("   请根据实际图像情况评价检测结果:")
        
        # 询问检测准确性
        try:
            actual_count = input(f"   ❓ 实际应该检测到多少个目标？: ")
            actual_count = int(actual_count)
            
            correct_detections = input(f"   ❓ 在{len(substances)}个检测结果中，有多少个是正确的？: ")
            correct_detections = int(correct_detections)
            
            # 计算准确率
            precision = correct_detections / len(substances) if len(substances) > 0 else 0
            recall = correct_detections / actual_count if actual_count > 0 else 0
            
            print(f"\n📊 检测性能评估:")
            print(f"   精确率: {precision:.1%} ({correct_detections}/{len(substances)})")
            print(f"   召回率: {recall:.1%} ({correct_detections}/{actual_count})")
            
            # 性能评估
            if precision >= 0.8 and recall >= 0.8:
                print("   🎉 检测效果优秀！")
                performance = "优秀"
            elif precision >= 0.6 and recall >= 0.6:
                print("   👍 检测效果良好")
                performance = "良好"
            elif precision >= 0.4 or recall >= 0.4:
                print("   ⚠️  检测效果一般，需要改进")
                performance = "一般"
            else:
                print("   ❌ 检测效果较差，需要重新设计算法")
                performance = "较差"
            
        except ValueError:
            print("   输入格式有误，跳过性能评估")
            performance = "未评估"
        
        # 询问具体问题
        print("\n🔧 改进建议:")
        issues = input("   ❓ 主要问题是什么？(误检/漏检/位置偏差/其他): ")
        suggestions = input("   ❓ 您有什么改进建议？: ")
        
        print(f"\n✅ {img_file.name} 测试完成")
        print(f"   性能评估: {performance}")
        print(f"   主要问题: {issues}")
        print(f"   改进建议: {suggestions}")
        
        # 询问是否继续
        continue_test = input("\n🚀 继续测试下一张图像？(y/n): ")
        if continue_test.lower() != 'y':
            break
    
    print("\n🎯 测试总结")
    print("感谢您提供的详细反馈！")
    print("基于您的评估，我们将进一步优化检测算法。")

def visualize_detection_with_feedback(image: np.ndarray, dish, substances, 
                                    image_name: str, test_type: str, 
                                    expected_description: str) -> np.ndarray:
    """可视化检测结果，便于用户反馈"""
    result = image.copy()
    
    # 绘制培养皿
    cv2.circle(result, dish.center, dish.radius, (0, 255, 0), 3)
    cv2.putText(result, f"Petri Dish R={dish.radius}px", 
                (dish.center[0]-80, dish.center[1]-dish.radius-30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    
    # 绘制检测到的物质
    colors = [(255, 0, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255), (0, 255, 255), (128, 255, 128)]
    
    for i, substance in enumerate(substances):
        color = colors[i % len(colors)]
        
        # 根据类型选择不同的绘制样式
        if substance.substance_type.name == "HOLE":
            # 挖孔用虚线圆圈
            draw_dashed_circle(result, substance.center, substance.radius, color, 2)
        else:
            # 滤纸片用实线圆圈
            cv2.circle(result, substance.center, substance.radius, color, 2)
        
        # 绘制中心点
        cv2.circle(result, substance.center, 4, color, -1)
        
        # 添加编号和得分
        label_text = f"#{i+1}"
        score_text = f"Score:{substance.detection_score:.2f}"
        
        cv2.putText(result, label_text, 
                    (substance.center[0]+substance.radius+8, substance.center[1]-8),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        cv2.putText(result, score_text, 
                    (substance.center[0]+substance.radius+8, substance.center[1]+12),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)
    
    # 添加图像信息
    info_y_start = 30
    info_lines = [
        f"Image: {image_name}",
        f"Type: {test_type}",
        f"Expected: {expected_description}",
        f"Detected: {len(substances)} substances",
        "",
        "Please evaluate detection accuracy:",
        "- Are positions correct?",
        "- Any false positives?",
        "- Any missed targets?"
    ]
    
    for i, line in enumerate(info_lines):
        y_pos = info_y_start + i * 22
        if line.startswith("Please") or line.startswith("-"):
            color = (0, 255, 255)  # 黄色提示
            font_size = 0.5
        elif line == "":
            continue
        else:
            color = (255, 255, 255)  # 白色信息
            font_size = 0.6
        
        cv2.putText(result, line, (10, y_pos), 
                    cv2.FONT_HERSHEY_SIMPLEX, font_size, color, 1)
    
    # 添加说明
    instruction = "Press any key to continue..."
    cv2.putText(result, instruction, (10, result.shape[0] - 20), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
    
    # 调整显示大小
    max_height = 900
    if result.shape[0] > max_height:
        scale = max_height / result.shape[0]
        new_width = int(result.shape[1] * scale)
        new_height = int(result.shape[0] * scale)
        result = cv2.resize(result, (new_width, new_height))
    
    # 显示结果
    window_title = f"Detection Results - {image_name}"
    cv2.imshow(window_title, result)
    
    return result

def draw_dashed_circle(image, center, radius, color, thickness):
    """绘制虚线圆圈"""
    angles = np.linspace(0, 2*np.pi, 64)
    points = []
    
    for angle in angles:
        x = int(center[0] + radius * np.cos(angle))
        y = int(center[1] + radius * np.sin(angle))
        points.append((x, y))
    
    # 绘制虚线效果（每隔一段绘制）
    for i in range(0, len(points)-1, 3):
        if i+1 < len(points):
            cv2.line(image, points[i], points[i+1], color, thickness)

def main():
    """主函数"""
    print("🚀 修复版本检测器测试")
    print("=" * 60)
    print("本测试将验证修复后的检测算法")
    print("请根据实际图像情况提供准确的反馈")
    print("您的反馈将帮助我们进一步改进算法")
    print("=" * 60)
    
    test_fixed_detector()

if __name__ == "__main__":
    main()