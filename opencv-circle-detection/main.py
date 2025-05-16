import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication

from gui.main_window import MainWindow
from utils.config import Config
from core.processor import ImageProcessor
from core.detector import CircleDetector

def main():
    """程序入口函数"""
    try:
        # 创建应用实例
        app = QApplication(sys.argv)
        
        # 设置应用样式
        app.setStyle('Fusion')
        
        # 创建主窗口
        window = MainWindow()
        window.show()
        
        # 运行应用
        sys.exit(app.exec())
        
    except Exception as e:
        print(f"程序运行出错: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()