#!/usr/bin/env python3
"""
抑菌圈检测系统增强版GUI启动脚本
包含单张图像处理和批量处理功能
"""
import sys
import os
from pathlib import Path

# 添加项目路径到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 检查基本依赖
try:
    import cv2
    import numpy as np
    from PyQt6.QtWidgets import QApplication
    print("✅ 基本依赖检查通过")
    print(f"   OpenCV版本: {cv2.__version__}")
    print(f"   NumPy版本: {np.__version__}")
except ImportError as e:
    print(f"❌ 缺少依赖: {e}")
    print("请运行: pip install opencv-python PyQt6 numpy")
    sys.exit(1)

# 导入并运行增强版GUI
try:
    print("🚀 启动抑菌圈检测系统增强版GUI...")
    print("📋 功能特性:")
    print("   ✅ 单张图像处理")
    print("   ✅ 批量处理功能")
    print("   ✅ 结果统计分析")
    print("   ✅ 汇总报告生成")
    
    from gui.enhanced_standalone_gui import main
    main()
except Exception as e:
    print(f"❌ GUI启动失败: {e}")
    print("\n🔧 故障排除:")
    print("1. 确保所有依赖已正确安装")
    print("2. 检查Python版本（推荐3.8+）")
    print("3. 尝试运行简化版: python gui/standalone_gui.py")
    sys.exit(1)