package org.microai.colony

import android.Manifest
import android.app.Activity
import android.content.Intent
import android.content.pm.PackageManager
import android.graphics.Bitmap
import android.graphics.Canvas
import android.graphics.Paint
import android.graphics.RectF
import android.os.Bundle
import android.provider.MediaStore
import android.widget.Button
import android.widget.Toast
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import java.io.File
import java.io.FileOutputStream

class MainActivity : AppCompatActivity() {
    private val scope = CoroutineScope(Dispatchers.Main)
    private lateinit var takeBtn: Button
    private lateinit var galleryRv: RecyclerView
    private lateinit var adapter: ImageAdapter

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(org.microai.colony.R.layout.activity_main)

        takeBtn = findViewById(org.microai.colony.R.id.btn_take)
        galleryRv = findViewById(org.microai.colony.R.id.rv_gallery)

        adapter = ImageAdapter(this)
        galleryRv.layoutManager = LinearLayoutManager(this)
        galleryRv.adapter = adapter

        OnnxHelper.init(this)

        takeBtn.setOnClickListener { checkCameraPermissionAndTake() }
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
            val bmp = res.data?.extras?.get("data") as? Bitmap
            bmp?.let { saveAndProcess(it) }
        }
    }

    private fun dispatchTakePictureIntent() {
        val takePictureIntent = Intent(MediaStore.ACTION_IMAGE_CAPTURE)
        takePhotoLauncher.launch(takePictureIntent)
    }

    private fun saveAndProcess(bitmap: Bitmap) {
        val dir = File(filesDir, "album")
        if (!dir.exists()) dir.mkdirs()
        val fname = "img_${System.currentTimeMillis()}.jpg"
        val f = File(dir, fname)
        FileOutputStream(f).use { out -> bitmap.compress(Bitmap.CompressFormat.JPEG, 90, out) }

        // run inference and save annotated image
        scope.launch(Dispatchers.IO) {
            val annotated = OnnxHelper.runInferenceAndAnnotate(this@MainActivity, f)
            if (annotated != null) {
                // overwrite file with annotated image
                FileOutputStream(f).use { out -> annotated.compress(Bitmap.CompressFormat.JPEG, 90, out) }
                scope.launch(Dispatchers.Main) {
                    Toast.makeText(this@MainActivity, "Inference complete, saved to album", Toast.LENGTH_SHORT).show()
                    refreshGallery()
                }
            } else {
                scope.launch(Dispatchers.Main) {
                    Toast.makeText(this@MainActivity, "Inference failed", Toast.LENGTH_SHORT).show()
                }
            }
        }
    }
}
