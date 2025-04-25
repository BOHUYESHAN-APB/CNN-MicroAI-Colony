# Android应用设计文档

## 1. 技术架构

### 1.1 前端架构
- **UI框架**: Jetpack Compose
- **设计风格**: iOS简约风格
- **核心组件**:
  - CameraX: 相机功能
  - Room: 本地数据存储
  - Retrofit: API请求
  - DataStore: 轻量级存储
  - WorkManager: 后台任务

### 1.2 后端集成
- 复用现有Flask API
- 新增endpoints:
  - 实时视频流处理
  - LLM分析接口
  - 批量数据统计

## 2. 功能模块

### 2.1 首页(MainActivity)
```
|- 顶部工具栏
   |- 标题
   |- 设置按钮
|- 主要功能区
   |- 实时检测按钮
   |- 拍照检测按钮
|- 最近记录
   |- 横向滚动列表
   |- 快速查看结果
```

### 2.2 检测界面(DetectionActivity)
```
|- 相机预览
|- 控制按钮
   |- 拍照/录制
   |- 闪光灯
   |- 切换相机
|- 实时检测结果显示
```

### 2.3 历史记录(HistoryFragment)
```
|- 筛选选项
|- 记录列表
   |- 缩略图
   |- 检测结果
   |- 时间戳
   |- 分享按钮
```

### 2.4 分析报告(AnalysisFragment)
```
|- 数据概览
   |- 总检测次数
   |- 平均数量
   |- 趋势图表
|- LLM分析结果
   |- 菌落密集度
   |- 数量统计
   |- 置信度分析
   |- 培养状况(待扩展)
   |- 菌落状况(待扩展)
|- 导出选项
```

### 2.5 设置(SettingsFragment)
```
|- 应用主题
|- 语言设置
|- 检测配置
|- 存储管理
```

## 3. 数据结构

### 3.1 本地数据库表
```kotlin
// 检测记录
data class DetectionRecord(
    val id: Long,
    val imageUri: String,
    val timestamp: Long,
    val colonyCount: Int,
    val confidence: Float,
    val analysisResult: String,
    val llmAnalysis: String?
)

// 分析报告
data class AnalysisReport(
    val id: Long,
    val recordId: Long,
    val density: Float,
    val distribution: String,
    val llmComments: String,
    val timestamp: Long
)
```

## 4. API接口

### 4.1 现有接口复用
- `/api/analyze`: 单张图片分析
- `/api/analyze_batch`: 批量分析
- `/api/annotated_image`: 生成标注图片

### 4.2 新增接口
```
POST /api/stream_analyze
- 实时视频流分析
- WebSocket连接
- 返回实时检测结果

POST /api/llm_analyze
- 输入：检测结果数据
- 返回：LLM分析报告

GET /api/statistics
- 返回数据统计信息
- 支持时间范围筛选
```

## 5. 后续扩展计划

### 5.1 模型增强
- 添加菌落形态分析
- 添加培养状况评估
- 提高检测准确度

### 5.2 功能扩展
- 离线模型支持
- 自动报告生成
- 数据同步功能
- 多设备协同

## 6. UI设计原则

### 6.1 配色方案
```
主色调: #FFFFFF (白色背景)
强调色: #007AFF (iOS蓝)
文字颜色:
  - 主要文字: #000000
  - 次要文字: #8E8E93
  - 提示文字: #C7C7CC
```

### 6.2 交互原则
- 手势操作优先
- 动画流畅自然
- 即时反馈
- 清晰的视觉层级
