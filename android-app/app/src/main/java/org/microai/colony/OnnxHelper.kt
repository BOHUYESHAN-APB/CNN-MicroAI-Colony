package com.bohuyshan.microai.colony

import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.Canvas
import android.graphics.Paint
import android.graphics.RectF
import android.os.Build
import ai.onnxruntime.OnnxTensor
import ai.onnxruntime.OrtEnvironment
import ai.onnxruntime.OrtSession
import java.nio.FloatBuffer
import java.io.File
import java.io.FileOutputStream
import kotlin.math.max
import kotlin.math.min

data class DetectionResult(val score: Float, val bounds: RectF)

data class InferenceResult(val annotatedPath: String, val detections: List<DetectionResult>)

object OnnxHelper {
    private var ortEnv: OrtEnvironment? = null
    private var ortSession: OrtSession? = null

    fun init(ctx: Context): Boolean {
        return try {
            val supportedAbis = Build.SUPPORTED_ABIS.joinToString()
            LogManager.log("Device supported ABIs: $supportedAbis")
            if (Build.SUPPORTED_ABIS.none { it.contains("arm64") }) {
                LogManager.log("arm64 ABI not present; skipping ONNX initialization")
                return false
            }
            if (ortEnv == null) {
                ortEnv = OrtEnvironment.getEnvironment()
                LogManager.log("ORT environment created")
            }
            val modelStream = ctx.assets.open("model.onnx")
            val tmp = File(ctx.cacheDir, "model.onnx")
            modelStream.use { input -> tmp.outputStream().use { output -> input.copyTo(output) } }
            val options = OrtSession.SessionOptions()
            ortSession = ortEnv!!.createSession(tmp.absolutePath, options)
            LogManager.log("ONNX model session loaded from assets/model.onnx")
            true
        } catch (t: Throwable) {
            t.printStackTrace()
            ortSession = null
            LogManager.logError("Failed to initialize ONNX runtime", t)
            false
        }
    }
    fun runInferenceAndAnnotate(ctx: Context, imgFile: File): Bitmap? {
        // keep for backward compatibility
        return try {
            LogManager.log("runInferenceAndAnnotate invoked for ${imgFile.absolutePath}")
            runInferenceAndSavePath(ctx, imgFile)?.let { result ->
                BitmapFactory.decodeFile(result.annotatedPath)
            }
        } catch (e: Exception) {
            e.printStackTrace(); null
        }
    }

    // New API: threshold and nmsIoU are float in [0,1]. Provide defaults for backward compatibility.
    fun runInferenceAndSavePath(ctx: Context, imgFile: File, threshold: Float = 0.45f, nmsIoU: Float = 0.3f): InferenceResult? {
        try {
            val session = ortSession
            val env = ortEnv
            if (session == null || env == null) {
                LogManager.logError("Inference attempted before ONNX runtime initialized", IllegalStateException("ORT session not ready"))
                return null
            }
            LogManager.log("Preparing inference for ${imgFile.absolutePath}")
            val bmp = android.graphics.BitmapFactory.decodeFile(imgFile.absolutePath)
            val resized = Bitmap.createScaledBitmap(bmp, 800, 800, true)
            val input = bitmapToFloatBuffer(resized)
            val inputName = session.inputNames.iterator().next()
            val shape = longArrayOf(1, 3, 800, 800)
            val tensor = OnnxTensor.createTensor(env, input, shape)
            val boxes: Array<FloatArray>
            val scores: FloatArray
            tensor.use { t ->
                session.run(mapOf(inputName to t)).use { result ->
                    boxes = (result[0].value as Array<*>)[0] as Array<FloatArray>
                    scores = (result[2].value as Array<*>)[0] as FloatArray
                }
            }

            val inds = scores.indices.filter { scores[it] > threshold }
                .sortedByDescending { scores[it] }
            val selected = mutableListOf<Int>()
            for (i in inds) {
                var keep = true
                for (j in selected) {
                    if (iou(boxes[i], boxes[j]) > nmsIoU) {
                        keep = false
                        break
                    }
                }
                if (keep) selected.add(i)
            }
            val outBmp = bmp.copy(Bitmap.Config.ARGB_8888, true)
            val canvas = Canvas(outBmp)
            val paint = Paint().apply { color = android.graphics.Color.RED; style = Paint.Style.STROKE; strokeWidth = 6f }
            val textPaint = Paint().apply { color = android.graphics.Color.RED; textSize = 36f }
            val detections = mutableListOf<DetectionResult>()
            for (i in selected) {
                val b = boxes[i]
                val left = (b[0] * bmp.width / 800.0f).toFloat()
                val top = (b[1] * bmp.height / 800.0f).toFloat()
                val right = (b[2] * bmp.width / 800.0f).toFloat()
                val bottom = (b[3] * bmp.height / 800.0f).toFloat()
                val rect = RectF(left, top, right, bottom)
                canvas.drawRect(rect, paint)
                canvas.drawText(String.format("%.2f", scores[i]), left, top - 6f, textPaint)
                detections.add(DetectionResult(scores[i], rect))
            }
            // save to app-specific album folder
            val projectName = ProjectRepository.getCurrentProject(ctx)
            val dir = ProjectRepository.getProjectAlbumDir(ctx, projectName)
            val outFile = File(dir, "annot_${System.currentTimeMillis()}.jpg")
            FileOutputStream(outFile).use { out -> outBmp.compress(Bitmap.CompressFormat.JPEG, 90, out) }
            LogManager.log("Inference output saved to ${outFile.absolutePath} with ${detections.size} boxes (project=$projectName)")
            if (resized != bmp) {
                resized.recycle()
            }
            bmp.recycle()
            return InferenceResult(outFile.absolutePath, detections)
        } catch (e: Exception) {
            e.printStackTrace()
            LogManager.logError("Inference error for ${imgFile.absolutePath}", e)
            return null
        }
    }

    private fun bitmapToFloatBuffer(bmp: Bitmap): FloatBuffer {
        val width = bmp.width
        val height = bmp.height
        val pixelCount = width * height
        val pixels = IntArray(pixelCount)
        bmp.getPixels(pixels, 0, width, 0, 0, width, height)
        val floatValues = FloatArray(3 * pixelCount)
        val offsetG = pixelCount
        val offsetB = 2 * pixelCount
        for (y in 0 until height) {
            for (x in 0 until width) {
                val idx = y * width + x
                val c = pixels[idx]
                val r = ((c shr 16) and 0xFF) / 255.0f
                val g = ((c shr 8) and 0xFF) / 255.0f
                val b = (c and 0xFF) / 255.0f
                floatValues[idx] = (r - 0.485f) / 0.229f
                floatValues[offsetG + idx] = (g - 0.456f) / 0.224f
                floatValues[offsetB + idx] = (b - 0.406f) / 0.225f
            }
        }
        return FloatBuffer.wrap(floatValues)
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
