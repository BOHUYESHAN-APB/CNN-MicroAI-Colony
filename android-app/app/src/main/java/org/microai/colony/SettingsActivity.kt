package com.bohuyshan.microai.colony

import android.content.Intent
import android.os.Bundle
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.FileProvider
import androidx.lifecycle.lifecycleScope
import com.google.android.material.appbar.MaterialToolbar
import com.google.android.material.button.MaterialButton
import com.google.android.material.button.MaterialButtonToggleGroup
import com.google.android.material.card.MaterialCardView
import com.google.android.material.materialswitch.MaterialSwitch
import java.io.File
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

class SettingsActivity : AppCompatActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_settings)

        val toolbar = findViewById<MaterialToolbar>(R.id.toolbar)
        val group = findViewById<MaterialButtonToggleGroup>(R.id.group_engine_priority)
        val switchGpu = findViewById<MaterialSwitch>(R.id.switch_gpu)
        val switchNpu = findViewById<MaterialSwitch>(R.id.switch_npu)
        val switchCpu = findViewById<MaterialSwitch>(R.id.switch_cpu)
        val aboutCard = findViewById<MaterialCardView>(R.id.card_about)
        val exportLogBtn = findViewById<MaterialButton>(R.id.btn_export_log)
        val exportPdfBtn = findViewById<MaterialButton>(R.id.btn_export_pdf)
        val exportTableBtn = findViewById<MaterialButton>(R.id.btn_export_table)
        val clearLogBtn = findViewById<MaterialButton>(R.id.btn_clear_log)

        toolbar.setNavigationOnClickListener { finish() }

        val preferred = InferencePreferences.getPreferredEngine(this)
        group.check(buttonIdForEngine(preferred))
        switchGpu.isChecked = InferencePreferences.isEngineAllowed(this, InferencePreferences.Engine.GPU)
        switchNpu.isChecked = InferencePreferences.isEngineAllowed(this, InferencePreferences.Engine.NPU)
        switchCpu.isChecked = InferencePreferences.isEngineAllowed(this, InferencePreferences.Engine.CPU)

        group.addOnButtonCheckedListener { _, checkedId, isChecked ->
            if (!isChecked) return@addOnButtonCheckedListener
            when (checkedId) {
                R.id.btn_engine_gpu -> InferencePreferences.setPreferredEngine(this, InferencePreferences.Engine.GPU)
                R.id.btn_engine_npu -> InferencePreferences.setPreferredEngine(this, InferencePreferences.Engine.NPU)
                R.id.btn_engine_cpu -> InferencePreferences.setPreferredEngine(this, InferencePreferences.Engine.CPU)
            }
        }

        switchGpu.setOnCheckedChangeListener { _, isChecked ->
            InferencePreferences.setEngineAllowed(this, InferencePreferences.Engine.GPU, isChecked)
        }
        switchNpu.setOnCheckedChangeListener { _, isChecked ->
            InferencePreferences.setEngineAllowed(this, InferencePreferences.Engine.NPU, isChecked)
        }
        switchCpu.setOnCheckedChangeListener { _, isChecked ->
            InferencePreferences.setEngineAllowed(this, InferencePreferences.Engine.CPU, isChecked)
        }

        exportLogBtn.setOnClickListener { shareCurrentLog() }
        exportPdfBtn.setOnClickListener { exportProjectPdf() }
        exportTableBtn.setOnClickListener { exportProjectTable() }
        clearLogBtn.setOnClickListener {
            LogManager.reset(this)
            LogManager.log("Log cleared by user from settings")
            Toast.makeText(this, R.string.settings_clear_log_success, Toast.LENGTH_SHORT).show()
        }

        aboutCard.setOnClickListener {
            startActivity(Intent(this, AboutActivity::class.java))
        }
    }

    private fun shareCurrentLog() {
        val uri = LogManager.getLogUri(this)
        if (uri == null) {
            Toast.makeText(this, R.string.settings_no_log_to_export, Toast.LENGTH_SHORT).show()
            return
        }
        val shareIntent = Intent(Intent.ACTION_SEND).apply {
            type = "text/plain"
            putExtra(Intent.EXTRA_STREAM, uri)
            addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
        }
        startActivity(Intent.createChooser(shareIntent, getString(R.string.settings_action_export_log)))
        LogManager.log("Log export triggered from settings")
    }

    private fun exportProjectPdf() {
        lifecycleScope.launch {
            val project = ProjectRepository.getCurrentProject(this@SettingsActivity)
            val toast = Toast.makeText(this@SettingsActivity, R.string.settings_export_pdf_in_progress, Toast.LENGTH_SHORT)
            toast.show()
            val file = withContext(Dispatchers.IO) { ExportManager.exportPdf(this@SettingsActivity, project) }
            toast.cancel()
            if (file == null) {
                Toast.makeText(this@SettingsActivity, R.string.settings_export_pdf_failed, Toast.LENGTH_LONG).show()
            } else {
                shareFile(file, "application/pdf", getString(R.string.settings_action_export_pdf))
            }
        }
    }

    private fun exportProjectTable() {
        lifecycleScope.launch {
            val project = ProjectRepository.getCurrentProject(this@SettingsActivity)
            val toast = Toast.makeText(this@SettingsActivity, R.string.settings_export_table_in_progress, Toast.LENGTH_SHORT)
            toast.show()
            val file = withContext(Dispatchers.IO) { ExportManager.exportCsv(this@SettingsActivity, project) }
            toast.cancel()
            if (file == null) {
                Toast.makeText(this@SettingsActivity, R.string.settings_export_table_failed, Toast.LENGTH_LONG).show()
            } else {
                shareFile(file, "text/csv", getString(R.string.settings_action_export_table))
            }
        }
    }

    private fun shareFile(file: File, mimeType: String, title: String) {
        val uri = FileProvider.getUriForFile(this, "${packageName}.fileprovider", file)
        val intent = Intent(Intent.ACTION_SEND).apply {
            type = mimeType
            putExtra(Intent.EXTRA_STREAM, uri)
            addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
        }
        startActivity(Intent.createChooser(intent, title))
    }

    private fun buttonIdForEngine(engine: InferencePreferences.Engine): Int = when (engine) {
        InferencePreferences.Engine.GPU -> R.id.btn_engine_gpu
        InferencePreferences.Engine.NPU -> R.id.btn_engine_npu
        InferencePreferences.Engine.CPU -> R.id.btn_engine_cpu
    }
}
