# OpenCV 抑菌圈检测 - 快速参数与运行指南

本指南提供了一个简单的参数清单与调优流程，便于使用 `opencv-circle-detection` 中已有的检测管线进行快速试验与调参。

## 快速运行（命令行模式）

在仓库 `opencv-circle-detection` 下，使用 headless 模式运行一张图像：

```powershell
python main.py --image "test_images/OIP-C.jpg" --output "out_OIP-C.jpg"
python main.py --image "test_images/R-C.jpg" --output "out_R-C.jpg"
```

运行后会在当前目录生成 `out_*.jpg` 带标注图像，并在控制台打印检测摘要（培养皿数/物质数/抑菌圈数）。

## 主要配置位置

- `opencv-circle-detection/utils/config.py`：默认参数（包括 Hough、预处理、阈值、回退像素范围等）
- `opencv-circle-detection/core/detector.py`：检测逻辑入口，调用 config 中默认值

## 主要参数（默认说明）

1. 培养皿检测
   - dp: 1
   - param1 (Canny 高阈值): 50
   - param2 (Hough 累加阈值): 35

2. 滤纸片 (filter_paper) 默认
   - hough_param1: 60
   - hough_param2: 28
   - brightness_threshold: 120
   - max_std_dev: 25.0
   - radius factor: 0.85 - 1.15（基于 filter_paper_diameter_mm 与 px_per_mm）

3. 挖空 / 透明孔洞 (hole) 默认
   - hough_param1: 40
   - hough_param2: 12
   - brightness_threshold: 90
   - max_std_dev: 35.0
   - radius factor: 0.8 - 1.2

4. 预处理
   - Gaussian blur kernel: (9,9), sigma: 2.0
   - CLAHE clipLimit: 2.0, grid: (8,8)
   - Tophat kernel: (15,15) （用于增强微弱边界）

## 调参建议（快速闭环）

1. 先保证培养皿能被正确检测并产生 `px_per_mm`（使用一张边缘清晰的培养皿图像）。
2. 根据物质类型选择策略（滤纸片/孔洞），使用默认半径范围走一次检测。观察误检/漏检。
3. 若误检多：提高 Hough 的 param2 或增加 minRadius/减小 maxRadius，或加形态学开运算过滤小噪声。
4. 若漏检：降低 param2，增强对比（CLAHE clipLimit+或使用 tophat）并降低 minRadius。
5. 对气泡干扰，多依赖 std_dev 与边际梯度判别规则（代码中已实现相关验证方法）。

## 进一步步骤

- 若需要更高精度，考虑将 `SpecializedInhibitionDetector` 中的径向分析替换或细化为更鲁棒的曲线拟合方法。
- 将常见的最优参数组合保存为 profile（例如 `profiles/filter_paper_windows.json`），便于批量处理时复用。

---
以上为快速指南。如需我将某些默认参数进一步调整到 `utils/config.py` 中，或为某张具体图片进行参数搜索并保存最佳参数，请把图片文件名告诉我。
