import cv2
import numpy as np
from pathlib import Path
import logging
from core.detector import CircleDetector
from core.models import Colony, PetriDish

# Configure logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

def process_image(image_path: str):
    """处理单张图片并显示结果"""
    logger.info(f"处理图片: {image_path}")
    
    # 读取图片
    image = cv2.imread(image_path)
    if image is None:
        logger.error(f"无法读取图片: {image_path}")
        return
        
    # 创建检测器
    detector = CircleDetector()
    
    # 1. 检测培养皿
    dishes = detector.detect_petri_dishes(image)
    if not dishes:
        logger.warning("未检测到培养皿")
        return
        
    dish = dishes[0]
    logger.info(f"培养皿检测结果: 中心({dish.center}), 半径{dish.radius}px")
    
    # 2. 检测滤纸片
    papers = detector.detect_filter_papers(image, dish)
    logger.info(f"检测到 {len(papers)} 个滤纸片")
    
    # 3. 检测抑菌圈
    zones = detector.detect_inhibition_zones(image, papers)
    
    # 绘制结果
    result = image.copy()
    
    # 绘制培养皿
    cv2.circle(result, dish.center, dish.radius, (0, 255, 0), 2)
    cv2.putText(result, f"Dish: {dish.diameter_mm}mm", 
               (dish.center[0] - dish.radius, dish.center[1] - dish.radius - 10),
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    
    # 绘制滤纸片和抑菌圈
    for zone in zones:
        paper = zone['paper']
        primary = zone['primary_zone']
        
        # 绘制滤纸片
        cv2.circle(result, paper.center, paper.radius, (255, 0, 0), 2)
        cv2.circle(result, paper.center, 2, (0, 0, 255), -1)
        
        # 绘制主抑菌圈
        if primary:
            cv2.circle(result, primary['center'], primary['radius'], (0, 255, 255), 2)
            cv2.putText(result, f"{primary['diameter_mm']:.1f}mm",
                       (primary['center'][0] + primary['radius'] + 5, primary['center'][1]),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
    
    # 显示结果
    cv2.imshow("Detection Result", result)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

def main():
    test_dir = Path("test_images")
    if not test_dir.exists():
        logger.error(f"测试目录 {test_dir} 不存在")
        return
    
    # 处理所有测试图片
    for img_path in test_dir.glob("*.jpg"):
        process_image(str(img_path))
        
        # 询问是否继续
        key = input("按Enter处理下一张图片，或输入q退出: ")
        if key.lower() == 'q':
            break

if __name__ == "__main__":
    main()