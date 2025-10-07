package org.microai.colony

import android.content.Context
import android.graphics.Bitmap
import android.graphics.Canvas
import android.graphics.Paint
import android.graphics.RectF
import org.json.JSONObject
import java.io.File
import java.nio.ByteBuffer
import java.nio.ByteOrder
import kotlin.math.max
import kotlin.math.min

object OnnxHelper {
    private var session: org.tensorflow.lite.nnapi.ExperimentalNnApi? = null
    private var ortSession: com.microsoft.onnxruntime.OrtSession? = null

    fun init(ctx: Context) {
        try {
            val env = com.microsoft.onnxruntime.OrtEnvironment.getEnvironment()
            val modelStream = ctx.assets.open("model.onnx")
            val tmp = File(ctx.cacheDir, "model.onnx")
            modelStream.use { input -> tmp.outputStream().use { output -> input.copyTo(output) } }
            ortSession = com.microsoft.onnxruntime.OrtEnvironment.getEnvironment().createSession(tmp.absolutePath, com.microsoft.onnxruntime.OrtSession.SessionOptions())
        } catch (e: Exception) {
            e.printStackTrace()
        }
    }

    fun runInferenceAndAnnotate(ctx: Context, imgFile: File): Bitmap? {
        try {
            val bmp = android.graphics.BitmapFactory.decodeFile(imgFile.absolutePath)
            val resized = Bitmap.createScaledBitmap(bmp, 800, 800, true)
            val input = bitmapToFloatBuffer(resized)
            val inputName = ortSession!!.inputNames.iterator().next()
            val shape = longArrayOf(1,3,800,800)
            val tensor = com.microsoft.onnxruntime.OnnxTensor.createTensor(com.microsoft.onnxruntime.OrtEnvironment.getEnvironment(), input, shape)
            val results = ortSession!!.run(mapOf(inputName to tensor))
            val boxes = (results[0].value as Array<*>)[0] as Array<FloatArray>
            val scores = (results[2].value as Array<*>)[0] as FloatArray
            // simple threshold and NMS
            val inds = scores.indices.filter { scores[it] > 0.45f }
            val selected = mutableListOf<Int>()
            for (i in inds) {
                var keep = true
                for (j in selected) {
                    if (iou(boxes[i], boxes[j]) > 0.3f) { keep = false; break }
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
            return outBmp
        } catch (e: Exception) {
            e.printStackTrace()
            return null
        }
    }

    private fun bitmapToFloatBuffer(bmp: Bitmap): FloatArray {
        val wh = bmp.width * bmp.height
        val pixels = IntArray(wh)
        bmp.getPixels(pixels, 0, bmp.width, 0, 0, bmp.width, bmp.height)
        val floatBuf = FloatArray(3 * wh)
        var idx = 0
        for (y in 0 until bmp.height) {
            for (x in 0 until bmp.width) {
                val c = pixels[y * bmp.width + x]
                val r = ((c shr 16) and 0xFF) / 255.0f
                val g = ((c shr 8) and 0xFF) / 255.0f
                val b = (c and 0xFF) / 255.0f
                // normalize
                floatBuf[idx++] = (r - 0.485f) / 0.229f
                floatBuf[idx++] = (g - 0.456f) / 0.224f
                floatBuf[idx++] = (b - 0.406f) / 0.225f
            }
        }
        return floatBuf
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
