# 数据集分类与规范说明

## 按任务类型分类

### 目标检测数据集 (COCO-MMDetection格式)
- **2ClassBlur**: 2类模糊检测（类别1-2）
- **3ClassBacteria**: 3类细菌分类（类别1-3） 
- **Face v1-v3**: 面部检测，3个迭代版本
- **S. Aureus Plates**: 金黄色葡萄球菌检测，含多个分辨率版本

### 实例分割数据集 (COCO-Segmentation格式)
- **Colony Counter Dataset**: 菌落计数分割
- **Micro Teks v1-v8**: 微生物分割，8个版本迭代
- **Lempas v1-v2**: 分割任务数据集

## 按分辨率规格
| 规格 | 分辨率 | 代表数据集 |
|------|--------|------------|
| 标准版 | 640×640 | 大多数数据集 |
| 高清版 | 1280×1280 | S. Aureus Plates V3 |
| 超清版 | 2048×2048 | S. Aureus Plates V4 |

## 按数据规模分类
- **小型测试集**: overfit test、Pre-label test
- **标准三分割**: train/valid/test完整划分
- **多版本迭代**: 
  - micro teks（v1-v8）
  - Petri dishes（v1-v7）

## 主要应用场景
1. **医学检测**
   - 细菌识别
   - 菌落计数

2. **质量控制**  
   - 模糊检测
   - 培养皿检测

3. **算法优化**
   - 不同版本用于模型迭代训练

## 使用规范
1. 目标检测数据集需转换为MMDetection兼容格式
2. 实例分割数据集需包含完整的mask标注
3. 多分辨率数据集应在文件名中注明版本标识