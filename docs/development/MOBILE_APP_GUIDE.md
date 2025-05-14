# 移动应用开发指南

## 技术栈

- Flutter
- Dart
- 相机API
- 传感器API

## 功能模块

### 1. 相机模块

```dart
class CameraModule {
  // 相机预览
  // 自动对焦
  // 水平仪显示
  // 拍照功能
}
```

#### 水平仪实现
- 使用加速度传感器
- 5度以内显示绿色边框
- 实时角度显示

### 2. 界面布局

#### 主界面
```
+------------------------+
|     状态栏和设置        |
+------------------------+
|                        |
|      相机预览区域       |
|                        |
|     水平仪指示器        |
|                        |
+------------------------+
|   历史  [拍照]  分析    |
+------------------------+
```

#### 分析界面
```
+------------------------+
|     分析结果展示        |
+------------------------+
|    - 菌落总数          |
|    - 位置标记          |
|    - 大小分布          |
|    - 置信度            |
+------------------------+
|     导出/分享按钮      |
+------------------------+
```

### 3. 数据管理

#### 本地存储
- 使用SQLite存储历史记录
- 图片存储在应用专有目录
- 工程文件管理

#### 数据同步
- 支持离线使用
- 可选的云端同步
- 数据导出功能

### 4. 项目结构

```
lib/
├── main.dart              # 应用入口
├── routes.dart            # 路由配置
├── modules/               # 功能模块
│   ├── camera/           # 相机相关
│   ├── analysis/         # 分析相关
│   └── settings/         # 设置相关
├── models/               # 数据模型
├── services/            # 后端服务
├── utils/              # 工具函数
└── widgets/           # UI组件
```

## 开发规范

### 1. 代码规范

- 使用 `flutter_lints` 进行代码检查
- 遵循Flutter官方风格指南
- 使用async/await处理异步

### 2. 性能优化

- 使用const构造函数
- 避免不必要的重建
- 图片缓存管理
- 内存使用监控

### 3. 文件命名

- 小写加下划线
- 描述性命名
- 避免缩写

### 4. 组件设计

- 职责单一
- 参数明确
- 状态管理清晰
- 错误处理完善

## 示例代码

### 1. 相机预览

```dart
class CameraPreview extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Stack(
      children: [
        CameraView(),
        LevelIndicator(),
        CaptureButton(),
      ],
    );
  }
}
```

### 2. 水平仪显示

```dart
class LevelIndicator extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return StreamBuilder<AccelerometerEvent>(
      stream: accelerometerEvents,
      builder: (context, snapshot) {
        // 计算倾斜角度
        final angles = calculateTiltAngles(snapshot.data);
        // 检查是否在5度范围内
        final isLevel = checkIsLevel(angles);
        
        return Container(
          decoration: BoxDecoration(
            border: Border.all(
              color: isLevel ? Colors.green : Colors.red,
              width: 2,
            ),
          ),
          child: Center(
            child: Text('X: ${angles.x}°, Y: ${angles.y}°'),
          ),
        );
      },
    );
  }
}
```

### 3. 分析结果展示

```dart
class AnalysisResult extends StatelessWidget {
  final AnalysisData data;

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        ColonyCountDisplay(count: data.count),
        ColonyDistributionChart(data: data.distribution),
        ExportButton(onPressed: () => exportResults(data)),
      ],
    );
  }
}
```

## 调试和测试

### 1. 调试工具
- Flutter DevTools
- VSCode调试器
- 性能分析工具

### 2. 测试类型
- 单元测试
- Widget测试
- 集成测试

### 3. 测试覆盖率
- 模块测试 > 80%
- UI测试 > 60%
- 关键功能 100%

## 发布流程

1. 版本号更新
2. 更新日志编写
3. 测试检查清单
4. 构建发布包
5. 应用商店提交

## 注意事项

1. 权限处理
   - 相机权限
   - 存储权限
   - 网络权限

2. 错误处理
   - 优雅降级
   - 用户提示
   - 错误日志

3. 性能监控
   - 启动时间
   - 内存使用
   - 帧率监控
