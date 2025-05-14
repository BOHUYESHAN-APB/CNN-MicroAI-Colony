import cv2
import numpy as np

# 创建空白图像
img = np.zeros((300, 300, 3), dtype=np.uint8)
img.fill(255)  # 白色背景

# 绘制圆形
cv2.circle(img, (150, 150), 100, (0, 0, 0), -1)  # 黑色实心圆

# 保存图片
cv2.imwrite("opencv-circle-detection/test_images/circle_test.png", img)
print("测试图片已创建: circle_test.png")