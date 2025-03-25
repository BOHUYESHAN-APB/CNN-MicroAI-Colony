"""
Dataset structure checker
数据集结构检查工具
"""
import os
from pathlib import Path

def scan_directory(path: str, level: int = 0):
    """Recursively scan directory and print its structure"""
    path = Path(path)
    
    if not path.exists():
        print(f"Path does not exist: {path}")
        return
        
    prefix = "  " * level
    print(f"{prefix}{path.name}/")
    
    try:
        for item in sorted(path.iterdir()):
            if item.is_file():
                if item.suffix.lower() in ['.json', '.jpg', '.jpeg', '.png', '.bmp']:
                    print(f"{prefix}  {item.name}")
            else:
                scan_directory(item, level + 1)
    except Exception as e:
        print(f"{prefix}Error accessing directory: {e}")

def main():
    # Check COCO dataset
    print("\nScanning COCO dataset structure:")
    print("="*50)
    scan_directory("D:/train/S. Aureus Plates V3.v3i.coco-mmdetection")
    
    # Check AGAR demo dataset
    print("\nScanning AGAR demo dataset structure:")
    print("="*50)
    scan_directory("D:/train/AGAR_demo")

if __name__ == "__main__":
    main()
