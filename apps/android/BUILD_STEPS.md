# Windows环境下的编译步骤

## 1. 环境准备

1. 检查JDK安装
```powershell
# 打开PowerShell或命令提示符
java -version
# 应显示JDK 17版本信息
```

2. 设置JAVA_HOME
```powershell
# 设置环境变量（根据实际安装路径调整）
$env:JAVA_HOME = "C:\Program Files\Java\jdk-17"
# 将Java添加到PATH
$env:Path += ";$env:JAVA_HOME\bin"
```

## 2. 获取Gradle Wrapper

1. 创建gradle目录
```powershell
cd apps/android
mkdir -p gradle/wrapper
```

2. 下载gradle-wrapper.jar（任选一种方式）:

A. 使用PowerShell下载:
```powershell
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/gradle/gradle/master/gradle/wrapper/gradle-wrapper.jar" -OutFile "gradle/wrapper/gradle-wrapper.jar"
```

B. 从Android Studio项目复制:
- 打开任意Android Studio项目
- 复制 `gradle/wrapper/gradle-wrapper.jar`
- 粘贴到当前项目的相同位置

## 3. 逐步编译

1. 清理项目
```powershell
.\gradlew.bat clean
```

2. 编译检查
```powershell
.\gradlew.bat compileDebug
```

3. 运行Lint检查
```powershell
.\gradlew.bat lintDebug
```

4. 运行单元测试
```powershell
.\gradlew.bat testDebug
```

5. 构建Debug版本
```powershell
.\gradlew.bat assembleDebug
```

## 4. 检查构建产物

1. 检查APK文件
```powershell
dir app\build\outputs\apk\debug\
```

2. 检查测试报告
```powershell
dir app\build\reports\tests\
```

3. 检查Lint报告
```powershell
dir app\build\reports\lint-results.html
```

## 5. 常见问题解决

### gradlew不可执行
```powershell
# 检查文件权限
Get-Acl gradlew.bat

# 如需要，添加执行权限
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
```

### 依赖下载问题
```powershell
# 强制更新依赖
.\gradlew.bat --refresh-dependencies
```

### 清理构建缓存
```powershell
# 删除构建缓存
Remove-Item -Recurse -Force .\app\build
Remove-Item -Recurse -Force .\build
Remove-Item -Recurse -Force .\gradle\*
```

## 6. 编译选项

### 跳过测试
```powershell
.\gradlew.bat assembleDebug -x test
```

### 并行构建
```powershell
.\gradlew.bat assembleDebug --parallel
```

### 显示详细日志
```powershell
.\gradlew.bat assembleDebug --info
```

## 7. 构建成功标准

1. 检查要点：
- Gradle构建成功
- 无编译错误
- 测试通过
- Lint检查通过
- APK文件生成

2. 输出位置：
- APK: `app/build/outputs/apk/debug/app-debug.apk`
- 测试报告: `app/build/reports/tests/`
- Lint报告: `app/build/reports/lint-results.html`

## 8. 后续步骤

1. 安装应用
```powershell
# 使用adb安装（需要连接设备）
adb install app\build\outputs\apk\debug\app-debug.apk
```

2. 查看日志
```powershell
adb logcat -s Colony
```

3. 运行UI测试
```powershell
.\gradlew.bat connectedAndroidTest
