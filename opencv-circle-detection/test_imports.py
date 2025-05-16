import sys
from pathlib import Path

# 将项目根目录添加到Python路径
project_root = Path(__file__).parent
sys.path.append(str(project_root))

# 测试导入
try:
    print("测试core包导入...")
    from core.detector import CircleDetector
    from core.processor import ImageProcessor
    from core.models import Colony, PetriDish
    print("core包导入成功")

    print("\n测试utils包导入...")
    from utils.config import Config
    print("utils包导入成功")

    print("\n测试gui包导入...")
    from gui.main_window import MainWindow
    from gui.image_view import ImageViewer
    from gui.report_view import ReportView
    print("gui包导入成功")

except ImportError as e:
    print(f"导入失败: {str(e)}")
    sys.exit(1)

print("\n所有包导入测试成功！")