package com.microai.colony.utils

import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.net.Uri
import android.os.Environment
import dagger.hilt.android.qualifiers.ApplicationContext
import java.io.File
import java.io.FileOutputStream
import java.text.SimpleDateFormat
import java.util.*
import javax.inject.Inject
import javax.inject.Singleton

/**
 * 文件工具类
 */
@Singleton
class FileUtils @Inject constructor() {
    companion object {
        private const val IMAGE_PREFIX = "IMG_"
        private const val IMAGE_SUFFIX = ".jpg"
        private const val QUALITY = 100
    }
    
    /**
     * 创建图片文件
     */
    fun createImageFile(context: Context): File {
        val timeStamp = SimpleDateFormat("yyyyMMdd_HHmmss", Locale.getDefault()).format(Date())
        val fileName = "${IMAGE_PREFIX}${timeStamp}${IMAGE_SUFFIX}"
        
        return File(
            context.getExternalFilesDir(Environment.DIRECTORY_PICTURES),
            fileName
        )
    }
    
    /**
     * 从Uri创建临时文件
     */
    fun createTempFileFromUri(context: Context, uri: Uri): File {
        val inputStream = context.contentResolver.openInputStream(uri)
        val bitmap = BitmapFactory.decodeStream(inputStream)
        
        val tempFile = createImageFile(context)
        FileOutputStream(tempFile).use { outputStream ->
            bitmap.compress(Bitmap.CompressFormat.JPEG, QUALITY, outputStream)
        }
        
        return tempFile
    }
    
    /**
     * 清理图片缓存
     */
    fun clearImageCache(context: Context) {
        context.getExternalFilesDir(Environment.DIRECTORY_PICTURES)?.let { dir ->
            dir.listFiles()?.forEach { file ->
                if (file.name.startsWith(IMAGE_PREFIX) && file.name.endsWith(IMAGE_SUFFIX)) {
                    file.delete()
                }
            }
        }
    }
    
    /**
     * 获取文件大小（MB）
     */
    fun getFileSizeInMB(file: File): Double {
        return file.length().toDouble() / (1024 * 1024)
    }
    
    /**
     * 检查存储空间
     */
    fun checkStorageSpace(context: Context): Boolean {
        val dir = context.getExternalFilesDir(Environment.DIRECTORY_PICTURES)
        val freeSpace = dir?.freeSpace ?: 0
        val minRequiredSpace = 100 * 1024 * 1024 // 100MB
        
        return freeSpace >= minRequiredSpace
    }
}
