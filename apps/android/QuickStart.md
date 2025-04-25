# 快速开始指南

## 使用Android Studio打开项目

1. 启动Android Studio
2. 选择 "Open an existing project"
3. 导航到项目的 `apps/android` 目录
4. 等待项目同步完成

## 首次构建步骤

1. 确保已安装JDK 17
   - Android Studio可以帮助下载和安装所需的JDK
   - 或从[Adoptium](https://adoptium.net/)手动下载安装

2. 同步Gradle文件
   - 点击工具栏中的"Sync Project with Gradle Files"按钮
   - 或在build.gradle.kts文件打开时点击"Sync Now"

3. 等待依赖下载
   - Android Studio会自动下载所需的依赖
   - 包括Gradle Wrapper和其他库文件

4. 构建项目
   - 点击工具栏的"Make Project"按钮
   - 或使用快捷键Ctrl+F9 (Windows) / Cmd+F9 (Mac)

## 运行应用

1. 连接Android设备
   - 通过USB连接真实设备
   - 或使用Android Studio的虚拟设备管理器创建模拟器

2. 运行应用
   - 点击工具栏的"Run"按钮
   - 或使用快捷键Shift+F10 (Windows) / Control+R (Mac)

## 常见问题解决

1. Gradle同步失败
   - File -> Invalidate Caches / Restart
   - 重新打开项目

2. 缺少SDK组件
   - Tools -> SDK Manager
   - 安装缺失的SDK平台和工具

3. 权限问题
   - 确保设备已启用开发者选项
   - 允许USB调试
   - 允许应用所需权限

## 开发提示

1. 实时预览
   - 使用Compose Preview查看UI组件
   - 在PreviewParameter中模拟不同角度数据

2. 调试传感器
   - 使用Android Studio的布局检查器
   - 观察传感器数据流
   - 在模拟器中模拟传感器数据

3. 性能监控
   - 使用Android Studio的CPU Profiler
   - 监控内存使用
   - 检查帧率表现

## 下一步

1. 查看详细文档
   - [README.md](README.md) - 完整的项目说明
   - [troubleshooting.md](docs/troubleshooting.md) - 问题排查指南

2. 探索代码
   - 查看SensorUtils了解角度检测实现
   - 研究TiltAngleIndicator的UI实现
   - 了解DetectionViewModel的状态管理

3. 运行测试
   - 执行单元测试验证功能
   - 运行UI测试检查界面

## 联系支持

如果遇到问题：
1. 查看项目[Wiki](https://github.com/yourusername/colony/wiki)
2. 提交[Issue](https://github.com/yourusername/colony/issues)
3. 参考[故障排除指南](docs/troubleshooting.md)
