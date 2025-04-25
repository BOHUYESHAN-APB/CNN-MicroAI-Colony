// 在现有的DetectionUiState中添加以下字段
data class DetectionUiState(
    val isLoading: Boolean = false,
    val error: String? = null,
    val isRealTimeMode: Boolean = false,
    val isFlashEnabled: Boolean = false,
    val detectionResult: DetectionResult? = null,
    val realTimeDetections: List<DetectionResult> = emptyList(),
    val tiltAngle: Double = 0.0,  // 添加倾斜角度字段
    val isIdealAngle: Boolean = true  // 添加是否为理想角度字段
)

@HiltViewModel
class DetectionViewModel @Inject constructor(
    @ApplicationContext private val context: Context,
    private val repository: ColonyRepository,
    private val fileUtils: FileUtils,
    private val sensorUtils: SensorUtils  // 注入SensorUtils
) : ViewModel() {

    private val _uiState = MutableStateFlow(DetectionUiState())
    val uiState: StateFlow<DetectionUiState> = _uiState.asStateFlow()

    init {
        observeTiltAngle()  // 观察倾斜角度
    }

    /**
     * 观察倾斜角度
     */
    private fun observeTiltAngle() {
        viewModelScope.launch {
            sensorUtils.getTiltAngle()
                .collect { angle ->
                    _uiState.update { state ->
                        state.copy(
                            tiltAngle = angle,
                            isIdealAngle = sensorUtils.isIdealAngle(angle)
                        )
                    }
                }
        }
    }

    // ... 其他现有方法 ...

    /**
     * 拍照前检查角度
     */
    private fun checkAngleBeforeCapture(): Boolean {
        return uiState.value.isIdealAngle
    }

    /**
     * 修改拍照方法，添加角度检查
     */
    fun captureImage() {
        // 如果角度不理想，显示提示
        if (!checkAngleBeforeCapture()) {
            _uiState.update { state ->
                state.copy(error = "请调整设备角度至5°以内")
            }
            return
        }

        val imageCapture = imageCapture ?: return
        
        viewModelScope.launch {
            _uiState.update { it.copy(isLoading = true) }
            
            try {
                val photoFile = fileUtils.createImageFile(context)
                
                val outputOptions = ImageCapture.OutputFileOptions.Builder(photoFile).build()
                
                imageCapture.takePicture(
                    outputOptions,
                    cameraExecutor,
                    object : ImageCapture.OnImageSavedCallback {
                        override fun onImageSaved(output: ImageCapture.OutputFileResults) {
                            val uri = Uri.fromFile(photoFile)
                            analyzeImage(uri)
                        }
                        
                        override fun onError(exception: ImageCaptureException) {
                            _uiState.update {
                                it.copy(
                                    isLoading = false,
                                    error = exception.message
                                )
                            }
                        }
                    }
                )
            } catch (e: Exception) {
                _uiState.update {
                    it.copy(
                        isLoading = false,
                        error = e.message
                    )
                }
            }
        }
    }

    // ... 其他现有方法 ...

}
