import cv2
import numpy as np
from dataclasses import dataclass
from typing import List, Optional, Tuple

@dataclass
class Colony:
    center: Tuple[int, int]
    radius: int
    contour: np.ndarray
    inhibition_zone: Optional[Tuple[int, int, int]] = None

@dataclass
class PetriDish:
    center: Tuple[int, int]
    radius: int
    colonies: List[Colony]
    diameter_mm: float

class CircleDetector:
    def __init__(self, plate_diameter_mm=90):
        self.plate_diameter_mm = plate_diameter_mm
    
    def detect_petri_dishes(self, image: np.ndarray) -> List[PetriDish]:
        """检测培养皿"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (9, 9), 2)
        
        # 修改霍夫圆检测参数
        plates = cv2.HoughCircles(blurred, cv2.HOUGH_GRADIENT, dp=1, minDist=300,  # 增加最小距离
                                param1=50, param2=35,  # 提高参数2的阈值
                                minRadius=int(image.shape[0]/3),  # 增加最小半径
                                maxRadius=int(image.shape[0]/1.5))
        
        if plates is None:
            raise Exception("未检测到培养皿")
        
        plates = np.uint16(np.around(plates[0, :]))
        petri_dishes = []
        
        # 按半径大小排序并只保留最大的圆作为培养皿
        sorted_plates = sorted(plates, key=lambda x: x[2], reverse=True)
        plate = sorted_plates[0]  # 只使用最大的圆
        
        petri_dishes.append(PetriDish(
            center=(plate[0], plate[1]),
            radius=plate[2],
            colonies=[],
            diameter_mm=self.plate_diameter_mm
        ))
        
        return petri_dishes

    def detect_colonies_in_dish(self, image: np.ndarray, dish: PetriDish) -> List[Colony]:
        """在培养皿内检测菌落"""
        # 创建培养皿mask
        mask = np.zeros_like(cv2.cvtColor(image, cv2.COLOR_BGR2GRAY))
        cv2.circle(mask, dish.center, dish.radius, 255, -1)
        
        # 在mask区域内处理图像
        masked = cv2.bitwise_and(image, image, mask=mask)
        gray = cv2.cvtColor(masked, cv2.COLOR_BGR2GRAY)
        
        # 增强对比度
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
        gray = clahe.apply(gray)
        
        # 自适应阈值分割，调整参数
        binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                     cv2.THRESH_BINARY_INV, 25, 3)
        
        # 形态学操作，调整核大小
        kernel = np.ones((7,7), np.uint8)
        morphed = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
        morphed = cv2.morphologyEx(morphed, cv2.MORPH_CLOSE, kernel)
        
        # 查找轮廓
        contours, _ = cv2.findContours(morphed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        colonies = []
        mm_per_pixel = self.plate_diameter_mm / (2 * dish.radius)
        min_colony_radius = int(dish.radius * 0.05)  # 最小菌落半径
        max_colony_radius = int(dish.radius * 0.2)   # 最大菌落半径
        
        for contour in contours:
            # 获取最小外接圆
            (x, y), radius = cv2.minEnclosingCircle(contour)
            center = (int(x), int(y))
            radius = int(radius)
            
            # 过滤条件
            if radius < min_colony_radius or radius > max_colony_radius:
                continue
                
            # 检查是否在培养皿内的有效区域
            dist_to_center = np.sqrt((center[0] - dish.center[0])**2 + 
                                   (center[1] - dish.center[1])**2)
            if dist_to_center > dish.radius * 0.8:  # 排除边缘区域
                continue
            
            # 创建Colony对象
            colony = Colony(center=center, radius=radius, contour=contour)
            
            # 检测抑菌圈
            inhibition = self.detect_inhibition_zone(gray, colony, dish)
            if inhibition:
                colony.inhibition_zone = inhibition
            
            colonies.append(colony)
        
        return colonies

    def detect_inhibition_zone(self, gray: np.ndarray, colony: Colony, dish: PetriDish) -> Optional[Tuple[int, int, int]]:
        """检测抑菌圈"""
        # 在菌落周围区域检测
        mask = np.zeros_like(gray)
        search_radius = min(int(colony.radius * 3.5), int(dish.radius * 0.8))
        cv2.circle(mask, colony.center, search_radius, 255, -1)
        cv2.circle(mask, colony.center, colony.radius, 0, -1)  # 排除菌落区域
        
        # 应用mask
        masked = cv2.bitwise_and(gray, gray, mask=mask)
        
        # 边缘检测，调整参数
        edges = cv2.Canny(masked, 30, 150)
        
        # 霍夫圆检测，调整参数
        circles = cv2.HoughCircles(edges, cv2.HOUGH_GRADIENT, dp=1, minDist=colony.radius*2,
                                 param1=40, param2=15,
                                 minRadius=int(colony.radius * 1.2),  # 确保抑菌圈大于菌落
                                 maxRadius=search_radius)
        
        if circles is not None:
            circles = np.uint16(np.around(circles[0, :]))
            # 选择最接近菌落中心的圆
            min_dist = float('inf')
            best_circle = None
            
            for circle in circles:
                x, y, r = circle
                dist = np.sqrt((x - colony.center[0])**2 + (y - colony.center[1])**2)
                if dist < min_dist:
                    min_dist = dist
                    best_circle = circle
            
            if best_circle is not None:
                return (best_circle[0], best_circle[1], best_circle[2])
        
        return None

    def draw_results(self, image: np.ndarray, dishes: List[PetriDish]) -> np.ndarray:
        """绘制检测结果"""
        result = image.copy()
        
        for i, dish in enumerate(dishes):
            # 绘制培养皿
            cv2.circle(result, dish.center, dish.radius, (255, 0, 0), 2)
            
            # 安全地计算文本位置
            text_x = np.clip(dish.center[0] - 50, 10, result.shape[1] - 200)
            text_y = np.clip(dish.center[1] - dish.radius - 10, 30, result.shape[0] - 10)
            
            cv2.putText(result, f'培养皿 {i+1}: {dish.diameter_mm}mm',
                       (text_x, text_y),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 0, 0), 2)
            
            mm_per_pixel = self.plate_diameter_mm / (2 * dish.radius)
            
            for j, colony in enumerate(dish.colonies):
                # 绘制菌落
                cv2.drawContours(result, [colony.contour], -1, (0, 255, 255), 2)
                colony_diameter = 2 * colony.radius * mm_per_pixel
                
                # 安全地计算文本位置
                text_x = np.clip(colony.center[0] - 40, 10, result.shape[1] - 150)
                text_y = np.clip(colony.center[1] - 10, 30, result.shape[0] - 10)
                
                cv2.putText(result, f'菌落 {j+1}: {colony_diameter:.1f}mm',
                           (text_x, text_y),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
                
                # 绘制抑菌圈
                if colony.inhibition_zone:
                    x, y, r = colony.inhibition_zone
                    cv2.circle(result, (x, y), r, (0, 255, 0), 2)
                    inhibition_diameter = 2 * r * mm_per_pixel
                    
                    # 安全地计算文本位置
                    text_x = np.clip(x - 40, 10, result.shape[1] - 150)
                    text_y = np.clip(y - r - 10, 30, result.shape[0] - 10)
                    
                    cv2.putText(result, f'抑菌圈: {inhibition_diameter:.1f}mm',
                               (text_x, text_y),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        return result

    def process_image(self, image_path: str) -> np.ndarray:
        """处理图像并返回结果"""
        # 读取图片
        img = cv2.imread(image_path)
        if img is None:
            raise Exception(f"无法读取图片: {image_path}")
        
        # 检测培养皿
        dishes = self.detect_petri_dishes(img)
        print(f"检测到 {len(dishes)} 个培养皿")
        
        # 对每个培养皿检测菌落和抑菌圈
        for i, dish in enumerate(dishes):
            dish.colonies = self.detect_colonies_in_dish(img, dish)
            print(f"在培养皿 {i+1} 内检测到 {len(dish.colonies)} 个菌落")
        
        # 绘制结果
        return self.draw_results(img, dishes)

def main():
    detector = CircleDetector()
    image_path = "test_images/R-C.jpg"
    
    try:
        result = detector.process_image(image_path)
        
        # 保存结果
        cv2.imwrite("test_images/result.png", result)
        
        # 显示结果
        cv2.imshow('检测结果', result)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        
    except Exception as e:
        print(f"处理失败: {str(e)}")

if __name__ == "__main__":
    main()