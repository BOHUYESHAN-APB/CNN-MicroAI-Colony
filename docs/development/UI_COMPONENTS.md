# UI组件文档

## 布局组件

### 1. 基础布局 (Layout)
```tsx
<Layout>
  <Header />
  <Content />
  <Footer />
</Layout>
```

主要特性：
- 响应式设计
- 暗黑模式支持
- iOS风格界面

### 2. 三段式布局
```
+------------------------+
|     快捷操作区域        | -> 顶部区域：工具栏和参数调整
+------------------------+
|                        |
|      主要内容区域       | -> 中部区域：主要显示和交互
|                        |
|                        |
+------------------------+
| 历史  [相机]  设置      | -> 底部区域：导航和主要功能
+------------------------+
```

## 功能组件

### 1. 相机组件 (CameraView)
```tsx
<CameraView
  onCapture={handleCapture}
  onTiltChange={handleTiltChange}
  showLevelIndicator={true}
  resolution={{ width: 1920, height: 1080 }}
/>
```

功能：
- 实时预览
- 自动对焦
- 水平仪显示
- 边框颜色指示

### 2. 水平仪组件 (LevelIndicator)
```tsx
<LevelIndicator 
  xTilt={number}
  yTilt={number}
  threshold={5} // 绿色边框阈值
/>
```

特性：
- 实时角度显示
- 视觉反馈
- 阈值设置
- 动画过渡

### 3. 分析结果展示 (AnalysisResult)
```tsx
<AnalysisResult
  data={analysisData}
  showConfidence={true}
  onExport={handleExport}
/>
```

包含：
- 菌落标记
- 数量统计
- 置信度显示
- 导出选项

## 交互组件

### 1. 控制面板 (ControlPanel)
```tsx
<ControlPanel>
  <ParameterControl />
  <ModelSelector />
  <ExportOptions />
</ControlPanel>
```

功能：
- 参数调整
- 模型选择
- 导出设置

### 2. 图像浏览器 (ImageBrowser)
```tsx
<ImageBrowser
  images={imageList}
  onSelect={handleSelect}
  sortBy="date"
/>
```

特性：
- 缩略图预览
- 排序筛选
- 批量选择

### 3. 工具栏 (Toolbar)
```tsx
<Toolbar>
  <Button icon="camera" />
  <Button icon="analyze" />
  <Button icon="export" />
</Toolbar>
```

## 状态组件

### 1. 加载指示器 (LoadingIndicator)
```tsx
<LoadingIndicator
  type="spinner"
  text="分析中..."
/>
```

### 2. 状态提示 (StatusIndicator)
```tsx
<StatusIndicator
  status="success|error|warning"
  message="操作成功"
/>
```

## 样式指南

### 1. 颜色系统
```css
:root {
  /* 主题色 */
  --primary: #1976d2;
  --secondary: #424242;
  --success: #4caf50;
  --warning: #ff9800;
  --error: #f44336;
  
  /* 灰度 */
  --gray-100: #f5f5f5;
  --gray-200: #eeeeee;
  --gray-300: #e0e0e0;
  --gray-400: #bdbdbd;
  --gray-500: #9e9e9e;
  
  /* 暗色主题 */
  --dark-bg: #121212;
  --dark-surface: #1e1e1e;
  --dark-primary: #90caf9;
}
```

### 2. 间距系统
```css
:root {
  --spacing-xs: 0.25rem;
  --spacing-sm: 0.5rem;
  --spacing-md: 1rem;
  --spacing-lg: 1.5rem;
  --spacing-xl: 2rem;
}
```

### 3. 字体系统
```css
:root {
  --font-family: -apple-system, system-ui, sans-serif;
  --font-size-sm: 0.875rem;
  --font-size-md: 1rem;
  --font-size-lg: 1.125rem;
  --font-weight-normal: 400;
  --font-weight-medium: 500;
  --font-weight-bold: 700;
}
```

## 响应式设计

### 1. 断点设置
```css
/* 移动端优先 */
@media (min-width: 640px) { /* 小屏幕 */ }
@media (min-width: 768px) { /* 中等屏幕 */ }
@media (min-width: 1024px) { /* 大屏幕 */ }
@media (min-width: 1280px) { /* 超大屏幕 */ }
```

### 2. 布局适配
```tsx
<Grid
  cols={{
    base: 1,    // 移动端
    sm: 2,      // 小屏幕
    md: 3,      // 中等屏幕
    lg: 4       // 大屏幕
  }}
>
  {/* 内容 */}
</Grid>
```

## 动画系统

### 1. 过渡效果
```css
.transition-base {
  transition: all 0.3s ease;
}

.transition-smooth {
  transition: all 0.5s cubic-bezier(0.4, 0, 0.2, 1);
}
```

### 2. 动画定义
```css
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes slideIn {
  from { transform: translateY(20px); }
  to { transform: translateY(0); }
}
```

## 辅助功能

### 1. 无障碍支持
```tsx
<Button
  aria-label="拍照"
  role="button"
  tabIndex={0}
>
  拍照
</Button>
```

### 2. 键盘导航
```tsx
<FocusTrap>
  <Dialog>
    <Button onKeyDown={handleKeyDown}>
      确认
    </Button>
  </Dialog>
</FocusTrap>
```

## 最佳实践

1. 组件封装
   - 单一职责
   - 可复用性
   - 可测试性

2. 性能优化
   - 懒加载
   - 虚拟列表
   - 缓存策略

3. 错误处理
   - 优雅降级
   - 错误边界
   - 用户反馈
