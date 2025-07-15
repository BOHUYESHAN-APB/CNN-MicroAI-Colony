#!/usr/bin/env python3
"""
抑菌圈检测系统批量处理启动脚本
支持多张图像的批量检测和结果导出
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

# 导入并运行批量处理GUI
try:
    print("🚀 启动抑菌圈检测系统批量处理GUI...")
    print("📋 功能特性:")
    print("   ✅ 批量添加图像文件或文件夹")
    print("   ✅ 自动检测培养皿和抑菌物质")
    print("   ✅ 批量保存检测结果和标注图像")
    print("   ✅ 生成汇总统计报告")
    print("   ✅ 实时进度显示和错误处理")
    print("   ✅ 支持暂停和继续处理")
    
    from gui.batch_gui import main
    main()
except Exception as e:
    print(f"❌ GUI启动失败: {e}")
    print("\n🔧 故障排除:")
    print("1. 确保所有依赖已正确安装")
    print("2. 检查Python版本（推荐3.8+）")
    print("3. 尝试运行单张处理: python gui/standalone_gui.py")
    sys.exit(1)