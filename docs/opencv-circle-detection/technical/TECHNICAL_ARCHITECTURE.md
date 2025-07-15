# OpenCV抑菌圈检测系统 - 技术架构文档

## 🏗️ 系统架构概览

### 整体架构设计

```
┌─────────────────────────────────────────────────────────────┐
│                    用户界面层 (GUI Layer)                     │
├─────────────────────────────────────────────────────────────┤
│  单张处理GUI  │  批量处理GUI  │  精度验证GUI  │  配置管理    │
└─────────────────────────────────────────────────────────────┘
                               │
┌─────────────────────────────────────────────────────────────┐
│                    业务逻辑层 (Business Layer)                │
├─────────────────────────────────────────────────────────────┤
│  检测控制器   │  结果处理器   │  批量管理器   │  验证管理器   │
└─────────────────────────────────────────────────────────────┘
                               │
┌─────────────────────────────────────────────────────────────┐
│                    算法引擎层 (Algorithm Layer)               │
├─────────────────────────────────────────────────────────────┤
│ 原始检测器 │ 修正检测器 │ 图像预处理 │ 特征提取 │ 精度评估 │
└─────────────────────────────────────────────────────────────┘
                               │
┌─────────────────────────────────────────────────────────────┐
│                    数据存储层 (Data Layer)                    │
├─────────────────────────────────────────────────────────────┤
│  图像文件   │  检测结果   │  配置数据   │  标准答案   │  日志  │
└─────────────────────────────────────────────────────────────┘
```

## 🔧 核心组件详解

### 1. 检测算法引擎

#### 检测器类层次结构
```python
BaseDetector (抽象基类)
├── CircleDetector (原始检测器)
│   ├── detect_petri_dishes()
│   ├── detect_filter_papers()
│   └── detect_holes()
├── CorrectedDetector (修正检测器)
│   ├── detect_transparent_holes_corrected()
│   └── detect_filter_papers_corrected()
└── SimpleDetector (简化检测器)
    ├── detect_petri_dish()
    ├── detect_substances()
    └── detect_zones()
```

#### 算法流程图
```
输入图像
    │
    ▼
图像预处理
├── 灰度转换
├── 噪声去除
├── 对比度增强
└── 尺寸标准化
    │
    ▼
培养皿检测
├── 霍夫圆检测
├── 候选圆筛选
├── 尺寸验证
└── 像素标定
    │
    ▼
抑菌物质检测
├── 滤纸片检测 ──── 亮度阈值分割
│                ├── 形态学操作
│                └── 轮廓分析
├── 透明挖孔检测 ── 反转图像处理
│                ├── 边缘检测
│                └── 圆形拟合
└── 自动类型判断
    │
    ▼
抑菌圈检测
├── ROI提取
├── 边缘增强
├── 轮廓检测
└── 圆形拟合
    │
    ▼
结果输出
├── 坐标转换
├── 尺寸计算
├── 数据封装
└── 可视化标注
```

### 2. 图像处理管道

#### 预处理模块
```python
class ImagePreprocessor:
    def __init__(self):
        self.filters = [
            GrayscaleConverter(),
            NoiseReducer(),
            ContrastEnhancer(),
            SizeNormalizer()
        ]
    
    def process(self, image):
        for filter in self.filters:
            image = filter.apply(image)
        return image
```

#### 核心算法实现

##### 霍夫圆检测
```python
def detect_circles(self, image, min_radius, max_radius):
    """霍夫圆检测实现"""
    circles = cv2.HoughCircles(
        image,
        cv2.HOUGH_GRADIENT,
        dp=1,                    # 累加器分辨率
        minDist=min_radius*2,    # 圆心最小距离
        param1=50,               # Canny边缘检测高阈值
        param2=30,               # 累加器阈值
        minRadius=min_radius,    # 最小半径
        maxRadius=max_radius     # 最大半径
    )
    return self.filter_valid_circles(circles)
```

##### 自适应阈值分割
```python
def adaptive_threshold(self, image, method='gaussian'):
    """自适应阈值分割"""
    if method == 'gaussian':
        return cv2.adaptiveThreshold(
            image, 255, 
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 11, 2
        )
    elif method == 'otsu':
        _, thresh = cv2.threshold(
            image, 0, 255, 
            cv2.THRESH_BINARY + cv2.THRESH_OTSU
        )
        return thresh
```

### 3. GUI架构设计

#### 主要界面组件
```python
MainWindow (QMainWindow)
├── ControlPanel (QWidget)
│   ├── FileOperations
│   ├── DetectorSelector  
│   ├── ParameterSettings
│   └── DetectionControls
├── DisplayArea (QWidget)
│   ├── ImageDisplay (QLabel)
│   ├── ResultsTabs (QTabWidget)
│   │   ├── VisualizationTab
│   │   ├── StatisticsTab
│   │   └── DetailedDataTab
│   └── ProgressBar
└── StatusBar (QStatusBar)
```

#### 多线程处理架构
```python
class DetectionWorker(QThread):
    """检测工作线程"""
    progress_updated = pyqtSignal(int)
    detection_finished = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    
    def run(self):
        # 后台执行检测任务
        # 发送进度更新信号
        # 完成后发送结果信号
```

### 4. 数据模型设计

#### 核心数据结构
```python
@dataclass
class DetectionResult:
    """检测结果数据模型"""
    filename: str
    timestamp: datetime
    dish: PetriDish
    substances: List[Substance]
    zones: List[InhibitionZone]
    px_per_mm: float
    processing_time: float

@dataclass  
class PetriDish:
    """培养皿数据模型"""
    center: Tuple[int, int]
    radius: int
    diameter_mm: float
    confidence: float

@dataclass
class Substance:
    """抑菌物质数据模型"""
    center: Tuple[int, int] 
    radius: int
    substance_type: SubstanceType
    confidence: float

@dataclass
class InhibitionZone:
    """抑菌圈数据模型"""
    center: Tuple[int, int]
    radius: int
    diameter_mm: float
    associated_substance: Substance
```

## 🔄 核心算法原理

### 1. 培养皿检测算法

#### 霍夫圆变换原理
霍夫圆变换是一种在图像中检测圆形的有效方法：

1. **边缘检测**：使用Canny算子检测图像边缘
2. **参数空间投票**：每个边缘点对可能的圆心位置投票
3. **峰值检测**：在参数空间中找到投票峰值
4. **圆验证**：验证检测到的圆是否满足几何约束

#### 参数优化策略
```python
def optimize_hough_params(self, image_size):
    """根据图像尺寸优化霍夫圆参数"""
    min_radius = int(image_size[0] * 0.2)  # 最小半径为图像宽度的20%
    max_radius = int(image_size[0] * 0.6)  # 最大半径为图像宽度的60%
    min_dist = min_radius * 1.5            # 最小距离为最小半径的1.5倍
    
    return {
        'minRadius': min_radius,
        'maxRadius': max_radius, 
        'minDist': min_dist,
        'param1': 50,  # 根据图像噪声水平调整
        'param2': 30   # 根据期望检测灵敏度调整
    }
```

### 2. 抑菌物质检测算法

#### 滤纸片检测策略
基于亮度差异的检测方法：

1. **阈值分割**：使用OTSU自动阈值或固定阈值
2. **形态学操作**：开运算去除噪声，闭运算填充空洞
3. **轮廓分析**：提取连通域轮廓
4. **几何筛选**：根据面积、圆形度等特征筛选

```python
def detect_filter_papers(self, image, dish):
    """滤纸片检测实现"""
    # 1. 创建培养皿掩码
    mask = self.create_dish_mask(image, dish)
    masked_image = cv2.bitwise_and(image, mask)
    
    # 2. 阈值分割
    _, binary = cv2.threshold(masked_image, 0, 255, 
                             cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    # 3. 形态学操作
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
    
    # 4. 轮廓检测和筛选
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, 
                                  cv2.CHAIN_APPROX_SIMPLE)
    return self.filter_substances_by_geometry(contours)
```

#### 透明挖孔检测策略
基于边缘和形状的检测方法：

1. **图像反转**：将挖孔区域转换为亮区域
2. **边缘检测**：使用Canny算子检测边缘
3. **轮廓提取**：提取闭合轮廓
4. **圆形拟合**：对轮廓进行圆形拟合

### 3. 抑菌圈检测算法

#### 区域增长策略
在抑菌物质周围搜索抑菌圈：

1. **ROI确定**：以抑菌物质为中心确定搜索区域
2. **梯度分析**：分析径向梯度变化
3. **边缘检测**：检测抑菌圈边界
4. **圆形拟合**：拟合最佳圆形边界

```python
def detect_inhibition_zones(self, image, substances):
    """抑菌圈检测实现"""
    zones = []
    for substance in substances:
        # 1. 提取ROI
        roi = self.extract_roi_around_substance(image, substance)
        
        # 2. 径向梯度分析
        gradients = self.compute_radial_gradients(roi, substance.center)
        
        # 3. 边缘检测
        edges = cv2.Canny(roi, 50, 150)
        
        # 4. 圆形拟合
        zone = self.fit_circular_boundary(edges, substance)
        if zone:
            zones.append(zone)
    
    return zones
```

## 📊 性能优化策略

### 1. 算法优化

#### 多尺度检测
```python
def multi_scale_detection(self, image, scales=[0.5, 1.0, 1.5]):
    """多尺度检测提高鲁棒性"""
    results = []
    for scale in scales:
        resized = cv2.resize(image, None, fx=scale, fy=scale)
        detection = self.single_scale_detection(resized)
        # 将结果缩放回原始尺寸
        scaled_result = self.scale_result(detection, 1/scale)
        results.append(scaled_result)
    
    return self.merge_multi_scale_results(results)
```

#### 感兴趣区域优化
```python
def roi_based_detection(self, image, dish):
    """基于ROI的检测优化"""
    # 只在培养皿内部进行检测，显著减少计算量
    roi_mask = self.create_dish_mask(image, dish, margin=0.9)
    roi_image = cv2.bitwise_and(image, roi_mask)
    
    # 在ROI内进行检测
    substances = self.detect_in_roi(roi_image)
    
    return substances
```

### 2. 内存优化

#### 图像缓存管理
```python
class ImageCache:
    """图像缓存管理器"""
    def __init__(self, max_size_mb=500):
        self.cache = {}
        self.max_size = max_size_mb * 1024 * 1024
        self.current_size = 0
    
    def get_processed_image(self, image_path, processor):
        """获取处理后的图像，使用缓存加速"""
        cache_key = f"{image_path}_{hash(processor)}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        # 处理图像并缓存
        processed = processor.process(cv2.imread(image_path))
        self.add_to_cache(cache_key, processed)
        return processed
```

### 3. 并发处理

#### 批量处理优化
```python
from concurrent.futures import ThreadPoolExecutor
import multiprocessing

class BatchProcessor:
    """批量处理优化器"""
    def __init__(self, max_workers=None):
        if max_workers is None:
            max_workers = min(4, multiprocessing.cpu_count())
        self.max_workers = max_workers
    
    def process_batch(self, image_paths, detector):
        """并行批量处理"""
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [executor.submit(detector.detect, path) 
                      for path in image_paths]
            
            results = []
            for future in futures:
                try:
                    result = future.result(timeout=60)  # 60秒超时
                    results.append(result)
                except Exception as e:
                    logging.error(f"批量处理出错: {e}")
                    results.append(None)
            
            return results
```

## 🔧 扩展和定制

### 1. 新检测器开发

#### 检测器接口
```python
from abc import ABC, abstractmethod

class BaseDetector(ABC):
    """检测器基类"""
    
    @abstractmethod
    def detect_petri_dishes(self, image):
        """检测培养皿"""
        pass
    
    @abstractmethod  
    def detect_substances(self, image, dish):
        """检测抑菌物质"""
        pass
    
    @abstractmethod
    def detect_zones(self, image, substances):
        """检测抑菌圈"""
        pass
```

#### 自定义检测器示例
```python
class CustomDetector(BaseDetector):
    """自定义检测器实现"""
    
    def __init__(self, custom_params):
        self.params = custom_params
        
    def detect_petri_dishes(self, image):
        # 实现自定义培养皿检测逻辑
        pass
        
    def detect_substances(self, image, dish):
        # 实现自定义物质检测逻辑  
        pass
        
    def detect_zones(self, image, substances):
        # 实现自定义抑菌圈检测逻辑
        pass
```

### 2. 插件系统设计

#### 插件接口
```python
class DetectionPlugin(ABC):
    """检测插件接口"""
    
    @abstractmethod
    def get_name(self):
        """获取插件名称"""
        pass
    
    @abstractmethod
    def get_version(self):
        """获取插件版本"""
        pass
    
    @abstractmethod
    def process_image(self, image, params):
        """处理图像"""
        pass
```

## 📝 开发规范

### 1. 代码结构规范

```
opencv-circle-detection/
├── core/                   # 核心算法模块
│   ├── __init__.py
│   ├── detectors/         # 检测器实现
│   ├── processors/        # 图像处理器
│   └── models/           # 数据模型
├── gui/                   # 用户界面模块
│   ├── __init__.py
│   ├── widgets/          # 界面组件
│   ├── controllers/      # 界面控制器
│   └── resources/        # 界面资源
├── utils/                 # 工具模块
│   ├── __init__.py
│   ├── image_utils.py    # 图像工具
│   ├── math_utils.py     # 数学工具
│   └── validation.py     # 验证工具
├── tests/                 # 测试模块
├── docs/                  # 文档
└── examples/              # 示例代码
```

### 2. 命名规范

- **类名**：使用PascalCase，如 `CircleDetector`
- **函数名**：使用snake_case，如 `detect_circles`
- **常量**：使用UPPER_CASE，如 `DEFAULT_RADIUS`
- **变量**：使用snake_case，如 `image_path`

### 3. 文档规范

```python
def detect_circles(self, image: np.ndarray, min_radius: int = 10, 
                  max_radius: int = 100) -> List[Circle]:
    """
    检测图像中的圆形。
    
    Args:
        image: 输入图像，BGR格式
        min_radius: 最小圆半径
        max_radius: 最大圆半径
        
    Returns:
        检测到的圆形列表
        
    Raises:
        ValueError: 当输入参数无效时
        
    Example:
        >>> detector = CircleDetector()
        >>> circles = detector.detect_circles(image, 20, 80)
    """
```

---

*技术架构文档版本：v1.0*  
*最后更新：2025年7月15日*