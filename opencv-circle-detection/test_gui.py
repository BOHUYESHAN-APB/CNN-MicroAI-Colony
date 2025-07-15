#!/usr/bin/env python3
"""
GUI界面测试脚本
检查GUI界面是否可以正常启动和运行
"""
import sys
import os
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_imports():
    """测试必要的模块导入"""
    print("🔍 测试模块导入...")
    
    try:
        import cv2
        print(f"✅ OpenCV版本: {cv2.__version__}")
    except ImportError as e:
        print(f"❌ OpenCV导入失败: {e}")
        return False
    
    try:
        import numpy as np
        print(f"✅ NumPy版本: {np.__version__}")
    except ImportError as e:
        print(f"❌ NumPy导入失败: {e}")
        return False
    
    try:
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtCore import QT_VERSION_STR
        print(f"✅ PyQt6版本: {QT_VERSION_STR}")
    except ImportError as e:
        print(f"❌ PyQt6导入失败: {e}")
        return False
    
    return True

def test_core_modules():
    """测试核心检测模块"""
    print("\n🔍 测试核心检测模块...")
    
    try:
        from core.detector import CircleDetector
        print("✅ 原始检测器导入成功")
    except ImportError as e:
        print(f"❌ 原始检测器导入失败: {e}")
        return False
    
    try:
        from core.corrected_detector_fixed import CorrectedDetector
        print("✅ 修正检测器导入成功")
    except ImportError as e:
        print(f"❌ 修正检测器导入失败: {e}")
        return False
    
    try:
        from core.models import Colony, PetriDish
        print("✅ 数据模型导入成功")
    except ImportError as e:
        print(f"❌ 数据模型导入失败: {e}")
        return False
    
    return True

def test_gui_import():
    """测试GUI模块导入"""
    print("\n🔍 测试GUI模块...")
    
    try:
        from gui.circle_detection_main import CircleDetectionMainWindow
        print("✅ GUI主窗口类导入成功")
        return True
    except ImportError as e:
        print(f"❌ GUI模块导入失败: {e}")
        return False

def test_gui_creation():
    """测试GUI界面创建"""
    print("\n🔍 测试GUI界面创建...")
    
    try:
        from PyQt6.QtWidgets import QApplication
        from gui.circle_detection_main import CircleDetectionMainWindow
        
        # 创建应用
        app = QApplication([])
        
        # 创建主窗口
        window = CircleDetectionMainWindow()
        print("✅ GUI界面创建成功")
        
        # 清理
        app.quit()
        return True
        
    except Exception as e:
        print(f"❌ GUI界面创建失败: {e}")
        return False

def check_test_images():
    """检查测试图像"""
    print("\n🔍 检查测试图像...")
    
    test_images_dir = project_root / "test_images"
    if test_images_dir.exists():
        image_files = list(test_images_dir.glob("*.jpg")) + list(test_images_dir.glob("*.png"))
        if image_files:
            print(f"✅ 找到 {len(image_files)} 个测试图像:")
            for img in image_files:
                print(f"   - {img.name}")
            return True
        else:
            print("⚠️  测试图像目录为空")
    else:
        print("⚠️  测试图像目录不存在")
    
    return False

def main():
    """主测试函数"""
    print("🚀 OpenCV抑菌圈检测系统 GUI 测试")
    print("=" * 50)
    
    success = True
    
    # 测试基础依赖
    if not test_imports():
        success = False
    
    # 测试核心模块
    if not test_core_modules():
        success = False
    
    # 测试GUI模块
    if not test_gui_import():
        success = False
    
    # 测试GUI创建
    if not test_gui_creation():
        success = False
    
    # 检查测试图像
    check_test_images()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 所有测试通过！GUI界面可以正常启动。")
        print("\n📖 使用说明:")
        print("   运行命令: python main_gui.py")
        print("   查看文档: README_GUI.md")
    else:
        print("❌ 部分测试失败，请检查依赖安装。")
        print("\n🔧 解决方案:")
        print("   pip install -r requirements.txt")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)