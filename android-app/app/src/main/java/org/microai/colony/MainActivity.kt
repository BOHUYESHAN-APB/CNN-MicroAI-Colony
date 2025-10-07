package org.microai.colony

import android.Manifest
import android.app.Activity
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Bundle
import android.os.SystemClock
import android.provider.MediaStore
import android.widget.Button
import android.widget.TextView
import android.widget.Toast
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import androidx.core.content.FileProvider
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import java.io.File

class MainActivity : AppCompatActivity() {
    private val scope = CoroutineScope(Dispatchers.Main)
    private lateinit var takeBtn: Button
    private lateinit var galleryRv: RecyclerView
    private lateinit var adapter: ImageAdapter
    private lateinit var lastPathTv: TextView
    private lateinit var tvThresholdLabel: TextView
    private lateinit var seekThreshold: android.widget.SeekBar
    private lateinit var tvNmsLabel: TextView
    private lateinit var seekNms: android.widget.SeekBar
    private lateinit var progInfer: android.widget.ProgressBar
    private var pendingCaptureFile: File? = null
    private lateinit var timingTv: TextView
    private var totalInferenceMs: Long = 0
    private var inferenceCount: Int = 0

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(org.microai.colony.R.layout.activity_main)

        takeBtn = findViewById(org.microai.colony.R.id.btn_take)
        lastPathTv = findViewById(org.microai.colony.R.id.tv_last_path)
        galleryRv = findViewById(org.microai.colony.R.id.rv_gallery)
        tvThresholdLabel = findViewById(org.microai.colony.R.id.tv_threshold_label)
        seekThreshold = findViewById(org.microai.colony.R.id.seek_threshold)
        tvNmsLabel = findViewById(org.microai.colony.R.id.tv_nms_label)
        seekNms = findViewById(org.microai.colony.R.id.seek_nms)
        progInfer = findViewById(org.microai.colony.R.id.prog_infer)
    timingTv = findViewById(org.microai.colony.R.id.tv_timing)

        adapter = ImageAdapter { file ->
            val intent = Intent(this, ImagePreviewActivity::class.java)
            intent.putExtra(ImagePreviewActivity.EXTRA_PATH, file.absolutePath)
            startActivity(intent)
        }
        galleryRv.layoutManager = LinearLayoutManager(this)
        galleryRv.adapter = adapter

        OnnxHelper.init(this)

        takeBtn.setOnClickListener { checkCameraPermissionAndTake() }
        seekThreshold.setOnSeekBarChangeListener(object: android.widget.SeekBar.OnSeekBarChangeListener{
            override fun onProgressChanged(seekBar: android.widget.SeekBar?, progress: Int, fromUser: Boolean) {
                val v = progress / 100.0f
                tvThresholdLabel.text = String.format("Score threshold: %.2f", v)
            }
            override fun onStartTrackingTouch(seekBar: android.widget.SeekBar?) {}
            override fun onStopTrackingTouch(seekBar: android.widget.SeekBar?) {}
        })
        seekNms.setOnSeekBarChangeListener(object: android.widget.SeekBar.OnSeekBarChangeListener{
            override fun onProgressChanged(seekBar: android.widget.SeekBar?, progress: Int, fromUser: Boolean) {
                val v = progress / 100.0f
                tvNmsLabel.text = String.format("NMS IoU: %.2f", v)
            }
            override fun onStartTrackingTouch(seekBar: android.widget.SeekBar?) {}
            override fun onStopTrackingTouch(seekBar: android.widget.SeekBar?) {}
        })
        refreshGallery()
    }

    private fun refreshGallery() {
        val dir = File(filesDir, "album")
        if (!dir.exists()) dir.mkdirs()
        val imgs = dir.listFiles { f -> f.extension.toLowerCase() in listOf("jpg","jpeg","png") }?.sortedByDescending { it.lastModified() } ?: emptyList()
        adapter.submitList(imgs)
    }

    private fun checkCameraPermissionAndTake() {
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.CAMERA) != PackageManager.PERMISSION_GRANTED) {
            ActivityCompat.requestPermissions(this, arrayOf(Manifest.permission.CAMERA), 101)
            return
        }
        dispatchTakePictureIntent()
    }

    private val takePhotoLauncher = registerForActivityResult(ActivityResultContracts.StartActivityForResult()) { res ->
        if (res.resultCode == Activity.RESULT_OK) {
            val file = pendingCaptureFile
            if (file != null && file.exists()) {
                processCapturedFile(file)
            } else {
                Toast.makeText(this, "未捕获到图像", Toast.LENGTH_SHORT).show()
            }
        } else {
            pendingCaptureFile?.delete()
            pendingCaptureFile = null
        }
    }

    private fun dispatchTakePictureIntent() {
        val takePictureIntent = Intent(MediaStore.ACTION_IMAGE_CAPTURE)
        if (takePictureIntent.resolveActivity(packageManager) != null) {
            val captureFile = createTempImageFile()
            val uri = FileProvider.getUriForFile(this, "${packageName}.fileprovider", captureFile)
            pendingCaptureFile = captureFile
            takePictureIntent.putExtra(MediaStore.EXTRA_OUTPUT, uri)
            takePictureIntent.addFlags(Intent.FLAG_GRANT_WRITE_URI_PERMISSION or Intent.FLAG_GRANT_READ_URI_PERMISSION)
            takePhotoLauncher.launch(takePictureIntent)
        } else {
            Toast.makeText(this, "无可用相机应用", Toast.LENGTH_SHORT).show()
        }
    }

    private fun createTempImageFile(): File {
        val dir = File(filesDir, "captures")
        if (!dir.exists()) dir.mkdirs()
        return File.createTempFile("capture_", ".jpg", dir)
    }

    private fun processCapturedFile(captureFile: File) {
        val dir = File(filesDir, "album")
        if (!dir.exists()) dir.mkdirs()
        val fname = "img_${System.currentTimeMillis()}.jpg"
        val f = File(dir, fname)
        try {
            captureFile.copyTo(f, overwrite = true)
            captureFile.delete()
        } catch (e: Exception) {
            e.printStackTrace()
            Toast.makeText(this, "保存原始图片失败", Toast.LENGTH_SHORT).show()
            return
        }
        pendingCaptureFile = null

        // run inference and save annotated image (keeps original) - pass threshold and nms IoU
        scope.launch(Dispatchers.IO) {
            val threshold = seekThreshold.progress / 100.0f
            val nmsIoU = seekNms.progress / 100.0f
            scope.launch(Dispatchers.Main) { progInfer.visibility = android.view.View.VISIBLE }
            val start = SystemClock.elapsedRealtime()
            val annotPath = OnnxHelper.runInferenceAndSavePath(this@MainActivity, f, threshold, nmsIoU)
            val duration = SystemClock.elapsedRealtime() - start
            scope.launch(Dispatchers.Main) { progInfer.visibility = android.view.View.GONE }
            if (annotPath != null) {
                scope.launch(Dispatchers.Main) {
                    updateTimingStats(duration)
                    Toast.makeText(this@MainActivity, "Inference complete, saved to album", Toast.LENGTH_SHORT).show()
                    // show path to the saved annotated image
                    lastPathTv.text = annotPath
                    refreshGallery()
                }
            } else {
                scope.launch(Dispatchers.Main) {
                    updateTimingStats(duration)
                    Toast.makeText(this@MainActivity, "Inference failed", Toast.LENGTH_SHORT).show()
                }
            }
        }
    }

    private fun updateTimingStats(lastMs: Long) {
        if (lastMs <= 0) return
        totalInferenceMs += lastMs
        inferenceCount += 1
        val avg = totalInferenceMs / inferenceCount
        timingTv.text = String.format("Last inference: %d ms | Avg: %d ms", lastMs, avg)
    }
}
