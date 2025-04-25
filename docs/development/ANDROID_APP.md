# Android应用开发文档

## 1. 项目概述

菌落检测分析Android应用是一个使用现代Android开发技术栈构建的移动应用程序。该应用提供菌落实时检测、图像分析、数据管理等功能。

## 2. 技术架构

### 2.1 核心技术
- Kotlin + Coroutines + Flow
- Jetpack Compose (UI框架)
- Hilt (依赖注入)
- Room (本地数据库)
- Retrofit (网络请求)
- CameraX (相机功能)
- DataStore (数据存储)

### 2.2 架构模式
采用MVVM架构模式：
- Model: 数据层，包括Repository和数据源
- ViewModel: 业务逻辑层，管理UI状态
- View: 使用Jetpack Compose构建的声明式UI

### 2.3 项目结构
```
app/
├── data/           # 数据层
│   ├── api/       # 网络API
│   ├── db/        # 本地数据库
│   ├── model/     # 数据模型
│   ├── repository/ # 数据仓库
│   └── datastore/ # 设置存储 
├── di/            # 依赖注入
├── ui/            # 界面层
│   ├── components/ # 共用组件
│   ├── screens/   # 页面
│   ├── theme/     # 主题
│   └── navigation/ # 导航
└── utils/         # 工具类
```

## 3. 功能模块

### 3.1 主页面(HomeScreen)
- 实时检测入口
- 拍照检测入口
- 最近记录展示

### 3.2 检测功能(DetectionScreen)
- 实时视频流检测
- 拍照检测
- 结果预览和保存

### 3.3 历史记录(HistoryScreen)
- 检测记录列表
- 时间筛选
- 记录详情查看
- 删除功能

### 3.4 分析报告(AnalysisScreen)
- 数据统计
- 趋势图表
- LLM分析结果
- 导出功能

### 3.5 设置功能(SettingsScreen)
- 主题切换
- 语言设置
- 存储管理
- 系统信息

## 4. 数据管理

### 4.1 本地存储
- Room数据库存储检测记录
- DataStore保存应用设置
- 文件系统存储图片

### 4.2 网络通信
- RESTful API请求
- WebSocket实时通信
- 文件上传下载

### 4.3 数据同步
- 本地缓存策略
- 增量同步
- 错误重试机制

## 5. 性能优化

### 5.1 内存管理
- 图片内存复用
- 生命周期感知
- 内存泄漏防护

### 5.2 性能监控
- 启动速度优化
- 页面加载优化
- 内存使用监控

### 5.3 电池优化
- 后台任务管理
- 网络请求优化
- 传感器使用优化

## 6. 开发指南

### 6.1 环境配置
```gradle
// 最低支持版本
minSdk = 24
// 目标版本
targetSdk = 34
// Kotlin版本
kotlinVersion = "1.9.0"
// Compose版本
composeVersion = "1.5.1"
```

### 6.2 构建配置
```gradle
plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
    id("com.google.dagger.hilt.android")
    id("kotlin-kapt")
}
```

### 6.3 关键依赖
```gradle
dependencies {
    // Compose
    implementation("androidx.compose.ui:ui")
    implementation("androidx.compose.material3:material3")
    
    // 相机
    implementation("androidx.camera:camera-camera2:1.3.1")
    implementation("androidx.camera:camera-lifecycle:1.3.1")
    implementation("androidx.camera:camera-view:1.3.1")
    
    // 网络
    implementation("com.squareup.retrofit2:retrofit:2.9.0")
    implementation("com.squareup.okhttp3:okhttp:4.11.0")
    
    // 依赖注入
    implementation("com.google.dagger:hilt-android:2.48")
    
    // 数据库
    implementation("androidx.room:room-runtime:2.6.1")
    implementation("androidx.room:room-ktx:2.6.1")
}
```

## 7. 注意事项

### 7.1 权限处理
- 相机权限
- 存储权限
- 网络权限

### 7.2 兼容性
- Android版本适配
- 屏幕尺寸适配
- 系统特性适配

### 7.3 安全性
- 数据加密
- 网络安全
- 隐私保护

## 8. 后续计划

### 8.1 功能增强
- 离线模型支持
- 批量处理优化
- 数据分析增强

### 8.2 性能优化
- 启动速度优化
- 内存使用优化
- 电池使用优化

### 8.3 用户体验
- UI/UX改进
- 操作流程优化
- 错误处理增强
