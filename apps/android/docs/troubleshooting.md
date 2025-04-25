# 编译和运行问题排查指南

## 1. 环境问题

### 1.1 JDK相关
- **错误**: JAVA_HOME is not set
- **解决**: 
  ```bash
  # Windows
  set JAVA_HOME=C:\Program Files\Java\jdk-17
  
  # Unix
  export JAVA_HOME=/usr/lib/jvm/java-17-openjdk
  ```

### 1.2 Gradle相关
- **错误**: gradlew不可执行
- **解决**:
  ```bash
  chmod +x gradlew
  ```

- **错误**: Gradle同步失败
- **解决**:
  1. 删除.gradle文件夹
  2. 重新同步项目
  3. 确保网络连接正常

## 2. 依赖问题

### 2.1 版本冲突
- **错误**: Duplicate class found
- **解决**:
  ```kotlin
  // 在app/build.gradle.kts中添加
  configurations.all {
      resolutionStrategy {
          force("androidx.core:core-ktx:1.12.0")
          // 添加其他强制版本
      }
  }
  ```

### 2.2 缺失依赖
- **错误**: Could not find com.google.dagger:hilt-android
- **解决**:
  1. 检查build.gradle中的仓库配置
  2. 检查网络连接
  3. 尝试清理项目并重新构建

## 3. 资源问题

### 3.1 资源冲突
- **错误**: Duplicate resources
- **解决**:
  1. 检查res目录下是否有重名资源
  2. 检查依赖库是否包含相同资源
  3. 使用资源覆盖规则

### 3.2 资源引用
- **错误**: Resource not found
- **解决**:
  1. 确保资源文件名正确
  2. 检查资源目录结构
  3. 执行Clean项目

## 4. 权限问题

### 4.1 运行时权限
- **错误**: Permission denied
- **解决**:
  1. 检查AndroidManifest.xml权限声明
  2. 确保正确实现权限请求逻辑
  3. 测试设备的权限设置

### 4.2 存储权限
- **错误**: Failed to save image
- **解决**:
  1. 检查存储权限声明
  2. 验证文件路径配置
  3. 检查存储空间是否充足

## 5. 传感器问题

### 5.1 陀螺仪访问
- **错误**: Sensor unavailable
- **解决**:
  1. 检查设备是否支持陀螺仪
  2. 验证传感器权限
  3. 确保传感器服务正常运行

### 5.2 相机访问
- **错误**: Camera device error
- **解决**:
  1. 检查相机权限
  2. 验证相机硬件状态
  3. 检查相机配置参数

## 6. 性能问题

### 6.1 内存溢出
- **错误**: OutOfMemoryError
- **解决**:
  1. 检查图片加载和缓存策略
  2. 优化内存使用
  3. 增加Java堆大小

### 6.2 ANR问题
- **错误**: Application Not Responding
- **解决**:
  1. 优化主线程操作
  2. 使用协程处理耗时任务
  3. 检查后台服务

## 7. 构建问题

### 7.1 签名配置
- **错误**: Signing configuration not found
- **解决**:
  1. 检查签名配置
  2. 验证密钥库文件
  3. 确认签名信息正确

### 7.2 ProGuard配置
- **错误**: ProGuard混淆错误
- **解决**:
  1. 检查混淆规则
  2. 添加Keep注解
  3. 更新ProGuard配置

## 8. 测试问题

### 8.1 单元测试
- **错误**: Test failure
- **解决**:
  1. 检查测试环境配置
  2. 验证测试数据
  3. 更新测试用例

### 8.2 UI测试
- **错误**: Espresso test failure
- **解决**:
  1. 检查测试设备设置
  2. 验证UI元素可见性
  3. 处理异步操作

## 9. 其他问题

### 9.1 编码问题
- **错误**: Character encoding
- **解决**:
  1. 设置源文件编码
  2. 检查资源文件编码
  3. 统一项目编码设置

### 9.2 版本兼容
- **错误**: API compatibility
- **解决**:
  1. 检查API级别设置
  2. 添加版本兼容代码
  3. 使用androidx库

## 10. 帮助资源

- [Android开发者文档](https://developer.android.com/)
- [Kotlin官方文档](https://kotlinlang.org/docs/home.html)
- [Jetpack Compose文档](https://developer.android.com/jetpack/compose)
- [GitHub Issues](https://github.com/yourusername/colony/issues)
- [项目Wiki](https://github.com/yourusername/colony/wiki)
