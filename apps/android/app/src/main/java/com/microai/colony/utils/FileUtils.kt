package com.microai.colony.utils

import android.content.Context
import android.net.Uri
import android.webkit.MimeTypeMap
import com.microai.colony.data.model.ModelInfo
import java.io.File
import java.io.FileOutputStream
import java.security.MessageDigest
import java.util.*

object FileUtils {
    private const val MODEL_DIR = "models"
    
    fun copyModelFile(context: Context, uri: Uri): Result<Triple<File, String, Long>> = runCatching {
        val inputStream = context.contentResolver.openInputStream(uri)
            ?: throw IllegalStateException("Cannot open input stream")
            
        // 创建模型目录
        val modelDir = File(context.filesDir, MODEL_DIR).apply { 
            if (!exists()) mkdirs()
        }
        
        // 生成唯一文件名
        val fileName = UUID.randomUUID().toString()
        val extension = getFileExtension(context, uri)
        val targetFile = File(modelDir, "$fileName.$extension")
        
        // 复制文件
        FileOutputStream(targetFile).use { outputStream ->
            inputStream.use { input ->
                input.copyTo(outputStream)
            }
        }
        
        // 计算文件hash
        val hash = calculateFileHash(targetFile)
        
        Triple(targetFile, hash, targetFile.length())
    }
    
    private fun getFileExtension(context: Context, uri: Uri): String {
        val mimeType = context.contentResolver.getType(uri)
        return MimeTypeMap.getSingleton()
            .getExtensionFromMimeType(mimeType)
            ?: uri.path?.substringAfterLast('.')
            ?: "unknown"
    }
    
    private fun calculateFileHash(file: File): String {
        val digest = MessageDigest.getInstance("SHA-256")
        file.inputStream().use { input ->
            val buffer = ByteArray(8192)
            var read: Int
            while (input.read(buffer).also { read = it } > 0) {
                digest.update(buffer, 0, read)
            }
        }
        return digest.digest().fold("") { str, it -> 
            str + "%02x".format(it) 
        }
    }
    
    fun deleteModel(context: Context, model: ModelInfo): Boolean {
        return try {
            File(model.path).delete()
        } catch (e: Exception) {
            e.printStackTrace()
            false
        }
    }
    
    fun getModelFile(context: Context, model: ModelInfo): File? {
        return try {
            File(model.path).takeIf { it.exists() }
        } catch (e: Exception) {
            e.printStackTrace()
            null
        }
    }
}
