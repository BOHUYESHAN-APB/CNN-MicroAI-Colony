import cv2
import numpy as np

def create_test_image(size=800):
    # 创建空白图像
    img = np.zeros((size, size, 3), dtype=np.uint8)
    img.fill(245)  # 更亮的背景色
    
    # 创建培养皿（直径90mm）
    center = (size//2, size//2)
    plate_radius = size//3
    cv2.circle(img, center, plate_radius, (230, 230, 230), -1)  # 更亮的培养基底色
    
    # 添加纹理使其看起来更自然
    noise = np.random.normal(0, 5, img.shape).astype(np.uint8)
    img = cv2.add(img, noise)
    
    # 计算比例尺（pixels/mm）
    px_per_mm = (2 * plate_radius) / 90  # 90mm是培养皿直径
    
    # 添加滤纸片和抑菌圈
    # 滤纸片直径6mm，每个位置包含主抑菌圈和次级（半透明）抑菌圈的直径
    filter_positions = [
        # (x偏移, y偏移, 主抑菌圈直径mm, 次级抑菌圈直径mm)
        (-20, -20, 16, 20),  # 强抑菌效果，大范围次级抑菌圈
        (20, -20, 12, 16),   # 中等抑菌效果，有重叠区域
        (-20, 20, 14, 18),   # 中强抑菌效果，清晰的双层圈
        (20, 20, 8, 10)      # 弱抑菌效果，轻微次级抑菌圈
    ]
    
    for dx, dy, primary_dia, secondary_dia in filter_positions:
        # 计算实际坐标
        x = center[0] + int(dx * px_per_mm)
        y = center[1] + int(dy * px_per_mm)
        
        # 绘制次级（半透明）抑菌圈
        if secondary_dia > primary_dia:
            secondary_radius = int((secondary_dia/2) * px_per_mm)
            # 创建弱渐变效果
            for r in range(secondary_radius, int(primary_dia/2 * px_per_mm), -1):
                alpha = np.clip((r - primary_dia/2*px_per_mm) /
                              (secondary_radius - primary_dia/2*px_per_mm), 0, 0.6)
                color = int(220 + (255-220) * alpha)
                cv2.circle(img, (x, y), r, (color, color, color), 1)
        
        # 绘制主抑菌圈
        if primary_dia > 6:  # 只在有抑菌效果时绘制
            primary_radius = int((primary_dia/2) * px_per_mm)
            # 创建清晰的渐变效果
            for r in range(primary_radius, int(3*px_per_mm), -1):
                alpha = np.clip((r - 3*px_per_mm) / (primary_radius - 3*px_per_mm), 0, 1)
                color = int(200 + (255-200) * alpha)
                cv2.circle(img, (x, y), r, (color, color, color), 1)
        
        # 绘制滤纸片（6mm直径）
        filter_radius = int(3 * px_per_mm)  # 3mm半径
        # 绘制滤纸片主体
        cv2.circle(img, (x, y), filter_radius, (150, 150, 150), -1)  # 更暗的滤纸片
        # 添加滤纸片边缘和纹理
        cv2.circle(img, (x, y), filter_radius, (130, 130, 130), 1)  # 更暗的边缘
        # 添加纸质纹理
        # 生成并应用纸质纹理
        size = filter_radius * 2 + 1
        # 为每个通道生成相同的纹理
        texture = np.random.normal(0, 2, (size, size)).astype(np.int8)
        texture = np.stack([texture] * 3, axis=-1)  # 复制到3个通道
        
        y1, y2 = y-filter_radius, y+filter_radius+1
        x1, x2 = x-filter_radius, x+filter_radius+1
        
        if (y1 >= 0 and y2 < img.shape[0] and x1 >= 0 and x2 < img.shape[1]):
            paper_region = img[y1:y2, x1:x2].astype(np.int16)
            mask = np.zeros((size, size), dtype=np.uint8)
            cv2.circle(mask, (filter_radius, filter_radius), filter_radius, 255, -1)
            
            # 扩展mask到3个通道
            mask_3d = np.stack([mask] * 3, axis=-1)
            
            # 安全地添加纹理并裁剪到有效范围
            paper_region[mask_3d > 0] = np.clip(
                paper_region[mask_3d > 0] + texture[mask_3d > 0],
                0, 255
            ).astype(np.uint8)
            
            img[y1:y2, x1:x2] = paper_region
    
    # 添加培养皿边缘
    cv2.circle(img, center, plate_radius, (180, 180, 180), 3)  # 更暗且更粗的边缘
    
    return img

# 生成测试图像
test_img = create_test_image(800)

# 保存图片
cv2.imwrite("opencv-circle-detection/test_images/inhibition_zone_test.png", test_img)
print("抑菌圈测试图片已创建: inhibition_zone_test.png")