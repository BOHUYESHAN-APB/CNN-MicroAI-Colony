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

def test_with_extended_display():
    """测试最终优化版检测器，延长显示时间"""
    print("🚀 最终优化检测器测试 - 延长显示版本")
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
        
        # 执行检测
        result = test_single_image_extended(detector, original_image, img_file.name, expected)
        
        # 显示结果图像并等待用户确认
        if result["visualization"] is not None:
            window_name = f"检测结果 - {img_file.name}"
            cv2.imshow(window_name, result["visualization"])
            
            print(f"\n📺 请仔细查看检测结果图像窗口")
            print(f"   🎯 图像: {img_file.name}")
            print(f"   🔍 预期: {expected['expected_count']}个，检测: {result['detected_count']}个")
            print(f"   ⏱️  用时: {result['detection_time']:.3f}秒")
            print(f"   📊 状态: {'成功' if result['success'] else '需要改进'}")
            print(f"   按任意键继续下一张图像...")
            
            # 等待用户按键
            cv2.waitKey(0)
            cv2.destroyWindow(window_name)
            
            # 询问用户反馈
            print(f"\n💬 请问这张图像的检测结果如何？")
            print(f"   您看到的检测位置是否准确？")
            print(f"   是否有漏检或误检的情况？")
    
    print(f"\n🎯 测试完成")
    print(f"请根据您看到的检测结果提供反馈，这将帮助我们进一步改进算法")

def test_single_image_extended(detector, image, image_name, expected):
    """测试单张图像 - 扩展版"""
    result = {
        "image_name": image_name,
        "type": expected["type"],
        "expected_count": expected["expected_count"],
        "detected_count": 0,
        "dishes_detected": 0,
        "detection_time": 0,
        "success": False,
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
    
    # 显示每个检测结果的详细信息
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
            result["success"] = True
        elif abs(detected_count - expected_count) <= 1:
            print(f"   ⚠️  检测数量接近: {detected_count}/{expected_count}")
            result["success"] = True
        else:
            print(f"   ❌ 检测数量偏差较大: {detected_count}/{expected_count}")
            result["success"] = False
    
    # 4. 创建详细的可视化结果
    result["visualization"] = create_detailed_visualization(
        image.copy(), dish, substances, image_name, expected, result
    )
    
    return result

def create_detailed_visualization(image, dish, substances, image_name, expected, result):
    """创建详细的检测结果可视化"""
    vis_image = image.copy()
    h, w = vis_image.shape[:2]
    
    # 绘制培养皿
    cv2.circle(vis_image, dish.center, dish.radius, (0, 255, 0), 4)
    cv2.putText(vis_image, f"Petri Dish R={dish.radius}px", 
                (dish.center[0]-100, dish.center[1]-dish.radius-30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
    
    # 绘制检测到的物质
    colors = [(255, 0, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255), (0, 255, 255), (128, 255, 128)]
    
    for i, substance in enumerate(substances):
        color = colors[i % len(colors)]
        
        # 根据类型选择绘制样式
        if substance.substance_type.name == "HOLE":
            # 挖孔用虚线圆圈
            draw_dashed_circle(vis_image, substance.center, substance.radius, color, 3)
            type_label = "挖孔"
        else:
            # 滤纸片用实线圆圈
            cv2.circle(vis_image, substance.center, substance.radius, color, 3)
            type_label = "滤纸片"
        
        # 绘制中心点
        cv2.circle(vis_image, substance.center, 6, color, -1)
        
        # 添加详细标签
        label_lines = [
            f"#{i+1} {type_label}",
            f"位置: {substance.center}",
            f"半径: {substance.radius}px",
            f"得分: {substance.detection_score:.2f}"
        ]
        
        # 计算标签位置（避免重叠）
        label_x = substance.center[0] + substance.radius + 10
        label_y = substance.center[1] - 30
        
        # 确保标签不超出图像边界
        if label_x + 200 > w:
            label_x = substance.center[0] - substance.radius - 200
        if label_y < 20:
            label_y = substance.center[1] + substance.radius + 50
        
        for j, line in enumerate(label_lines):
            cv2.putText(vis_image, line, 
                        (label_x, label_y + j * 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
    
    # 添加总体信息面板
    info_panel_height = 180
    info_panel = np.zeros((info_panel_height, w, 3), dtype=np.uint8)
    info_panel[:] = (50, 50, 50)  # 深灰色背景
    
    info_lines = [
        f"检测结果总结 - {image_name}",
        f"类型: {expected['type']}",
        f"预期目标数量: {expected['expected_count']}",
        f"实际检测数量: {len(substances)}",
        f"检测用时: {result['detection_time']:.3f}秒",
        f"检测状态: {'成功' if result['success'] else '需要改进'}",
        "",
        "请仔细检查每个检测位置的准确性"
    ]
    
    for i, line in enumerate(info_lines):
        if line.startswith("检测结果总结"):
            color = (0, 255, 255)  # 黄色标题
            font_size = 0.8
        elif line.startswith("检测状态"):
            color = (0, 255, 0) if result['success'] else (0, 165, 255)  # 绿色/橙色
            font_size = 0.7
        elif line == "":
            continue
        elif line.startswith("请仔细检查"):
            color = (255, 255, 255)  # 白色提示
            font_size = 0.6
        else:
            color = (200, 200, 200)  # 浅灰色信息
            font_size = 0.7
        
        cv2.putText(info_panel, line, (10, 25 + i * 20), 
                    cv2.FONT_HERSHEY_SIMPLEX, font_size, color, 2)
    
    # 合并图像和信息面板
    final_image = np.vstack([vis_image, info_panel])
    
    return final_image

def draw_dashed_circle(image, center, radius, color, thickness):
    """绘制虚线圆圈"""
    angles = np.linspace(0, 2*np.pi, 64)
    points = []
    
    for angle in angles:
        x = int(center[0] + radius * np.cos(angle))
        y = int(center[1] + radius * np.sin(angle))
        points.append((x, y))
    
    # 绘制虚线效果（每隔2段绘制1段）
    for i in range(0, len(points)-1, 3):
        if i+1 < len(points):
            cv2.line(image, points[i], points[i+1], color, thickness)

def main():
    """主函数"""
    test_with_extended_display()

if __name__ == "__main__":
    main()