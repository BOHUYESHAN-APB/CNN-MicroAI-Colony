#!/usr/bin/env python3
"""
抑菌圈检测系统GUI启动脚本 - 简化版
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
except ImportError as e:
    print(f"❌ 缺少依赖: {e}")
    print("请运行: pip install opencv-python PyQt6 numpy")
    sys.exit(1)

# 导入并运行GUI
try:
    from gui.standalone_gui import main
    print("🚀 启动抑菌圈检测系统GUI...")
    main()
except Exception as e:
    print(f"❌ GUI启动失败: {e}")
    sys.exit(1)