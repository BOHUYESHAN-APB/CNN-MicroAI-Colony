package com.microai.colony.utils

import android.content.Context
import android.graphics.*
import android.net.Uri
import androidx.core.content.ContextCompat
import com.microai.colony.R
import com.microai.colony.data.model.DetectionResult
import javax.inject.Inject
import javax.inject.Singleton

/**
 * 图片处理工具类
 */
@Singleton
class ImageUtils @Inject constructor() {
    companion object {
        private const val BOX_STROKE_WIDTH = 4f
        private const val TEXT_SIZE = 36f
        private const val TEXT_PADDING = 8f
    }
    
    /**
     * 绘制检测框
     */
    fun drawDetectionBoxes(
        context: Context,
        bitmap: Bitmap,
        detectionResult: DetectionResult
    ): Bitmap {
        val mutable = bitmap.copy(Bitmap.Config.ARGB_8888, true)
        val canvas = Canvas(mutable)
        val paint = Paint().apply {
            style = Paint.Style.STROKE
            strokeWidth = BOX_STROKE_WIDTH
            color = ContextCompat.getColor(context, R.color.detection_box_stroke)
        }
        
        val textPaint = Paint().apply {
            style = Paint.Style.FILL
            textSize = TEXT_SIZE
            color = Color.WHITE
        }
        
        val bgPaint = Paint().apply {
            style = Paint.Style.FILL
            color = Color.BLACK
            alpha = 160
        }
        
        detectionResult.boxes.forEachIndexed { index, box ->
            // 绘制检测框
            canvas.drawRect(
                box.x1,
                box.y1,
                box.x2,
                box.y2,
                paint
            )
            
            // 绘制置信度文本
            val text = String.format("%.2f", box.confidence)
            val bounds = Rect()
            textPaint.getTextBounds(text, 0, text.length, bounds)
            
            // 绘制文本背景
            canvas.drawRect(
                box.x1,
                box.y1 - bounds.height() - 2 * TEXT_PADDING,
                box.x1 + bounds.width() + 2 * TEXT_PADDING,
                box.y1,
                bgPaint
            )
            
            // 绘制文本
            canvas.drawText(
                text,
                box.x1 + TEXT_PADDING,
                box.y1 - TEXT_PADDING,
                textPaint
            )
        }
        
        return mutable
    }
    
    /**
     * 调整图片大小
     */
    fun resizeBitmap(bitmap: Bitmap, maxWidth: Int, maxHeight: Int): Bitmap {
        val width = bitmap.width
        val height = bitmap.height
        
        val ratioBitmap = width.toFloat() / height.toFloat()
        val ratioMax = maxWidth.toFloat() / maxHeight.toFloat()
        
        var finalWidth = maxWidth
        var finalHeight = maxHeight
        
        if (ratioMax > ratioBitmap) {
            finalWidth = (maxHeight.toFloat() * ratioBitmap).toInt()
        } else {
            finalHeight = (maxWidth.toFloat() / ratioBitmap).toInt()
        }
        
        return Bitmap.createScaledBitmap(bitmap, finalWidth, finalHeight, true)
    }
    
    /**
     * 旋转图片
     */
    fun rotateBitmap(bitmap: Bitmap, degrees: Float): Bitmap {
        val matrix = Matrix()
        matrix.postRotate(degrees)
        return Bitmap.createBitmap(
            bitmap,
            0,
            0,
            bitmap.width,
            bitmap.height,
            matrix,
            true
        )
    }
    
    /**
     * 创建预览图
     */
    fun createThumbnail(bitmap: Bitmap, size: Int): Bitmap {
        return Bitmap.createScaledBitmap(bitmap, size, size, true)
    }
    
    /**
     * 从Uri加载Bitmap
     */
    fun loadBitmapFromUri(context: Context, uri: Uri): Bitmap? {
        return try {
            context.contentResolver.openInputStream(uri)?.use { input ->
                BitmapFactory.decodeStream(input)
            }
        } catch (e: Exception) {
            null
        }
    }
}
