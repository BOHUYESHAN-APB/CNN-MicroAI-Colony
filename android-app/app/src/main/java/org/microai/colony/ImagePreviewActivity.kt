package org.microai.colony

import android.content.Intent
import android.os.Bundle
import android.widget.Button
import android.widget.ImageView
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.FileProvider
import android.graphics.BitmapFactory
import java.io.File

class ImagePreviewActivity : AppCompatActivity() {
    companion object {
        const val EXTRA_PATH = "extra_path"
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_image_preview)

        val path = intent.getStringExtra(EXTRA_PATH)
        if (path.isNullOrEmpty()) {
            finish()
            return
        }

        val file = File(path)
        val imageView: ImageView = findViewById(R.id.preview_image)
        val shareBtn: Button = findViewById(R.id.btn_share)
        val closeBtn: Button = findViewById(R.id.btn_close)

        if (file.exists()) {
            val bmp = BitmapFactory.decodeFile(file.absolutePath)
            imageView.setImageBitmap(bmp)
        }

        shareBtn.setOnClickListener {
            val uri = FileProvider.getUriForFile(this, "${packageName}.fileprovider", file)
            val shareIntent = Intent(Intent.ACTION_SEND).apply {
                type = "image/jpeg"
                putExtra(Intent.EXTRA_STREAM, uri)
                addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
            }
            startActivity(Intent.createChooser(shareIntent, "Share annotated image"))
        }

        closeBtn.setOnClickListener { finish() }
    }
}
