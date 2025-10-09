package com.bohuyshan.microai.colony

import android.content.Context
import android.net.Uri
import android.util.Log
import androidx.core.content.FileProvider
import java.io.File
import java.io.FileWriter
import java.io.IOException
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

object LogManager {
    private const val LOG_DIR_NAME = "logs"
    private const val LOG_FILE_NAME = "session.log"
    private const val TAG = "MicroAIColonyLog"

    private val dateFormat = SimpleDateFormat("yyyy-MM-dd HH:mm:ss.SSS", Locale.US)
    private var logFile: File? = null

    @Synchronized
    fun init(context: Context) {
        val dir = File(context.filesDir, LOG_DIR_NAME)
        if (!dir.exists()) {
            dir.mkdirs()
        }

        val file = File(dir, LOG_FILE_NAME)
        try {
            if (file.exists()) {
                file.writeText("")
            } else {
                file.createNewFile()
            }
            logFile = file
            log("Session started at ${dateFormat.format(Date())}")
        } catch (e: IOException) {
            Log.e(TAG, "Failed to initialize log file", e)
        }
    }

    @Synchronized
    fun reset(context: Context) {
        init(context)
    }

    @Synchronized
    fun log(message: String) {
        appendLine("INFO", message)
    }

    @Synchronized
    fun logError(message: String, throwable: Throwable? = null) {
        val detail = if (throwable != null) {
            "$message\n${Log.getStackTraceString(throwable)}"
        } else {
            message
        }
        appendLine("ERROR", detail)
    }

    private fun appendLine(level: String, message: String) {
        val file = logFile ?: return
        val formatted = "${dateFormat.format(Date())} [$level] $message"
        try {
            FileWriter(file, true).use { writer ->
                writer.appendLine(formatted)
            }
        } catch (e: IOException) {
            Log.e(TAG, "Failed to write log", e)
        }
    }

    @Synchronized
    fun getLogUri(context: Context): Uri? {
        val file = logFile
        return if (file != null && file.exists() && file.length() > 0) {
            FileProvider.getUriForFile(context, "${context.packageName}.fileprovider", file)
        } else {
            null
        }
    }

    @Synchronized
    fun hasLog(): Boolean {
        val file = logFile
        return file != null && file.exists() && file.length() > 0
    }
}
