import os
from pathlib import Path

def check_and_create_directories():
    """检查并创建所需的资源目录"""
    app_dir = Path(__file__).parent
    
    # 需要创建的目录
    required_dirs = [
        'resources/themes',
        'resources/i18n',
        'logs',
        'config/defaults',
        'results'
    ]
    
    # 创建目录
    for dir_path in required_dirs:
        full_path = app_dir / dir_path
        if not full_path.exists():
            print(f"Creating directory: {full_path}")
            full_path.mkdir(parents=True, exist_ok=True)
        else:
            print(f"Directory exists: {full_path}")
    
    print("\nResource structure check completed.")

if __name__ == "__main__":
    check_and_create_directories()
