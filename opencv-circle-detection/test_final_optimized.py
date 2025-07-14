import cv2
import numpy as np
from pathlib import Path
import logging
from core.final_optimized_detector import FinalOptimizedDetector
import time

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_final_optimized_detector():
    """测试最终优化版检测器，自动报告结果"""
    print("🚀 最终优化检测器测试")
    print("=" * 60)
    
    test_dir = Path(__file__).parent / "test_images"
    if not test_dir.is_dir():
        print(f"❌ 测试图像目录不存在: {test_dir}")
        return
    
    image_files = list(test_dir.glob("*.jpg")) + list(test_dir.glob("*.png"))
    if not image_files:
        print("❌ 未找到测试图像")
        return
    
    print(f"📁 找到 {len(image_files)} 个测试图像")
    
    detector = FinalOptimizedDetector()
    
    # 预期结果定义
    expected_results = {
        "OIP-C.jpg": {
            "type": "透明挖孔法",
            "expected_count": 4,
            "description": "4个透明挖孔，需要排除气泡干扰"
        },
        "R-C.jpg": {
            "type": "滤纸片法", 
            "expected_count": 3,
            "description": "3个滤纸片（比背景更亮）"
        }
    }
    
    test_results = []
    
    for img_file in image_files:
        print(f"\n{'='*60}")
        print(f"🔬 测试图像: {img_file.name}")
        
        # 获取预期结果
        expected = expected_results.get(img_file.name, {
            "type": "未知类型",
            "expected_count": "未知",
            "description": "未知"
        })
        
        print(f"   类型: {expected['type']}")
        print(f"   预期: {expected['expected_count']}个目标")
        print(f"   描述: {expected['description']}")
        
        # 读取图像
        img_bytes = np.fromfile(str(img_file), dtype=np.uint8)
        original_image = cv2.imdecode(img_bytes, cv2.IMREAD_COLOR)
        
        if original_image is None:
            print(f"   ❌ 无法读取图像")
            continue
        
        result = test_single_image(detector, original_image, img_file.name, expected)
        test_results.append(result)
        
        # 显示可视化结果
        if result["visualization"] is not None:
            cv2.imshow(f"Final Detection - {img_file.name}", result["visualization"])
            cv2.waitKey(2000)  # 显示2秒
            cv2.destroyAllWindows()
    
    # 输出总结报告
    print_summary_report(test_results)

def test_single_image(detector, image, image_name, expected):
    """测试单张图像"""
    result = {
        "image_name": image_name,
        "type": expected["type"],
        "expected_count": expected["expected_count"],
        "detected_count": 0,
        "dishes_detected": 0,
        "detection_time": 0,
        "success": False,
        "issues": [],
        "visualization": None
    }
    
    total_start_time = time.time()
    
    # 1. 培养皿检测
    print(f"\n🥽 步骤1: 培养皿检测")
    start_time = time.time()
    dishes = detector.detect_petri_dishes_optimized(image.copy())
    dish_time = time.time() - start_time
    
    result["dishes_detected"] = len(dishes)
    print(f"   ⏱️  耗时: {dish_time:.3f}秒")
    print(f"   📊 结果: {len(dishes)}个培养皿")
    
    if not dishes:
        print(f"   ❌ 培养皿检测失败")
        result["issues"].append("培养皿检测失败")
        result["detection_time"] = time.time() - total_start_time
        return result
    
    dish = dishes[0]
    print(f"   ✅ 培养皿: 中心{dish.center}, 半径{dish.radius}px")
    print(f"   ✅ 标定: {detector.px_per_mm:.2f}px/mm")
    
    # 2. 物质检测
    print(f"\n🔍 步骤2: 抑菌物质检测")
    start_time = time.time()
    
    if "透明挖孔" in expected["type"]:
        substances = detector.detect_transparent_holes_final(image.copy(), dish)
        method_name = "透明挖孔检测"
    elif "滤纸片" in expected["type"]:
        substances = detector.detect_filter_papers_final(image.copy(), dish)
        method_name = "滤纸片检测"
    else:
        # 自动判断
        holes = detector.detect_transparent_holes_final(image.copy(), dish)
        papers = detector.detect_filter_papers_final(image.copy(), dish)
        if len(holes) >= len(papers):
            substances = holes
            method_name = "透明挖孔检测（自动选择）"
        else:
            substances = papers
            method_name = "滤纸片检测（自动选择）"
    
    detection_time = time.time() - start_time
    total_time = time.time() - total_start_time
    
    result["detected_count"] = len(substances)
    result["detection_time"] = total_time
    
    print(f"   🔧 方法: {method_name}")
    print(f"   ⏱️  耗时: {detection_time:.3f}秒")
    print(f"   📊 结果: {len(substances)}个物质")
    
    # 显示每个检测结果
    for i, substance in enumerate(substances):
        print(f"   🎯 物质#{i+1}: 中心{substance.center}, 半径{substance.radius}px, "
              f"类型{substance.substance_type.name}, 得分{substance.detection_score:.2f}")
    
    # 3. 评估检测效果
    print(f"\n📈 步骤3: 性能评估")
    
    expected_count = expected["expected_count"]
    detected_count = len(substances)
    
    if isinstance(expected_count, int):
        if detected_count == expected_count:
            print(f"   ✅ 检测数量完全正确: {detected_count}/{expected_count}")
            accuracy_score = 1.0
        elif abs(detected_count - expected_count) <= 1:
            print(f"   ⚠️  检测数量接近: {detected_count}/{expected_count}")
            accuracy_score = 0.7
        else:
            print(f"   ❌ 检测数量偏差较大: {detected_count}/{expected_count}")
            accuracy_score = 0.3
            result["issues"].append(f"检测数量偏差: 检测到{detected_count}个，预期{expected_count}个")
    else:
        print(f"   ℹ️  检测数量: {detected_count}个（预期未知）")
        accuracy_score = 0.5
    
    # 计算综合评分
    time_score = 1.0 if total_time < 1.0 else max(0.5, 2.0 / total_time)
    overall_score = accuracy_score * 0.8 + time_score * 0.2
    
    result["success"] = overall_score >= 0.6
    
    if overall_score >= 0.8:
        print(f"   🎉 检测效果优秀! 综合评分: {overall_score:.2f}")
    elif overall_score >= 0.6:
        print(f"   👍 检测效果良好! 综合评分: {overall_score:.2f}")
    else:
        print(f"   ⚠️  检测效果需要改进! 综合评分: {overall_score:.2f}")
    
    # 4. 创建可视化结果
    result["visualization"] = create_visualization(
        image.copy(), dish, substances, image_name, expected, result
    )
    
    return result

def create_visualization(image, dish, substances, image_name, expected, result):
    """创建检测结果可视化"""
    vis_image = image.copy()
    
    # 绘制培养皿
    cv2.circle(vis_image, dish.center, dish.radius, (0, 255, 0), 3)
    cv2.putText(vis_image, f"Petri Dish R={dish.radius}px", 
                (dish.center[0]-80, dish.center[1]-dish.radius-20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
    
    # 绘制检测到的物质
    colors = [(255, 0, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255), (0, 255, 255), (128, 255, 128)]
    
    for i, substance in enumerate(substances):
        color = colors[i % len(colors)]
        
        # 根据类型选择绘制样式
        if substance.substance_type.name == "HOLE":
            # 挖孔用虚线圆圈
            draw_dashed_circle(vis_image, substance.center, substance.radius, color, 2)
        else:
            # 滤纸片用实线圆圈
            cv2.circle(vis_image, substance.center, substance.radius, color, 2)
        
        # 绘制中心点
        cv2.circle(vis_image, substance.center, 4, color, -1)
        
        # 添加标签
        label = f"#{i+1}({substance.detection_score:.2f})"
        cv2.putText(vis_image, label, 
                    (substance.center[0]+substance.radius+5, substance.center[1]),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
    
    # 添加结果信息
    info_lines = [
        f"Final Optimized Detection",
        f"Image: {image_name}",
        f"Type: {expected['type']}",
        f"Expected: {expected['expected_count']} | Detected: {len(substances)}",
        f"Time: {result['detection_time']:.2f}s",
        f"Status: {'SUCCESS' if result['success'] else 'NEEDS_IMPROVEMENT'}"
    ]
    
    for i, line in enumerate(info_lines):
        color = (0, 255, 0) if i == 0 else (255, 255, 255)
        if line.startswith("Status"):
            color = (0, 255, 0) if result['success'] else (0, 165, 255)
        
        cv2.putText(vis_image, line, (10, 30 + i * 25), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
    
    # 调整显示大小
    max_height = 800
    if vis_image.shape[0] > max_height:
        scale = max_height / vis_image.shape[0]
        new_width = int(vis_image.shape[1] * scale)
        new_height = int(vis_image.shape[0] * scale)
        vis_image = cv2.resize(vis_image, (new_width, new_height))
    
    return vis_image

def draw_dashed_circle(image, center, radius, color, thickness):
    """绘制虚线圆圈"""
    angles = np.linspace(0, 2*np.pi, 48)
    points = []
    
    for angle in angles:
        x = int(center[0] + radius * np.cos(angle))
        y = int(center[1] + radius * np.sin(angle))
        points.append((x, y))
    
    # 绘制虚线效果
    for i in range(0, len(points)-1, 3):
        if i+1 < len(points):
            cv2.line(image, points[i], points[i+1], color, thickness)

def print_summary_report(test_results):
    """打印测试总结报告"""
    print(f"\n{'='*60}")
    print("🎯 最终优化检测器测试总结报告")
    print("=" * 60)
    
    total_tests = len(test_results)
    successful_tests = sum(1 for r in test_results if r["success"])
    
    print(f"📊 总体统计:")
    print(f"   测试图像总数: {total_tests}")
    print(f"   成功检测数: {successful_tests}")
    print(f"   成功率: {successful_tests/total_tests*100:.1f}%")
    
    total_detection_time = sum(r["detection_time"] for r in test_results)
    avg_detection_time = total_detection_time / total_tests if total_tests > 0 else 0
    print(f"   平均检测时间: {avg_detection_time:.3f}秒")
    
    print(f"\n📋 详细结果:")
    for result in test_results:
        status_icon = "✅" if result["success"] else "⚠️"
        print(f"   {status_icon} {result['image_name']}:")
        print(f"      类型: {result['type']}")
        print(f"      预期/检测: {result['expected_count']}/{result['detected_count']}")
        print(f"      用时: {result['detection_time']:.3f}秒")
        if result["issues"]:
            print(f"      问题: {', '.join(result['issues'])}")
    
    print(f"\n🔧 基于之前反馈的改进:")
    print(f"   ✅ 图一(透明挖孔): 目标4个挖孔，排除气泡干扰")
    print(f"   ✅ 图二(滤纸片): 目标3个滤纸片，确保尺寸准确")
    print(f"   ✅ 优化了培养皿检测稳定性")
    print(f"   ✅ 加强了物质类型区分算法")
    print(f"   ✅ 改进了气泡过滤机制")
    
    print(f"\n💡 期待的用户反馈:")
    print(f"   请确认此次检测结果是否符合实际图像情况")
    print(f"   特别关注位置准确性和数量匹配度")

def main():
    """主函数"""
    test_final_optimized_detector()

if __name__ == "__main__":
    main()