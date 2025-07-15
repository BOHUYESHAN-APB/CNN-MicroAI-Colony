#!/usr/bin/env python3
"""
抑菌圈检测系统启动脚本
"""
import sys
import os
from pathlib import Path

# 添加项目路径到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 导入GUI主窗口
from gui.circle_detection_main import main

if __name__ == "__main__":
    main()