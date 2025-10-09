# Checkpoint for Next Dev (快速接手指南)

日期: 2025-10-08

说明: 本文档为项目当前的检查点（简洁版），供另一个窗口或开发者快速理解当前状态、关键文件和最小构建/验证步骤。已刻意排除与 ADB 相关的操作内容。

---

## 一句话总结

Android 模块已添加启动时每次重建的内部日志（`session.log`），并修复了启动时因主题/资源导致的崩溃；项目可以在 Android Studio 中用 JDK 17 成功同步与构建（参见下方详细步骤）。

---

## 当前状态（要点）

- 已实现并集成：在应用级别 `LogManager`（写入 `files/logs/session.log` 并提供分享能力）。
- 已修复的运行时问题：因 Activity 未使用 AppCompat/Material 主题导致的 IllegalStateException（已通过新增/调整 theme/resources 解决）。
- 构建：在 Android Studio 中使用 Gradle wrapper / Gradle JDK 指向 JDK 17 可同步与构建成功（截图显示 Build SUCCESSFUL）。
- 排除了 ADB 细节（本检查点不包含设备安装或 adb 命令）。

---

## 关键环境（必须确认）

- 推荐 JDK: Microsoft Build of OpenJDK 17
  - 示例路径: `D:\Program Files\Microsoft\jdk-17.0.15.6-hotspot`
- Android Studio: 最新稳定版（支持 compileSdk 36、Gradle 9.x 系列）
- Gradle wrapper: 配置在 `android-app/gradle/wrapper/gradle-wrapper.properties`，distribution 为 `gradle-9.1.0-bin.zip`。
- 注意：请把 Android Studio 的 Gradle JVM (Gradle JDK) 指向上面的 JDK 路径以避免 Gradle/Java 兼容问题。

---

## 关键文件与说明（按路径）

- `android-app/app/src/main/java/org/microai/colony/LogManager.kt`
  - 目的: 应用每次启动时重新创建 `session.log`，提供写入、清除和导出（FileProvider）功能。

- `android-app/app/src/main/java/org/microai/colony/MainActivity.kt`
  - 变更: 初始化 `LogManager`、在 `onCreate` 增加 try/catch 捕获未处理异常并弹出堆栈复制对话框；绑定“导出日志/清空日志”按钮。

- `android-app/app/src/main/java/org/microai/colony/OnnxHelper.kt`
  - 变更: 更安全的 `init()`（返回 boolean），在初始化失败时记录日志并避免直接抛出未捕获异常。

- `android-app/app/src/main/res/values/styles.xml`
  - 目的: 定义 `Theme.MicroAIColony`（基于 Material/AppCompat），解决 AppCompat 主题异常。

- `android-app/app/src/main/res/values/colors.xml`
  - 目的: 主题颜色定义。

- `android-app/app/src/main/res/values/attrs.xml`
  - 目的: 声明缺失的 style attributes（例如 `colorBackground` 等），用于消除 aapt2 资源链接错误。

- `android-app/app/src/main/res/xml/file_paths.xml`
  - 变更: 添加 `<files-path name="logs" path="logs/" />`，以便通过 FileProvider 导出日志文件。

- `android-app/app/build.gradle`
  - 可能变更: 如需确保只打包 `arm64-v8a`，`defaultConfig` 中曾加入 `ndk { abiFilters 'arm64-v8a' }`（如你不需要此限制，请在 Android Studio 中审查并决定保留或删除）。

- `android-app/gradle/wrapper/gradle-wrapper.properties`
  - 说明: 使用 Gradle 9.1.0（wrapper 将下载对应 distribution）。

---

## 最小在 Android Studio 中构建步骤（不含 ADB）

1. 打开 Android Studio → File → Open，选择项目根目录（建议打开 `android-app` 文件夹或整个 repo）。
2. 设置 Gradle JDK: File → Settings（或 Preferences）→ Build, Execution, Deployment → Build Tools → Gradle → Gradle JVM，指向 `D:\Program Files\Microsoft\jdk-17.0.15.6-hotspot`。
3. 点击 "Sync Project with Gradle Files"（等待同步完成）。
4. Build → Clean Project，然后 Build → Rebuild Project。
5. 成功后：Build → Build Bundle(s) / APK(s) → Build APK(s)。

如果 Android Studio 在第一步提示下载 Gradle wrapper 的 distribution，允许下载并等待完成（会放在用户的 Gradle 缓存目录）。

---

## CLI 构建（PowerShell 最小命令，供参考）

在 `android-app` 目录中（示例）：

```powershell
$env:JAVA_HOME = 'D:\Program Files\Microsoft\jdk-17.0.15.6-hotspot'
$env:PATH = "$env:JAVA_HOME\bin;$env:PATH"
.\gradlew.bat clean assembleDebug
```

说明：若 `gradle/wrapper/gradle-wrapper.jar` 丢失，`gradlew.bat` 将无法运行。Android Studio 通常会在 Sync 时自动处理缺失 wrapper 的下载。

---

## 已知问题与解决办法（快速索引）

1. 问题：Activity 抛出 `You need to use a Theme.AppCompat theme (or descendant)`。
   - 原因：Activity 主题不是 AppCompat/Material 的子类。
   - 解决：已在 `styles.xml` 中添加 `Theme.MicroAIColony` 并在 `AndroidManifest.xml` 的 `<application>` 指定 `android:theme="@style/Theme.MicroAIColony"`。

2. 问题：资源链接失败（aapt2）“style attribute 'attr/colorBackground' not found”。
   - 原因：主题引用了未声明的 attributes。
   - 解决：已在 `res/values/attrs.xml` 声明所需 attrs 或把主题改为只使用已存在的属性。

3. 问题：打包/安装报 `INSTALL_FAILED_INVALID_ABI`（若遇到）。
   - 原因：APK 中仅包含 32-bit native 库，但设备为 64-bit。
   - 解决：在 `app/build.gradle` 中设置 `ndk.abiFilters 'arm64-v8a'` 或删除不必要的过滤以支持设备 ABI（请在 Android Studio 中审查此改动）。

---
 # Checkpoint for Next Dev (快速接手指南)

 日期: 2025-10-08

 说明: 本文档为项目当前的检查点（简洁版），供另一个窗口或开发者快速理解当前状态、关键文件和最小构建/验证步骤。已刻意排除与 ADB 相关的操作内容。

 ---

 ## 一句话总结

 Android 模块已添加启动时每次重建的内部日志（`session.log`），并修复了启动时因主题/资源导致的崩溃；项目可以在 Android Studio 中用 JDK 17 成功同步与构建（参见下方详细步骤）。

 ---

 ## 当前状态（要点）

 - 已实现并集成：在应用级别 `LogManager`（写入 `files/logs/session.log` 并提供分享能力）。
 - 已修复的运行时问题：因 Activity 未使用 AppCompat/Material 主题导致的 IllegalStateException（已通过新增/调整 theme/resources 解决）。
 - 构建：在 Android Studio 中使用 Gradle wrapper / Gradle JDK 指向 JDK 17 可同步与构建成功（截图显示 Build SUCCESSFUL）。
 - 排除了 ADB 细节（本检查点不包含设备安装或 adb 命令）。

 ---

 ## 关键环境（必须确认）

 - 推荐 JDK: Microsoft Build of OpenJDK 17
   - 示例路径: `D:\Program Files\Microsoft\jdk-17.0.15.6-hotspot`
 - Android Studio: 最新稳定版（支持 compileSdk 36、Gradle 9.x 系列）
 - Gradle wrapper: 配置在 `android-app/gradle/wrapper/gradle-wrapper.properties`，distribution 为 `gradle-9.1.0-bin.zip`。
 - 注意：请把 Android Studio 的 Gradle JVM (Gradle JDK) 指向上面的 JDK 路径以避免 Gradle/Java 兼容问题。

 ---

 ## 关键文件与说明（按路径）

 - `android-app/app/src/main/java/org/microai/colony/LogManager.kt`
   - 目的: 应用每次启动时重新创建 `session.log`，提供写入、清除和导出（FileProvider）功能。

 - `android-app/app/src/main/java/org/microai/colony/MainActivity.kt`
   - 变更: 初始化 `LogManager`、在 `onCreate` 增加 try/catch 捕获未处理异常并弹出堆栈复制对话框；绑定“导出日志/清空日志”按钮。

 - `android-app/app/src/main/java/org/microai/colony/OnnxHelper.kt`
   - 变更: 更安全的 `init()`（返回 boolean），在初始化失败时记录日志并避免直接抛出未捕获异常。

 - `android-app/app/src/main/res/values/styles.xml`
   - 目的: 定义 `Theme.MicroAIColony`（基于 Material/AppCompat），解决 AppCompat 主题异常。

 - `android-app/app/src/main/res/values/colors.xml`
   - 目的: 主题颜色定义。

 - `android-app/app/src/main/res/values/attrs.xml`
   - 目的: 声明缺失的 style attributes（例如 `colorBackground` 等），用于消除 aapt2 资源链接错误。

 - `android-app/app/src/main/res/xml/file_paths.xml`
   - 变更: 添加 `<files-path name="logs" path="logs/" />`，以便通过 FileProvider 导出日志文件。

 - `android-app/app/build.gradle`
   - 可能变更: 如需确保只打包 `arm64-v8a`，`defaultConfig` 中曾加入 `ndk { abiFilters 'arm64-v8a' }`（如你不需要此限制，请在 Android Studio 中审查并决定保留或删除）。

 - `android-app/gradle/wrapper/gradle-wrapper.properties`
   - 说明: 使用 Gradle 9.1.0（wrapper 将下载对应 distribution）。

 ---

 ## 最小在 Android Studio 中构建步骤（不含 ADB）

 1. 打开 Android Studio → File → Open，选择项目根目录（建议打开 `android-app` 文件夹或整个 repo）。
 2. 设置 Gradle JDK: File → Settings（或 Preferences）→ Build, Execution, Deployment → Build Tools → Gradle → Gradle JVM，指向 `D:\Program Files\Microsoft\jdk-17.0.15.6-hotspot`。
 3. 点击 "Sync Project with Gradle Files"（等待同步完成）。
 4. Build → Clean Project，然后 Build → Rebuild Project。
 5. 成功后：Build → Build Bundle(s) / APK(s) → Build APK(s)。

 如果 Android Studio 在第一步提示下载 Gradle wrapper 的 distribution，允许下载并等待完成（会放在用户的 Gradle 缓存目录）。

 ---

 ## CLI 构建（PowerShell 最小命令，供参考）

 在 `android-app` 目录中（示例）：

 ```powershell
 $env:JAVA_HOME = 'D:\Program Files\Microsoft\jdk-17.0.15.6-hotspot'
 $env:PATH = "$env:JAVA_HOME\bin;$env:PATH"
 .\gradlew.bat clean assembleDebug
 ```

 说明：若 `gradle/wrapper/gradle-wrapper.jar` 丢失，`gradlew.bat` 将无法运行。Android Studio 通常会在 Sync 时自动处理缺失 wrapper 的下载。

 ---

 ## 已知问题与解决办法（快速索引）

 1. 问题：Activity 抛出 `You need to use a Theme.AppCompat theme (or descendant)`。
    - 原因：Activity 主题不是 AppCompat/Material 的子类。
    - 解决：已在 `styles.xml` 中添加 `Theme.MicroAIColony` 并在 `AndroidManifest.xml` 的 `<application>` 指定 `android:theme="@style/Theme.MicroAIColony"`。

 2. 问题：资源链接失败（aapt2）“style attribute 'attr/colorBackground' not found”。
    - 原因：主题引用了未声明的 attributes。
    - 解决：已在 `res/values/attrs.xml` 声明所需 attrs 或把主题改为只使用已存在的属性。

 3. 问题：打包/安装报 `INSTALL_FAILED_INVALID_ABI`（若遇到）。
    - 原因：APK 中仅包含 32-bit native 库，但设备为 64-bit。
    - 解决：在 `app/build.gradle` 中设置 `ndk.abiFilters 'arm64-v8a'` 或删除不必要的过滤以支持设备 ABI（请在 Android Studio 中审查此改动）。

 ---

 ## 常见调试流程（无 ADB）

 - 如果 Build 失败：打开 Build → Build Output → 查看第一个错误并把错误文本复制到问题追踪。通常 aapt2 或 Kotlin/Java 编译错误会直接指向文件/行号。
 - 如果资源/主题相关错误：优先查看 `res/values/styles.xml` 与 `res/values/attrs.xml`，检查是否引用了不存在的属性或资源名拼写错误。
 - 如果 third-party native libs 导致打包异常：检查 `app/libs` 或 AAR 中 `jni` 内容，并在 `build.gradle` 中调整 `abiFilters`。

 ---

 ## 回退/撤销（如果需要）

 - 恢复所有本地未提交改动（谨慎，会丢失未提交变更）：

 # Checkpoint for Next Dev (快速接手指南)

 日期: 2025-10-08

 说明: 本文档为项目当前的检查点（简洁版），供另一个窗口或开发者快速理解当前状态、关键文件和最小构建/验证步骤（不包含 ADB 操作）。

 ---

 ## 一句话总结

 Android 模块已添加每次启动重建的内部日志（`session.log`），并修复了启动时的主题/资源崩溃；项目可在 Android Studio 使用 JDK 17 同步与构建成功。

 ---

 ## 当前状态（要点）

 - 已实现并集成：`LogManager`，写入 `files/logs/session.log` 并支持导出。
 - 已修复：AppCompat/Material 主题导致的启动崩溃（已添加/调整 theme/resources）。
 - 构建：在 Android Studio 使用 Gradle wrapper + Gradle JDK 指向 JDK 17 能成功构建（见最小构建步骤）。

 ---

 ## 关键环境（必须确认）

 - 推荐 JDK: Microsoft Build of OpenJDK 17
   - 示例路径: `D:\Program Files\Microsoft\jdk-17.0.15.6-hotspot`
 - Android Studio: 最新稳定版，支持 compileSdk 36 和 Gradle 9.x
 - Gradle wrapper: `android-app/gradle/wrapper/gradle-wrapper.properties` 指向 `gradle-9.1.0-bin.zip`

 请在 Android Studio 中把 Gradle JVM (Gradle JDK) 设置为上面的 JDK 路径。

 ---

 ## 关键文件（路径 + 用途）

 - `android-app/app/src/main/java/org/microai/colony/LogManager.kt`
   - 每次启动重建 `session.log`；写入/清空/导出功能（FileProvider）。

 - `android-app/app/src/main/java/org/microai/colony/MainActivity.kt`
   - 初始化 `LogManager`；在 `onCreate` 增加全局 try/catch；绑定导出/清空日志按钮。

 - `android-app/app/src/main/java/org/microai/colony/OnnxHelper.kt`
   - 更安全的 `init()`（返回 boolean）與错误日志记录。

 - `android-app/app/src/main/res/values/styles.xml`
   - 定义 `Theme.MicroAIColony`（基于 Material/AppCompat）。

 - `android-app/app/src/main/res/values/colors.xml`
   - 主题颜色定义。

 - `android-app/app/src/main/res/values/attrs.xml`
   - 声明缺失的 theme 属性（消除 aapt2 资源链接错误）。

 - `android-app/app/src/main/res/xml/file_paths.xml`
   - 包含 `<files-path name="logs" path="logs/" />`，用于 FileProvider 导出 logs。

 - `android-app/app/build.gradle`
   - 可能包含 `ndk { abiFilters 'arm64-v8a' }`（如需支持其它 ABIs，请在 Studio 中调整）。

 ---

 ## 最小在 Android Studio 中构建步骤（不含 ADB）

 1. 打开 Android Studio → File → Open，选择项目根目录（或 `android-app`）。
 2. Settings → Build Tools → Gradle → Gradle JVM，设置为 `D:\Program Files\Microsoft\jdk-17.0.15.6-hotspot`。
 3. 点击 "Sync Project with Gradle Files"。
 4. Build → Clean Project，然后 Build → Rebuild Project。
 5. Build → Build Bundle(s) / APK(s) → Build APK(s)。

 若提示下载 Gradle distribution，允许下载并等待完成。

 ---

 ## 已知问题與快速修复索引

 - 主题错误（"You need to use a Theme.AppCompat theme"）
   - 修复状态：已添加 `Theme.MicroAIColony` 并在 Manifest 指定。若仍报错，请检查 `styles.xml` 是否被正确加载。

 - 资源链接错误（aapt2: attr 不存在）
   - 修复状态：已在 `attrs.xml` 中声明缺失属性。若仍报错，请贴出 Build Output 中的第一条错误。

 - 安装时 ABI 错误（INSTALL_FAILED_INVALID_ABI）
   - 可能原因：APK 未包含设备 ABI。检查 `app/build.gradle` 中的 `ndk.abiFilters` 并按需移除或添加目标 ABI（在 Studio 中修改并 Rebuild）。

 ---

 ## 回退（若需撤销我之前的修改）

 - 恢复所有本地未提交改动（注意：会丢失未提交变更）：

 ```powershell
 git status
 git restore --source=HEAD --staged --worktree -- .
 ```

 - 回退单个文件示例：

 ```powershell
 git checkout -- android-app/app/src/main/java/org/microai/colony/LogManager.kt
 ```

 ---

 ## 给接手 AI 的短流程（最短路径）

 1. 在新窗口启动 Android Studio，设置 Gradle JDK（JDK17），Sync。若 Sync 失败，把第一条错误复制出来。  
 2. 若 Sync 成功，Rebuild 并生成 APK；若失败，把 Build Output 第一条错误的前 10 行贴上来。  
 3. 检查 `LogManager.kt`，确认日志文件写入路径为 `context.filesDir/logs/session.log`。  
 4. 如需修改 ABI 或主题，直接在 Android Studio 中修改 `app/build.gradle` 或 `res/values/styles.xml` 并 Rebuild。

 ---

 ## 联系点与备注

 - 日志文件位置（运行时，应用私有）: `context.filesDir/logs/session.log`（可通过应用 UI 导出）。
 - 重点：UI 中已加入“导出日志”和“清空日志”按钮，方便在实际设备上快速导出诊断信息（但本检查点不包含 ADB 操作）。

 ---

 如果你需要，我可以把此文件再生成一个更短的 `QUICK_START.md`，只包含 5 条要做步骤（供新窗口的 AI 直接运行）。要我生成吗？
