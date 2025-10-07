
// MainActivity.kt - 主界面
class MainActivity : AppCompatActivity() {
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        
        // 设置拍照按钮
        findViewById<Button>(R.id.camera_button).setOnClickListener {
            val intent = Intent(this, CameraActivity::class.java)
            startActivity(intent)
        }
    }
}

// CameraActivity.kt - 拍照功能
class CameraActivity : AppCompatActivity() {
    
    private fun takePhoto() {
        // 拍照逻辑
        val photoFile = createImageFile()
        
        // 启动检测
        val intent = Intent(this, DetectionActivity::class.java)
        intent.putExtra("image_path", photoFile.absolutePath)
        startActivity(intent)
    }
}

// DetectionActivity.kt - 检测功能
class DetectionActivity : AppCompatActivity() {
    
    private lateinit var session: OrtSession
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        
        // 加载ONNX模型
        val modelFile = "colony_detector_android.onnx"
        session = OrtSession.createInstance(this, modelFile)
        
        // 处理图片
        val imagePath = intent.getStringExtra("image_path")
        processImage(imagePath)
    }
    
    private fun processImage(imagePath: String?) {
        // 图片预处理
        val bitmap = BitmapFactory.decodeFile(imagePath)
        val processedBitmap = preprocessImage(bitmap)
        
        // 运行模型推理
        val input = bitmapToFloatArray(processedBitmap)
        val results = session.run(input)
        
        // 显示结果
        showResults(results, bitmap)
    }
}
