"""
测量精度验证功能测试脚本
"""
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from utils.accuracy_validator import AccuracyValidator, create_sample_ground_truth

def test_accuracy_validation():
    """测试精度验证功能"""
    print("🔍 测试测量精度验证功能")
    print("=" * 50)
    
    # 创建验证器和示例标准答案
    print("📋 创建标准答案数据...")
    validator = create_sample_ground_truth()
    
    # 保存标准答案
    ground_truth_file = "test_ground_truth.json"
    validator.save_ground_truth(ground_truth_file)
    print(f"✅ 标准答案已保存到: {ground_truth_file}")
    
    # 模拟检测结果（完美匹配）
    print("\n🎯 测试完美匹配结果...")
    perfect_result = {
        'dish': {'center': (239, 232), 'radius': 184},
        'substances': [
            {'center': (221, 221), 'radius': 17, 'type': 'hole'},
            {'center': (334, 245), 'radius': 17, 'type': 'hole'},
            {'center': (248, 323), 'radius': 11, 'type': 'hole'},
            {'center': (356, 282), 'radius': 9, 'type': 'hole'}
        ],
        'zones': [
            {'center': (221, 221), 'radius': 45, 'diameter_mm': 22.0},
            {'center': (334, 245), 'radius': 38, 'diameter_mm': 18.5},
            {'center': (248, 323), 'radius': 35, 'diameter_mm': 17.1},
            {'center': (356, 282), 'radius': 30, 'diameter_mm': 14.7}
        ]
    }
    
    validation_result = validator.validate_detection_result("OIP-C.jpg", perfect_result)
    print(f"总体精度: {validation_result['overall_accuracy']:.3f}")
    print(f"培养皿精度: {validation_result['dish_accuracy']['accuracy_score']:.3f}")
    print(f"物质检测精度: {validation_result['substance_accuracy']['overall_score']:.3f}")
    print(f"抑菌圈精度: {validation_result['zone_accuracy']['overall_score']:.3f}")
    
    # 模拟检测结果（有误差）
    print("\n⚠️  测试有误差的结果...")
    imperfect_result = {
        'dish': {'center': (245, 238), 'radius': 190},  # 中心偏移，半径有误差
        'substances': [
            {'center': (225, 225), 'radius': 15, 'type': 'hole'},  # 位置和大小有误差
            {'center': (330, 250), 'radius': 19, 'type': 'hole'},  # 位置有误差
            {'center': (250, 320), 'radius': 12, 'type': 'hole'}   # 缺少一个物质
            # 缺少第4个物质
        ],
        'zones': [
            {'center': (225, 225), 'radius': 42, 'diameter_mm': 20.5},  # 直径有误差
            {'center': (330, 250), 'radius': 40, 'diameter_mm': 19.2}   # 缺少抑菌圈
            # 缺少其他抑菌圈
        ]
    }
    
    validation_result2 = validator.validate_detection_result("OIP-C.jpg", imperfect_result)
    print(f"总体精度: {validation_result2['overall_accuracy']:.3f}")
    print(f"培养皿精度: {validation_result2['dish_accuracy']['accuracy_score']:.3f}")
    print(f"物质检测精度: {validation_result2['substance_accuracy']['overall_score']:.3f}")
    print(f"抑菌圈精度: {validation_result2['zone_accuracy']['overall_score']:.3f}")
    
    # 测试第二张图像
    print("\n📸 测试第二张图像...")
    result_r_c = {
        'dish': {'center': (549, 241), 'radius': 237},
        'substances': [
            {'center': (562, 288), 'radius': 25, 'type': 'filter_paper'},
            {'center': (450, 200), 'radius': 23, 'type': 'filter_paper'}
            # 缺少一个物质
        ],
        'zones': [
            {'center': (562, 288), 'radius': 55, 'diameter_mm': 20.8}
            # 缺少其他抑菌圈
        ]
    }
    
    validation_result3 = validator.validate_detection_result("R-C.jpg", result_r_c)
    print(f"总体精度: {validation_result3['overall_accuracy']:.3f}")
    
    # 生成精度统计
    print("\n📊 生成精度统计...")
    stats = validator.get_accuracy_statistics()
    print(f"平均总体精度: {stats['overall_accuracy']['mean']:.3f} ± {stats['overall_accuracy']['std']:.3f}")
    print(f"平均培养皿精度: {stats['dish_accuracy']['mean']:.3f} ± {stats['dish_accuracy']['std']:.3f}")
    print(f"平均物质检测精度: {stats['substance_accuracy']['mean']:.3f} ± {stats['substance_accuracy']['std']:.3f}")
    print(f"平均抑菌圈精度: {stats['zone_accuracy']['mean']:.3f} ± {stats['zone_accuracy']['std']:.3f}")
    
    # 生成详细报告
    print("\n📝 生成详细验证报告...")
    report = validator.generate_accuracy_report("accuracy_validation_report.txt")
    print("报告预览:")
    print("-" * 30)
    print(report[:500] + "..." if len(report) > 500 else report)
    
    print("\n✅ 精度验证功能测试完成！")
    print(f"📄 详细报告已保存到: accuracy_validation_report.txt")
    print(f"📋 标准答案数据: {ground_truth_file}")

if __name__ == "__main__":
    test_accuracy_validation()