# Android应用构建说明

## Windows环境设置

1. 安装必要软件
- 安装 [Android Studio](https://developer.android.com/studio)
- 安装 [Java JDK 17](https://adoptium.net/)
- 配置环境变量：
  * JAVA_HOME: `C:\Program Files\Java\jdk-17`
  * 添加 `%JAVA_HOME%\bin` 到 PATH

2. 使用Android Studio打开项目
- 打开 `apps/android` 目录
- 等待Gradle同步完成
- 如果遇到gradle-wrapper.jar缺失，可以：
  * 使用Android Studio自动修复
  * 或从其他Android项目复制gradle/wrapper文件夹
  * 或从[Gradle官网](https://gradle.org/releases/)下载

3. 命令行构建（可选）
```cmd
cd apps/android
.\gradlew.bat clean
.\gradlew.bat build
```

## Unix环境设置

1. 设置权限
```bash
chmod +x gradlew
```

2. 构建项目
```bash
./gradlew clean build
```

## 项目配置

- minSdk: 24
- targetSdk: 34
- compileSdk: 34
- Kotlin: 1.9.0
- Compose: 1.5.1
- Gradle: 8.2.0

## 构建变体

1. Debug版本
```cmd
# Windows
.\gradlew.bat assembleDebug

# Unix
./gradlew assembleDebug
```

2. Release版本
```cmd
# Windows
.\gradlew.bat assembleRelease

# Unix
./gradlew assembleRelease
```

## 运行测试

1. 单元测试
```cmd
# Windows
.\gradlew.bat test

# Unix
./gradlew test
```

2. UI测试（需要连接设备或模拟器）
```cmd
# Windows
.\gradlew.bat connectedAndroidTest

# Unix
./gradlew connectedAndroidTest
```

## 依赖说明

主要依赖包括：
- Jetpack Compose
- CameraX
- Room Database
- Retrofit
- Hilt
- DataStore

## 问题排查

如果遇到构建问题，请参考：
- [troubleshooting.md](docs/troubleshooting.md)

## 注意事项

1. 开发环境要求
- Android Studio Hedgehog | 2023.1.1 或更高版本
- JDK 17
- Windows 10/11 或 macOS/Linux

2. 设备要求
- Android 7.0 (API 24) 或更高版本
- 支持陀螺仪传感器
- 相机功能
- 足够的存储空间

3. 权限要求
- 相机权限
- 存储权限
- 传感器权限

## 帮助和支持

- [项目Wiki](https://github.com/yourusername/colony/wiki)
- [问题报告](https://github.com/yourusername/colony/issues)
- [开发文档](docs/development/)
