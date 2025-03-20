"""Generate test pattern images"""
import os
import cv2
import numpy as np

def create_test_pattern(width=800, height=600, num_colonies=50):
    """Create artificial colony test pattern"""
    # 创建白色背景
    img = np.ones((height, width, 3), dtype=np.uint8) * 255
    
    # 随机生成菌落
    for _ in range(num_colonies):
        # 随机位置
        x = np.random.randint(50, width-50)
        y = np.random.randint(50, height-50)
        
        # 随机大小
        radius = np.random.randint(10, 30)
        
        # 随机颜色(灰白色)
        color = np.random.randint(180, 220)
        
        # 绘制菌落(带柔和边缘)
        cv2.circle(img, (x, y), radius, (color, color, color), -1)
        cv2.circle(img, (x, y), radius+2, (color+20, color+20, color+20), 2)
        
    return img

def main():
    # 获取当前脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(script_dir, "test_images")
    
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    # 生成不同密度的测试图片
    densities = [20, 50, 100]
    for density in densities:
        img = create_test_pattern(num_colonies=density)
        filename = os.path.join(output_dir, f"pattern_{density}.jpg")
        cv2.imwrite(filename, img)
        print(f"Created {filename}")

if __name__ == "__main__":
    main()
