package com.bohuyshan.microai.colony

import android.Manifest
import android.app.AlertDialog
import android.content.ClipData
import android.content.ClipboardManager
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.Matrix
import android.graphics.RectF
import android.net.Uri
import android.os.Bundle
import android.os.SystemClock
import android.view.Surface
import android.view.View
import android.widget.ImageButton
import android.widget.ImageView
import android.widget.ProgressBar
import android.widget.SeekBar
import android.widget.TextView
import android.widget.Toast
import androidx.activity.result.ActivityResultLauncher
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import androidx.camera.core.AspectRatio
import androidx.camera.core.CameraSelector
import androidx.camera.core.ImageCapture
import androidx.camera.core.ImageCaptureException
import androidx.camera.core.Preview
import androidx.camera.lifecycle.ProcessCameraProvider
import androidx.camera.view.PreviewView
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import androidx.core.content.FileProvider
import com.google.android.material.button.MaterialButtonToggleGroup
import com.google.android.material.floatingactionbutton.FloatingActionButton
import com.google.android.material.progressindicator.CircularProgressIndicator
import com.google.android.material.bottomsheet.BottomSheetBehavior
import com.google.android.material.card.MaterialCardView
import androidx.exifinterface.media.ExifInterface
import com.bohuyshan.microai.colony.ui.SquareOverlayView
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.io.File
import java.io.FileOutputStream
import java.util.concurrent.ExecutorService
import java.util.concurrent.Executors

class MainActivity : AppCompatActivity() {
    private val scope = CoroutineScope(Dispatchers.Main)
    private lateinit var previewView: PreviewView
    private lateinit var overlayView: SquareOverlayView
    private lateinit var takeBtn: FloatingActionButton
    private lateinit var lastPathTv: TextView
    private lateinit var detectionStatsTv: TextView
    private lateinit var lastResultPreview: ImageView
    private lateinit var tvThresholdLabel: TextView
    private lateinit var seekThreshold: SeekBar
    private lateinit var tvNmsLabel: TextView
    private lateinit var seekNms: SeekBar
    private lateinit var progInfer: ProgressBar
    private lateinit var progressCapture: CircularProgressIndicator
    private lateinit var timingTv: TextView
    private lateinit var engineStatusTv: TextView
    private lateinit var settingsBtn: ImageButton
    private lateinit var openGalleryBtn: ImageButton
    private lateinit var manageProjectBtn: ImageButton
    private lateinit var panelTitleTv: TextView
    private lateinit var sheetToggleBtn: ImageButton
    private lateinit var bottomSheetBehavior: BottomSheetBehavior<MaterialCardView>
    private lateinit var presetGroup: MaterialButtonToggleGroup
    private lateinit var galleryLauncher: ActivityResultLauncher<String>
    private var currentProject: String = ""
    private var totalInferenceMs: Long = 0
    private var inferenceCount: Int = 0
    private var lastResultPath: String? = null
    // single capture mode flags
    private var singleShotDone: Boolean = false
    private var captureLaunched: Boolean = false
    private var imageCapture: ImageCapture? = null
    private var cameraProvider: ProcessCameraProvider? = null
    private val cameraExecutor: ExecutorService = Executors.newSingleThreadExecutor()
    private var cameraInitialized: Boolean = false
    private val cameraPermissionRequestCode = 101
    private var isOnnxReady: Boolean = false
    private var updatingFromPreset: Boolean = false

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        try {
            LogManager.init(this)
            LogManager.log("MainActivity created")
            setContentView(R.layout.activity_main)

            previewView = findViewById(R.id.camera_preview)
            overlayView = findViewById(R.id.square_overlay)
            takeBtn = findViewById(R.id.btn_take)
            lastPathTv = findViewById(R.id.tv_last_path)
            detectionStatsTv = findViewById(R.id.tv_detection_stats)
            lastResultPreview = findViewById(R.id.img_last_result)
            tvThresholdLabel = findViewById(R.id.tv_threshold_label)
            seekThreshold = findViewById(R.id.seek_threshold)
            tvNmsLabel = findViewById(R.id.tv_nms_label)
            seekNms = findViewById(R.id.seek_nms)
            progInfer = findViewById(R.id.prog_infer)
            timingTv = findViewById(R.id.tv_timing)
            progressCapture = findViewById(R.id.progress_capture)
            engineStatusTv = findViewById(R.id.tv_engine_status)
            settingsBtn = findViewById(R.id.btn_settings)
            openGalleryBtn = findViewById(R.id.btn_open_gallery)
            manageProjectBtn = findViewById(R.id.btn_manage_project)
            panelTitleTv = findViewById(R.id.tv_panel_title)
            sheetToggleBtn = findViewById(R.id.btn_sheet_toggle)
            val bottomSheetCard = findViewById<MaterialCardView>(R.id.bottom_sheet)
            bottomSheetBehavior = BottomSheetBehavior.from(bottomSheetCard)
            bottomSheetBehavior.peekHeight = resources.getDimensionPixelSize(R.dimen.bottom_sheet_peek_height)
            bottomSheetBehavior.state = BottomSheetBehavior.STATE_COLLAPSED
            updateSheetToggleIcon(BottomSheetBehavior.STATE_COLLAPSED)
            bottomSheetBehavior.addBottomSheetCallback(object : BottomSheetBehavior.BottomSheetCallback() {
                override fun onStateChanged(bottomSheet: View, newState: Int) {
                    updateSheetToggleIcon(newState)
                }

                override fun onSlide(bottomSheet: View, slideOffset: Float) {}
            })
            sheetToggleBtn.setOnClickListener { toggleBottomSheet() }
            presetGroup = findViewById(R.id.group_detection_preset)
            setupPresetButtons()
            currentProject = ProjectRepository.getCurrentProject(this)
            panelTitleTv.text = getString(R.string.main_panel_title, currentProject, "--")
            detectionStatsTv.text = getString(R.string.main_detection_result_placeholder)
            lastResultPreview.visibility = View.GONE
            lastResultPreview.setOnClickListener {
                lastResultPath?.let { path ->
                    val intent = Intent(this, ImagePreviewActivity::class.java)
                    intent.putExtra(ImagePreviewActivity.EXTRA_PATH, path)
                    startActivity(intent)
                }
            }

            takeBtn.isEnabled = false
            takeBtn.alpha = 0.4f

            galleryLauncher = registerForActivityResult(ActivityResultContracts.GetContent()) { uri ->
                if (uri != null) {
                    handleImportedImage(uri)
                }
            }

            isOnnxReady = OnnxHelper.init(this)
            if (isOnnxReady) {
                LogManager.log("ONNX helper initialized successfully")
            } else {
                LogManager.log("ONNX helper failed to initialize; disabling capture")
                Toast.makeText(this, getString(R.string.main_init_failed_message), Toast.LENGTH_LONG).show()
                takeBtn.isEnabled = false
                takeBtn.alpha = 0.4f
            }
            updateCaptureButtonState()
            updateEngineStatus()
            if (panelTitleTv.text.isNullOrEmpty()) {
                panelTitleTv.text = "MicroAI Colony"
            }

            takeBtn.setOnClickListener { capturePhoto() }
            settingsBtn.setOnClickListener { openSettings() }
            openGalleryBtn.setOnClickListener { galleryLauncher.launch("image/*") }
            manageProjectBtn.setOnClickListener { openProjectManager() }
            seekThreshold.setOnSeekBarChangeListener(object: SeekBar.OnSeekBarChangeListener{
                override fun onProgressChanged(seekBar: SeekBar?, progress: Int, fromUser: Boolean) {
                    val v = progress / 100.0f
                    tvThresholdLabel.text = String.format("Score threshold: %.2f", v)
                    if (fromUser && ::presetGroup.isInitialized && !updatingFromPreset) {
                        presetGroup.clearChecked()
                    }
                }
                override fun onStartTrackingTouch(seekBar: SeekBar?) {}
                override fun onStopTrackingTouch(seekBar: SeekBar?) {}
            })
            seekNms.setOnSeekBarChangeListener(object: SeekBar.OnSeekBarChangeListener{
                override fun onProgressChanged(seekBar: SeekBar?, progress: Int, fromUser: Boolean) {
                    val v = progress / 100.0f
                    tvNmsLabel.text = String.format("NMS IoU: %.2f", v)
                    if (fromUser && ::presetGroup.isInitialized && !updatingFromPreset) {
                        presetGroup.clearChecked()
                    }
                }
                override fun onStartTrackingTouch(seekBar: SeekBar?) {}
                override fun onStopTrackingTouch(seekBar: SeekBar?) {}
            })
            refreshGallery()

            ensureCameraPermissionAndStart()
            updateCaptureButtonState()
        } catch (t: Throwable) {
            LogManager.logError("Fatal error during MainActivity.onCreate", t)
            showFatalErrorDialog(t)
        }
    }

    private fun refreshGallery() {
        val dir = ensureAlbumDir()
        val allImages = dir.listFiles { f -> f.extension.lowercase() in listOf("jpg", "jpeg", "png") }
            ?.sortedByDescending { it.lastModified() }
            ?: emptyList()
        val primaryImages = allImages.filter { it.name.startsWith("img_") || it.name.startsWith("import_") }
    panelTitleTv.text = getString(R.string.main_panel_title, currentProject, primaryImages.size.toString())
        LogManager.log("Gallery refreshed, count=${primaryImages.size}")
    }

    private fun ensureAlbumDir(): File {
        if (currentProject.isBlank()) {
            currentProject = ProjectRepository.getCurrentProject(this)
        }
        return ProjectRepository.getProjectAlbumDir(this, currentProject)
    }

    private fun openSettings() {
        startActivity(Intent(this, SettingsActivity::class.java))
    }

    private fun openProjectManager() {
        startActivity(Intent(this, ProjectManagerActivity::class.java))
    }

    private fun updateEngineStatus() {
        if (!::engineStatusTv.isInitialized) return
        if (!isOnnxReady) {
            engineStatusTv.text = getString(R.string.main_engine_not_ready)
            return
        }
        val engine = InferencePreferences.getPreferredEngine(this)
        val label = when (engine) {
            InferencePreferences.Engine.GPU -> "GPU"
            InferencePreferences.Engine.NPU -> "NPU"
            InferencePreferences.Engine.CPU -> "CPU"
        }
        engineStatusTv.text = "Engine: $label"
    }

    private fun ensureCameraPermissionAndStart() {
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.CAMERA) == PackageManager.PERMISSION_GRANTED) {
            LogManager.log("Camera permission already granted")
            startCamera()
        } else {
            LogManager.log("Camera permission not granted; requesting")
            ActivityCompat.requestPermissions(this, arrayOf(Manifest.permission.CAMERA), cameraPermissionRequestCode)
        }
        updateCaptureButtonState()
    }

    private fun updateCaptureButtonState() {
        val enabled = cameraInitialized && isOnnxReady && !singleShotDone && !captureLaunched
        takeBtn.isEnabled = enabled
        takeBtn.alpha = if (enabled) 1f else 0.4f
    }

    override fun onResume() {
        super.onResume()
        val latest = ProjectRepository.getCurrentProject(this)
        if (latest != currentProject) {
            currentProject = latest
        }
        refreshGallery()
        updateEngineStatus()
    }

    override fun onRequestPermissionsResult(requestCode: Int, permissions: Array<out String>, grantResults: IntArray) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        if (requestCode == cameraPermissionRequestCode) {
            if (grantResults.isNotEmpty() && grantResults[0] == PackageManager.PERMISSION_GRANTED) {
                LogManager.log("Camera permission granted via request")
                startCamera()
            } else {
                Toast.makeText(this, getString(R.string.main_camera_permission_required), Toast.LENGTH_LONG).show()
                LogManager.log("Camera permission denied")
                updateCaptureButtonState()
            }
        }
    }

    private fun startCamera() {
        if (cameraInitialized) {
            LogManager.log("Camera already initialized; skipping start")
            return
        }
        val cameraProviderFuture = ProcessCameraProvider.getInstance(this)
        cameraProviderFuture.addListener({
            try {
                cameraProvider = cameraProviderFuture.get()
                bindCameraUseCases()
            } catch (e: Exception) {
                LogManager.logError("Failed to start camera", e)
                Toast.makeText(this, getString(R.string.main_camera_start_failed), Toast.LENGTH_LONG).show()
            }
        }, ContextCompat.getMainExecutor(this))
    }

    private fun bindCameraUseCases() {
        val provider = cameraProvider ?: return
        val rotation = previewView.display?.rotation ?: Surface.ROTATION_0
        val preview = Preview.Builder()
            .setTargetAspectRatio(AspectRatio.RATIO_4_3)
            .setTargetRotation(rotation)
            .build().also {
                it.setSurfaceProvider(previewView.surfaceProvider)
            }
        imageCapture = ImageCapture.Builder()
            .setCaptureMode(ImageCapture.CAPTURE_MODE_MINIMIZE_LATENCY)
            .setTargetAspectRatio(AspectRatio.RATIO_4_3)
            .setTargetRotation(rotation)
            .build()

        val cameraSelector = CameraSelector.DEFAULT_BACK_CAMERA

        try {
            provider.unbindAll()
            provider.bindToLifecycle(this, cameraSelector, preview, imageCapture)
            cameraInitialized = true
            captureLaunched = false
            singleShotDone = false
            updateCaptureButtonState()
            LogManager.log("Camera preview bound successfully")
        } catch (e: Exception) {
            LogManager.logError("Failed binding camera use cases", e)
            Toast.makeText(this, getString(R.string.main_camera_init_failed), Toast.LENGTH_LONG).show()
            cameraInitialized = false
            updateCaptureButtonState()
        }
    }

    private fun capturePhoto() {
        if (!isOnnxReady) {
            Toast.makeText(this, getString(R.string.main_model_not_ready), Toast.LENGTH_SHORT).show()
            updateCaptureButtonState()
            return
        }
        if (singleShotDone) {
            LogManager.log("Single shot already captured; ignoring capture request")
            return
        }
        if (captureLaunched) {
            LogManager.log("Capture already in progress; ignoring")
            return
        }
        val imageCapture = imageCapture ?: run {
            Toast.makeText(this, getString(R.string.main_camera_not_ready), Toast.LENGTH_SHORT).show()
            return
        }
        val photoFile = createTempPhotoFile()
        val outputOptions = ImageCapture.OutputFileOptions.Builder(photoFile).build()
        captureLaunched = true
        updateCaptureButtonState()
        progressCapture.visibility = View.VISIBLE
        LogManager.log("Starting capture to ${photoFile.absolutePath}")

        imageCapture.takePicture(outputOptions, cameraExecutor, object : ImageCapture.OnImageSavedCallback {
            override fun onError(exception: ImageCaptureException) {
                LogManager.logError("Capture failed", exception)
                photoFile.delete()
                captureLaunched = false
                scope.launch(Dispatchers.Main) {
                    progressCapture.visibility = View.GONE
                    updateCaptureButtonState()
                    Toast.makeText(this@MainActivity, getString(R.string.main_capture_failed), Toast.LENGTH_SHORT).show()
                }
            }

            override fun onImageSaved(outputFileResults: ImageCapture.OutputFileResults) {
                LogManager.log("Capture succeeded file=${photoFile.absolutePath}")
                singleShotDone = true
                captureLaunched = false
                scope.launch(Dispatchers.Main) {
                    val overlayRect = overlayView.getSquareRectNormalized()
                    processCapturedFile(photoFile, overlayRect)
                    progressCapture.visibility = View.GONE
                    updateCaptureButtonState()
                }
            }
        })
    }

    private fun createTempPhotoFile(): File {
        val dir = File(filesDir, "captures")
        if (!dir.exists()) dir.mkdirs()
        return File.createTempFile("capture_", ".jpg", dir)
    }

    private fun processCapturedFile(captureFile: File, overlayRect: RectF) {
        val dir = ensureAlbumDir()
        val fname = "img_${System.currentTimeMillis()}.jpg"
        val f = File(dir, fname)
        try {
            captureFile.copyTo(f, overwrite = true)
            captureFile.delete()
            LogManager.log("Stored capture as ${f.absolutePath}")
        } catch (e: Exception) {
            e.printStackTrace()
            LogManager.logError("Failed saving captured image", e)
            scope.launch(Dispatchers.Main) { Toast.makeText(this@MainActivity, getString(R.string.main_save_raw_failed), Toast.LENGTH_SHORT).show() }
            return
        }
    val cropFile = cropImageToOverlay(f, overlayRect)
    val inferenceInput = cropFile ?: f
    runInferenceAsync(inferenceInput, cropFile, f)
    }

    private fun handleImportedImage(uri: Uri) {
        scope.launch(Dispatchers.IO) {
            try {
                val inputStream = contentResolver.openInputStream(uri)
                if (inputStream == null) {
                    LogManager.log("Failed to open input stream for imported uri=$uri")
                    scope.launch(Dispatchers.Main) {
                        Toast.makeText(this@MainActivity, getString(R.string.main_read_image_failed), Toast.LENGTH_SHORT).show()
                    }
                    return@launch
                }
                val dir = ensureAlbumDir()
                val dest = File(dir, "import_${System.currentTimeMillis()}.jpg")
                inputStream.use { stream ->
                    FileOutputStream(dest).use { out ->
                        stream.copyTo(out)
                    }
                }
                LogManager.log("Imported gallery image saved as ${dest.absolutePath}")
                scope.launch(Dispatchers.Main) {
                    runInferenceAsync(dest, null, dest)
                }
            } catch (e: Exception) {
                LogManager.logError("Failed to import gallery image", e)
                scope.launch(Dispatchers.Main) {
                    Toast.makeText(this@MainActivity, getString(R.string.main_import_failed), Toast.LENGTH_SHORT).show()
                }
            }
        }
    }

    private fun runInferenceAsync(primaryFile: File, cropFile: File? = null, fallbackFile: File? = null) {
        val threshold = seekThreshold.progress / 100.0f
        val nmsIoU = seekNms.progress / 100.0f
        scope.launch(Dispatchers.IO) {
            scope.launch(Dispatchers.Main) { progInfer.visibility = View.VISIBLE }
            LogManager.log("Running inference on ${primaryFile.absolutePath} threshold=$threshold nms=$nmsIoU")
            val start = SystemClock.elapsedRealtime()
            var activeFile = primaryFile
            var result = OnnxHelper.runInferenceAndSavePath(this@MainActivity, primaryFile, threshold, nmsIoU)
            var previewBitmap = result?.annotatedPath?.let { BitmapFactory.decodeFile(it) }
            var usedFallback = false
            if ((result == null || result.detections.isEmpty()) && fallbackFile != null && fallbackFile.exists() && fallbackFile != primaryFile) {
                LogManager.log("Primary inference yielded no detection; retrying with original image ${fallbackFile.absolutePath}")
                result?.annotatedPath?.let { File(it).takeIf(File::exists)?.delete() }
                result = OnnxHelper.runInferenceAndSavePath(this@MainActivity, fallbackFile, threshold, nmsIoU)
                previewBitmap = result?.annotatedPath?.let { BitmapFactory.decodeFile(it) }
                activeFile = fallbackFile
                usedFallback = true
            }
            val duration = SystemClock.elapsedRealtime() - start
            scope.launch(Dispatchers.Main) {
                progInfer.visibility = View.GONE
                singleShotDone = false
                captureLaunched = false
                updateTimingStats(duration)
                if (result != null) {
                    renderInferenceResult(result, previewBitmap)
                    if (usedFallback) {
                        detectionStatsTv.text = detectionStatsTv.text.toString() + getString(R.string.main_detection_full_image_suffix)
                    }
                    val toastMsg = if (result.detections.isEmpty()) {
                        getString(R.string.main_inference_no_detection)
                    } else {
                        getString(R.string.main_inference_with_detection, result.detections.size)
                    }
                    Toast.makeText(this@MainActivity, toastMsg, Toast.LENGTH_SHORT).show()
                    LogManager.log("Inference success duration=${duration}ms output=${result.annotatedPath} source=${activeFile.absolutePath}")
                    if (cropFile != null) {
                        LogManager.log("Square crop saved at ${cropFile.absolutePath}")
                    }
                    persistDetectionHistory(result, activeFile, threshold, nmsIoU, usedFallback)
                    refreshGallery()
                } else {
                    Toast.makeText(this@MainActivity, getString(R.string.main_inference_failed), Toast.LENGTH_SHORT).show()
                    LogManager.log("Inference failed duration=${duration}ms")
                    cropFile?.delete()
                    detectionStatsTv.text = getString(R.string.main_inference_failed)
                    lastResultPath = null
                    lastResultPreview.setImageDrawable(null)
                    lastResultPreview.visibility = View.GONE
                }
                updateCaptureButtonState()
            }
        }
    }

    private fun cropImageToOverlay(sourceFile: File, overlayRect: RectF): File? {
        return try {
            val bitmap = decodeBitmapWithOrientation(sourceFile) ?: return null
            val leftPx = (overlayRect.left * bitmap.width).toInt().coerceIn(0, bitmap.width - 1)
            val topPx = (overlayRect.top * bitmap.height).toInt().coerceIn(0, bitmap.height - 1)
            val widthPx = (overlayRect.width() * bitmap.width).toInt().coerceAtLeast(1)
            val heightPx = (overlayRect.height() * bitmap.height).toInt().coerceAtLeast(1)
            val squareSize = minOf(widthPx, heightPx, bitmap.width - leftPx, bitmap.height - topPx)
            val safeLeft = leftPx.coerceIn(0, bitmap.width - squareSize)
            val safeTop = topPx.coerceIn(0, bitmap.height - squareSize)
            val squareBitmap = Bitmap.createBitmap(bitmap, safeLeft, safeTop, squareSize, squareSize)
            val cropFile = File(sourceFile.parentFile, "crop_${System.currentTimeMillis()}.jpg")
            FileOutputStream(cropFile).use { out ->
                squareBitmap.compress(Bitmap.CompressFormat.JPEG, 95, out)
            }
            squareBitmap.recycle()
            bitmap.recycle()
            cropFile
        } catch (e: Exception) {
            LogManager.logError("Failed to crop image to overlay", e)
            null
        }
    }

    private fun decodeBitmapWithOrientation(file: File): Bitmap? {
        val raw = BitmapFactory.decodeFile(file.absolutePath) ?: return null
        return try {
            val exif = ExifInterface(file.absolutePath)
            val orientation = exif.getAttributeInt(ExifInterface.TAG_ORIENTATION, ExifInterface.ORIENTATION_NORMAL)
            val matrix = Matrix()
            when (orientation) {
                ExifInterface.ORIENTATION_ROTATE_90 -> matrix.postRotate(90f)
                ExifInterface.ORIENTATION_ROTATE_180 -> matrix.postRotate(180f)
                ExifInterface.ORIENTATION_ROTATE_270 -> matrix.postRotate(270f)
                ExifInterface.ORIENTATION_FLIP_HORIZONTAL -> matrix.preScale(-1f, 1f)
                ExifInterface.ORIENTATION_FLIP_VERTICAL -> matrix.preScale(1f, -1f)
                ExifInterface.ORIENTATION_TRANSPOSE -> {
                    matrix.postRotate(90f)
                    matrix.preScale(-1f, 1f)
                }
                ExifInterface.ORIENTATION_TRANSVERSE -> {
                    matrix.postRotate(270f)
                    matrix.preScale(-1f, 1f)
                }
            }
            if (matrix.isIdentity) {
                raw
            } else {
                val transformed = Bitmap.createBitmap(raw, 0, 0, raw.width, raw.height, matrix, true)
                if (transformed != raw) {
                    raw.recycle()
                }
                transformed
            }
        } catch (e: Exception) {
            LogManager.logError("Failed to apply EXIF orientation for ${file.absolutePath}", e)
            raw
        }
    }

    override fun onDestroy() {
        super.onDestroy()
        cameraProvider?.unbindAll()
        cameraExecutor.shutdown()
    }

    private fun updateTimingStats(lastMs: Long) {
        if (lastMs <= 0) return
        totalInferenceMs += lastMs
        inferenceCount += 1
        val avg = totalInferenceMs / inferenceCount
    timingTv.text = getString(R.string.main_timing_stats, lastMs, avg)
        LogManager.log("Timing updated. last=${lastMs}ms avg=${avg}ms")
    }

    private fun renderInferenceResult(result: InferenceResult, previewBitmap: Bitmap?) {
        lastResultPath = result.annotatedPath
        lastPathTv.text = getString(R.string.main_recent_result_value, result.annotatedPath)
        val count = result.detections.size
        val summary = if (count == 0) {
            getString(R.string.main_detection_summary_empty)
        } else {
            val scores = result.detections
                .sortedByDescending { it.score }
                .take(3)
                .joinToString(separator = " / ") { String.format("%.2f", it.score) }
            getString(R.string.main_detection_summary_with_scores, count, scores)
        }
        detectionStatsTv.text = summary
        if (::bottomSheetBehavior.isInitialized) {
            bottomSheetBehavior.state = BottomSheetBehavior.STATE_EXPANDED
        }
        if (previewBitmap != null) {
            lastResultPreview.setImageBitmap(previewBitmap)
            lastResultPreview.visibility = View.VISIBLE
        } else {
            lastResultPreview.setImageDrawable(null)
            lastResultPreview.visibility = View.GONE
        }
    }

    private fun toggleBottomSheet() {
        if (!::bottomSheetBehavior.isInitialized) return
        val nextState = if (bottomSheetBehavior.state == BottomSheetBehavior.STATE_COLLAPSED) {
            BottomSheetBehavior.STATE_EXPANDED
        } else {
            BottomSheetBehavior.STATE_COLLAPSED
        }
        bottomSheetBehavior.state = nextState
    }

    private fun updateSheetToggleIcon(state: Int) {
        if (!::sheetToggleBtn.isInitialized) return
        val collapsed = state == BottomSheetBehavior.STATE_COLLAPSED
        sheetToggleBtn.rotation = if (collapsed) 180f else 0f
    }

    private fun setupPresetButtons() {
        presetGroup.addOnButtonCheckedListener { _, checkedId, isChecked ->
            if (!isChecked) return@addOnButtonCheckedListener
            val preset = when (checkedId) {
                R.id.btn_preset_precision -> DetectionPreset.PRECISION
                R.id.btn_preset_recall -> DetectionPreset.RECALL
                else -> DetectionPreset.BALANCED
            }
            applyPreset(preset)
        }
        presetGroup.check(R.id.btn_preset_balanced)
        applyPreset(DetectionPreset.BALANCED)
    }

    private fun applyPreset(preset: DetectionPreset) {
        updatingFromPreset = true
        seekThreshold.progress = preset.threshold
        seekNms.progress = preset.nms
    tvThresholdLabel.text = getString(R.string.main_threshold_value, preset.threshold / 100f)
    tvNmsLabel.text = getString(R.string.main_nms_value, preset.nms / 100f)
        updatingFromPreset = false
    }

    private enum class DetectionPreset(val threshold: Int, val nms: Int) {
        PRECISION(threshold = 55, nms = 45),
        BALANCED(threshold = 18, nms = 30),
        RECALL(threshold = 5, nms = 20)
    }

    private fun persistDetectionHistory(result: InferenceResult, sourceFile: File, threshold: Float, nms: Float, usedFallback: Boolean) {
        val project = ProjectRepository.getCurrentProject(this)
        val entry = DetectionHistory.DetectionEntry(
            timestamp = System.currentTimeMillis(),
            projectName = project,
            sourceFileName = sourceFile.name,
            annotatedFileName = File(result.annotatedPath).name,
            threshold = threshold,
            nms = nms,
            usedFallback = usedFallback,
            detections = result.detections.map {
                DetectionHistory.DetectionDetail(
                    score = it.score,
                    left = it.bounds.left,
                    top = it.bounds.top,
                    right = it.bounds.right,
                    bottom = it.bounds.bottom
                )
            }
        )
        scope.launch(Dispatchers.IO) {
            DetectionHistory.record(this@MainActivity, entry)
        }
    }

    private fun showFatalErrorDialog(t: Throwable) {
        val message = buildString {
            appendLine(getString(R.string.main_error_fatal_intro))
            appendLine()
            appendLine(getString(R.string.main_error_fatal_type, t::class.java.name))
            appendLine(
                getString(
                    R.string.main_error_fatal_message,
                    t.message ?: getString(R.string.main_error_fatal_message_empty)
                )
            )
            appendLine()
            appendLine(getString(R.string.main_error_fatal_stack))
            appendLine(t.stackTraceToString())
        }

        AlertDialog.Builder(this)
            .setTitle(R.string.main_error_fatal_title)
            .setMessage(message)
            .setCancelable(false)
            .setPositiveButton(R.string.main_error_fatal_copy_close) { dialog, _ ->
                val clipboard = getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
                clipboard.setPrimaryClip(ClipData.newPlainText("MicroAI Colony Fatal", message))
                Toast.makeText(this, getString(R.string.main_error_copied), Toast.LENGTH_SHORT).show()
                dialog.dismiss()
                finish()
            }
            .setNegativeButton(R.string.main_error_fatal_close) { dialog, _ ->
                dialog.dismiss()
                finish()
            }
            .show()
    }
}
