// 在现有的DetectionScreen中更新内容

@OptIn(ExperimentalPermissionsApi::class)
@Composable
fun DetectionScreen(
    modifier: Modifier = Modifier,
    viewModel: DetectionViewModel = hiltViewModel(),
    onNavigateBack: () -> Unit,
    onDetectionComplete: (String) -> Unit
) {
    val context = LocalContext.current
    val lifecycleOwner = LocalLifecycleOwner.current
    val cameraPermissionState = rememberPermissionState(Manifest.permission.CAMERA)
    val sensorPermissionState = rememberPermissionState(Manifest.permission.HIGH_SAMPLING_RATE_SENSORS)
    
    val uiState by viewModel.uiState.collectAsState()
    
    LaunchedEffect(key1 = true) {
        cameraPermissionState.launchPermissionRequest()
        sensorPermissionState.launchPermissionRequest()
    }
    
    Scaffold(
        topBar = {
            CenterAlignedTopAppBar(
                title = { Text(stringResource(R.string.detection_title)) },
                navigationIcon = {
                    IconButton(onClick = onNavigateBack) {
                        Icon(Icons.Filled.ArrowBack, contentDescription = null)
                    }
                }
            )
        }
    ) { padding ->
        Box(
            modifier = modifier
                .fillMaxSize()
                .padding(padding)
        ) {
            when {
                !cameraPermissionState.hasPermission || !sensorPermissionState.hasPermission -> {
                    MultiplePermissionsRequest(
                        permissions = listOf(
                            PermissionRequest(
                                Manifest.permission.CAMERA,
                                stringResource(R.string.permission_camera_title),
                                stringResource(R.string.permission_camera_description)
                            ),
                            PermissionRequest(
                                Manifest.permission.HIGH_SAMPLING_RATE_SENSORS,
                                "需要传感器权限",
                                "需要传感器权限来监测设备角度"
                            )
                        ),
                        onRequestPermissions = {
                            cameraPermissionState.launchPermissionRequest()
                            sensorPermissionState.launchPermissionRequest()
                        }
                    )
                }
                uiState.isLoading -> {
                    LoadingScreen()
                }
                uiState.error != null -> {
                    ErrorScreen(
                        message = uiState.error!!,
                        onRetry = { viewModel.retry() }
                    )
                }
                else -> {
                    DetectionContent(
                        uiState = uiState,
                        onCaptureImage = { viewModel.captureImage() },
                        onSwitchCamera = { viewModel.switchCamera() },
                        onToggleFlash = { viewModel.toggleFlash() }
                    )
                    
                    // 添加角度指示器
                    TiltAngleIndicator(
                        angle = uiState.tiltAngle,
                        modifier = Modifier
                            .align(Alignment.TopCenter)
                            .padding(top = 16.dp)
                    )
                    
                    // 添加拍摄提示
                    ShootingHint(
                        angle = uiState.tiltAngle,
                        modifier = Modifier
                            .align(Alignment.TopCenter)
                            .padding(top = 120.dp)
                    )
                    
                    // 检测结果覆盖层
                    if (uiState.detectionResult != null) {
                        DetectionOverlay(
                            result = uiState.detectionResult!!,
                            onClose = { viewModel.clearResult() }
                        )
                    }
                }
            }
            
            // 控制按钮
            CameraControls(
                isFlashEnabled = uiState.isFlashEnabled,
                onCaptureClick = { 
                    if (uiState.isIdealAngle) {
                        viewModel.captureImage()
                    }
                },
                onSwitchCamera = { viewModel.switchCamera() },
                onToggleFlash = { viewModel.toggleFlash() },
                modifier = Modifier
                    .align(Alignment.BottomCenter)
                    .padding(bottom = 32.dp)
            )
        }
    }
}

// ... 其他现有的组件代码 ...
