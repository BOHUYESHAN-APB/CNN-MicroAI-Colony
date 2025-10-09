package com.bohuyshan.microai.colony

import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import com.google.android.material.button.MaterialButton
import com.google.android.material.appbar.MaterialToolbar

class AboutActivity : AppCompatActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_about)

        val toolbar = findViewById<MaterialToolbar>(R.id.toolbar)
        val githubButton = findViewById<MaterialButton>(R.id.btn_open_github)

        toolbar.setNavigationOnClickListener { finish() }

        githubButton.setOnClickListener {
            val uri = Uri.parse("https://github.com/BOHUYESHAN-APB/CNN-MicroAI-Colony")
            val intent = Intent(Intent.ACTION_VIEW, uri)
            startActivity(intent)
        }

        val versionView = findViewById<TextView>(R.id.tv_version)
        val packageInfo = packageManager.getPackageInfo(packageName, 0)
        versionView.text = getString(R.string.about_version_format, packageInfo.versionName ?: "-")
    }
}
