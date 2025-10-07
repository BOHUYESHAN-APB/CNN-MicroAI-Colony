package org.microai.colony

import android.content.Context
import android.graphics.Bitmap
import android.graphics.Canvas
import android.graphics.Paint
import android.graphics.RectF
import ai.onnxruntime.OnnxTensor
import ai.onnxruntime.OrtEnvironment
import ai.onnxruntime.OrtSession
import java.nio.FloatBuffer
import java.io.File
import java.io.FileOutputStream
import kotlin.math.max
import kotlin.math.min

object OnnxHelper {
    private var ortEnv: OrtEnvironment? = null
    private var ortSession: OrtSession? = null

    fun init(ctx: Context) {
        try {
            ortEnv = ortEnv ?: OrtEnvironment.getEnvironment()
            val modelStream = ctx.assets.open("model.onnx")
            val tmp = File(ctx.cacheDir, "model.onnx")
            modelStream.use { input -> tmp.outputStream().use { output -> input.copyTo(output) } }
            val options = OrtSession.SessionOptions()
            ortSession = ortEnv!!.createSession(tmp.absolutePath, options)
        } catch (e: Exception) {
            e.printStackTrace()
        }
    }
    fun runInferenceAndAnnotate(ctx: Context, imgFile: File): Bitmap? {
        // keep for backward compatibility
        return try {
            runInferenceAndSavePath(ctx, imgFile)?.let { path ->
                android.graphics.BitmapFactory.decodeFile(path)
            }
        } catch (e: Exception) {
            e.printStackTrace(); null
        }
    }

    // New API: threshold and nmsIoU are float in [0,1]. Provide defaults for backward compatibility.
    fun runInferenceAndSavePath(ctx: Context, imgFile: File, threshold: Float = 0.45f, nmsIoU: Float = 0.3f): String? {
        try {
            val bmp = android.graphics.BitmapFactory.decodeFile(imgFile.absolutePath)
            val resized = Bitmap.createScaledBitmap(bmp, 800, 800, true)
            val input = bitmapToFloatBuffer(resized)
            val inputName = ortSession!!.inputNames.iterator().next()
            val shape = longArrayOf(1,3,800,800)
            input.rewind()
            val tensor = OnnxTensor.createTensor(ortEnv!!, input, shape)
            val results = ortSession!!.run(mapOf(inputName to tensor))
            val boxes = (results[0].value as Array<*>)[0] as Array<FloatArray>
            val scores = (results[2].value as Array<*>)[0] as FloatArray
            // simple threshold and NMS
            val inds = scores.indices.filter { scores[it] > threshold }
            val selected = mutableListOf<Int>()
            for (i in inds) {
                var keep = true
                for (j in selected) {
                    if (iou(boxes[i], boxes[j]) > nmsIoU) { keep = false; break }
                }
                if (keep) selected.add(i)
            }
            val outBmp = bmp.copy(Bitmap.Config.ARGB_8888, true)
            val canvas = Canvas(outBmp)
            val paint = Paint().apply { color = android.graphics.Color.RED; style = Paint.Style.STROKE; strokeWidth = 6f }
            val textPaint = Paint().apply { color = android.graphics.Color.RED; textSize = 36f }
            for (i in selected) {
                val b = boxes[i]
                val left = (b[0] * bmp.width / 800.0f).toFloat()
                val top = (b[1] * bmp.height / 800.0f).toFloat()
                val right = (b[2] * bmp.width / 800.0f).toFloat()
                val bottom = (b[3] * bmp.height / 800.0f).toFloat()
                canvas.drawRect(RectF(left, top, right, bottom), paint)
                canvas.drawText(String.format("%.2f", scores[i]), left, top - 6f, textPaint)
            }
            // save to app-specific album folder
            val dir = File(ctx.filesDir, "album")
            if (!dir.exists()) dir.mkdirs()
            val outFile = File(dir, "annot_${System.currentTimeMillis()}.jpg")
            FileOutputStream(outFile).use { out -> outBmp.compress(Bitmap.CompressFormat.JPEG, 90, out) }
            return outFile.absolutePath
        } catch (e: Exception) {
            e.printStackTrace()
            return null
        }
    }

    private fun bitmapToFloatBuffer(bmp: Bitmap): FloatBuffer {
        val wh = bmp.width * bmp.height
        val pixels = IntArray(wh)
        bmp.getPixels(pixels, 0, bmp.width, 0, 0, bmp.width, bmp.height)
        val buffer = FloatBuffer.allocate(3 * wh)
        for (y in 0 until bmp.height) {
            for (x in 0 until bmp.width) {
                val c = pixels[y * bmp.width + x]
                val r = ((c shr 16) and 0xFF) / 255.0f
                val g = ((c shr 8) and 0xFF) / 255.0f
                val b = (c and 0xFF) / 255.0f
                // normalize
                buffer.put((r - 0.485f) / 0.229f)
                buffer.put((g - 0.456f) / 0.224f)
                buffer.put((b - 0.406f) / 0.225f)
            }
        }
        buffer.rewind()
        return buffer
    }

    private fun iou(a: FloatArray, b: FloatArray): Float {
        val xA = max(a[0], b[0]); val yA = max(a[1], b[1])
        val xB = min(a[2], b[2]); val yB = min(a[3], b[3])
        val interW = max(0f, xB - xA); val interH = max(0f, yB - yA)
        val inter = interW * interH
        val areaA = max(0f, a[2]-a[0]) * max(0f, a[3]-a[1])
        val areaB = max(0f, b[2]-b[0]) * max(0f, b[3]-b[1])
        val denom = areaA + areaB - inter
        return if (denom > 0f) inter / denom else 0f
    }
}
