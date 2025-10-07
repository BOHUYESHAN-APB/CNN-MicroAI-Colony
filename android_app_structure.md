# 安卓应用集成方案

## 应用功能概述

基于你的需求，安卓应用将实现以下功能：
- 📸 **拍照识别**：使用手机摄像头拍摄菌落图片
- 🔍 **菌落检测**：使用Faster R-CNN模型检测菌落位置
- 📊 **统计报告**：生成菌落数量、分布等统计信息
- 🖼️ **结果展示**：显示带框选标记的结果图片

## 技术架构

### 1. 模型选择
- **主模型**：Faster R-CNN ResNet50 (`checkpoint_epoch_31.pth`)
- **格式**：TensorFlow Lite (`.tflite`)
- **输入尺寸**：512×512像素
- **输出**：边界框坐标、置信度分数

### 2. 安卓应用架构
```
app/
├── src/main/java/com/colony/detector/
│   ├── MainActivity.kt          # 主界面
│   ├── CameraActivity.kt        # 拍照功能
│   ├── DetectionService.kt      # 模型推理服务
│   ├── ResultActivity.kt        # 结果显示
│   └── utils/
│       ├── ImageUtils.kt        # 图像处理工具
│       └── StatisticsUtils.kt   # 统计计算工具
├── res/
│   ├── layout/                  # 界面布局
│   ├── drawable/                # 图标资源
│   └── values/                  # 字符串资源
└── assets/
    └── colony_detector.tflite   # 模型文件
```

## 核心功能实现

### 1. 拍照功能 (CameraActivity.kt)
```kotlin
class CameraActivity : AppCompatActivity() {
    private lateinit var cameraExecutor: ExecutorService
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        
        // 请求相机权限
        if (allPermissionsGranted()) {
            startCamera()
        } else {
            ActivityCompat.requestPermissions(
                this, REQUIRED_PERMISSIONS, REQUEST_CODE_PERMISSIONS
            )
        }
        
        cameraExecutor = Executors.newSingleThreadExecutor()
    }
    
    private fun takePhoto() {
        // 拍照并保存图片
        val imageCapture = imageCapture ?: return
        
        val photoFile = File(
            externalMediaDirs.first(),
            "${System.currentTimeMillis()}.jpg"
        )
        
        val outputOptions = ImageCapture.OutputFileOptions.Builder(photoFile).build()
        
        imageCapture.takePicture(
            outputOptions, ContextCompat.getMainExecutor(this),
            object : ImageCapture.OnImageSavedCallback {
                override fun onError(exc: ImageCaptureException) {
                    Log.e(TAG, "拍照失败: ${exc.message}", exc)
                }
                
                override fun onImageSaved(output: ImageCapture.OutputFileResults) {
                    // 启动检测服务
                    val intent = Intent(this@CameraActivity, DetectionService::class.java)
                    intent.putExtra("image_path", photoFile.absolutePath)
                    startService(intent)
                }
            }
        )
    }
}
```

### 2. 模型推理服务 (DetectionService.kt)
```kotlin
class DetectionService : Service() {
    private lateinit var interpreter: Interpreter
    
    override fun onCreate() {
        super.onCreate()
        
        // 加载TensorFlow Lite模型
        val model = loadModelFile("colony_detector.tflite")
        val options = Interpreter.Options()
        interpreter = Interpreter(model, options)
    }
    
    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        val imagePath = intent?.getStringExtra("image_path") ?: return START_NOT_STICKY
        
        // 在后台线程处理检测
        Thread {
            try {
                val bitmap = BitmapFactory.decodeFile(imagePath)
                val processedBitmap = preprocessImage(bitmap)
                val detectionResults = detectColonies(processedBitmap)
                
                // 发送结果广播
                sendDetectionResults(detectionResults, imagePath)
            } catch (e: Exception) {
                Log.e(TAG, "检测失败: ${e.message}", e)
            }
        }.start()
        
        return START_NOT_STICKY
    }
    
    private fun detectColonies(bitmap: Bitmap): DetectionResult {
        // 准备输入数据
        val input = preprocessForModel(bitmap)
        
        // 运行推理
        val outputBoxes = Array(1) { FloatArray(100 * 4) } // 假设最多100个检测框
        val outputScores = Array(1) { FloatArray(100) }    // 置信度分数
        
        val inputs = arrayOf<Any>(input)
        val outputs = mutableMapOf<Int, Any>()
        outputs[0] = outputBoxes
        outputs[1] = outputScores
        
        interpreter.runForMultipleInputsOutputs(inputs, outputs)
        
        // 后处理结果
        return postprocessDetections(outputBoxes[0], outputScores[0], bitmap.width, bitmap.height)
    }
    
    private fun preprocessImage(bitmap: Bitmap): Bitmap {
        // 调整尺寸为512x512
        return Bitmap.createScaledBitmap(bitmap, 512, 512, true)
    }
}
```

### 3. 结果显示界面 (ResultActivity.kt)
```kotlin
class ResultActivity : AppCompatActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        
        val detectionResult = intent.getParcelableExtra<DetectionResult>("detection_result")
        val imagePath = intent.getStringExtra("image_path")
        
        // 显示原图
        val originalBitmap = BitmapFactory.decodeFile(imagePath)
        binding.originalImageView.setImageBitmap(originalBitmap)
        
        // 显示带检测框的结果图
        val resultBitmap = drawDetectionBoxes(originalBitmap, detectionResult.boxes)
        binding.resultImageView.setImageBitmap(resultBitmap)
        
        // 显示统计信息
        displayStatistics(detectionResult)
    }
    
    private fun displayStatistics(result: DetectionResult) {
        val colonyCount = result.boxes.size
        val avgConfidence = result.boxes.map { it.confidence }.average()
        
        binding.colonyCountText.text = "检测到菌落数量: $colonyCount"
        binding.confidenceText.text = "平均置信度: ${String.format("%.2f", avgConfidence)}"
        
        // 显示分布统计
        val distribution = calculateDistribution(result.boxes)
        binding.distributionText.text = "菌落分布: ${distribution}"
    }
    
    private fun drawDetectionBoxes(bitmap: Bitmap, boxes: List<BoundingBox>): Bitmap {
        val mutableBitmap = bitmap.copy(Bitmap.Config.ARGB_8888, true)
        val canvas = Canvas(mutableBitmap)
        val paint = Paint().apply {
            color = Color.RED
            style = Paint.Style.STROKE
            strokeWidth = 4f
        }
        
        boxes.forEach { box ->
            val rect = RectF(
                box.left * bitmap.width,
                box.top * bitmap.height,
                box.right * bitmap.width,
                box.bottom * bitmap.height
            )
            canvas.drawRect(rect, paint)
            
            // 绘制置信度文本
            canvas.drawText(
                "${String.format("%.2f", box.confidence)}",
                rect.left,
                rect.top - 10,
                Paint().apply {
                    color = Color.RED
                    textSize = 24f
                }
            )
        }
        
        return mutableBitmap
    }
}
```

## 数据模型定义

```kotlin
data class DetectionResult(
    val boxes: List<BoundingBox>,
    val processingTime: Long,
    val imageSize: Size
)

data class BoundingBox(
    val left: Float,
    val top: Float,
    val right: Float,
    val bottom: Float,
    val confidence: Float,
    val classId: Int = 0 // 0表示菌落类
)

data class ColonyStatistics(
    val totalCount: Int,
    val averageSize: Float,
    val density: Float, // 菌落密度
    val distribution: String // 分布描述
)
```

## 权限配置

在 `AndroidManifest.xml` 中添加所需权限：
```xml
<uses-permission android:name="android.permission.CAMERA" />
<uses-permission android:name="android.permission.WRITE_EXTERNAL_STORAGE" />
<uses-permission android:name="android.permission.READ_EXTERNAL_STORAGE" />

<application>
    <service android:name=".DetectionService" />
    
    <activity android:name=".MainActivity">
        <intent-filter>
            <action android:name="android.intent.action.MAIN" />
            <category android:name="android.intent.category.LAUNCHER" />
        </intent-filter>
    </activity>
    
    <activity android:name=".CameraActivity" />
    <activity android:name=".ResultActivity" />
</application>
```

## 依赖配置

在 `build.gradle` 中添加依赖：
```gradle
dependencies {
    implementation 'org.tensorflow:tensorflow-lite:2.13.0'
    implementation 'org.tensorflow:tensorflow-lite-gpu:2.13.0'
    implementation 'androidx.camera:camera-core:1.3.0'
    implementation 'androidx.camera:camera-camera2:1.3.0'
    implementation 'androidx.camera:camera-lifecycle:1.3.0'
    implementation 'androidx.camera:camera-view:1.3.0'
}
```

## 部署流程

### 1. 模型转换
```bash
python android_model_converter.py
```

### 2. 安卓项目设置
1. 在Android Studio中创建新项目
2. 将生成的 `.tflite` 文件复制到 `app/src/main/assets/` 目录
3. 按照上述架构创建Kotlin文件
4. 配置权限和依赖

### 3. 测试运行
1. 连接安卓设备或启动模拟器
2. 构建并安装应用
3. 测试拍照检测功能

## 性能优化建议

1. **模型优化**：
   - 使用TensorFlow Lite量化减小模型大小
   - 启用GPU加速推理
   - 使用多线程处理

2. **用户体验**：
   - 添加加载动画
   - 实现离线缓存
   - 优化图片处理流程

3. **功能扩展**：
   - 添加历史记录功能
   - 实现批量处理
   - 添加导出报告功能

这个方案完全满足你的需求：拍照识别、检测标记、统计报告和带框选的结果图片展示。