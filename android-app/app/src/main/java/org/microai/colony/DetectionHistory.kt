package com.bohuyshan.microai.colony

import android.content.Context
import org.json.JSONArray
import org.json.JSONObject
import java.io.File
import java.io.IOException
import java.util.UUID

object DetectionHistory {
    private const val HISTORY_FILE = "inference_history.json"

    data class DetectionDetail(
        val score: Float,
        val left: Float,
        val top: Float,
        val right: Float,
        val bottom: Float
    ) {
        fun toJson(): JSONObject = JSONObject().apply {
            put("score", score)
            put("left", left)
            put("top", top)
            put("right", right)
            put("bottom", bottom)
        }

        companion object {
            fun fromJson(obj: JSONObject): DetectionDetail = DetectionDetail(
                score = obj.optDouble("score", 0.0).toFloat(),
                left = obj.optDouble("left", 0.0).toFloat(),
                top = obj.optDouble("top", 0.0).toFloat(),
                right = obj.optDouble("right", 0.0).toFloat(),
                bottom = obj.optDouble("bottom", 0.0).toFloat()
            )
        }
    }

    data class DetectionEntry(
        val id: String = UUID.randomUUID().toString(),
        val timestamp: Long,
        val projectName: String,
        val sourceFileName: String,
        val annotatedFileName: String,
        val threshold: Float,
        val nms: Float,
        val usedFallback: Boolean,
        val detections: List<DetectionDetail>
    ) {
        val detectionCount: Int
            get() = detections.size

        fun toJson(): JSONObject = JSONObject().apply {
            put("id", id)
            put("timestamp", timestamp)
            put("project", projectName)
            put("source", sourceFileName)
            put("annotated", annotatedFileName)
            put("threshold", threshold)
            put("nms", nms)
            put("fallback", usedFallback)
            put("detections", JSONArray().apply {
                detections.forEach { put(it.toJson()) }
            })
        }

        companion object {
            fun fromJson(obj: JSONObject): DetectionEntry = DetectionEntry(
                id = obj.optString("id", UUID.randomUUID().toString()),
                timestamp = obj.optLong("timestamp", System.currentTimeMillis()),
                projectName = obj.optString("project", ProjectRepository.DEFAULT_PROJECT_NAME),
                sourceFileName = obj.optString("source", ""),
                annotatedFileName = obj.optString("annotated", ""),
                threshold = obj.optDouble("threshold", 0.0).toFloat(),
                nms = obj.optDouble("nms", 0.0).toFloat(),
                usedFallback = obj.optBoolean("fallback", false),
                detections = obj.optJSONArray("detections")?.let { arr ->
                    buildList {
                        for (i in 0 until arr.length()) {
                            val det = arr.optJSONObject(i) ?: continue
                            add(DetectionDetail.fromJson(det))
                        }
                    }
                } ?: emptyList()
            )
        }
    }

    @Synchronized
    fun record(context: Context, entry: DetectionEntry) {
        val storage = historyFile(context, entry.projectName)
        val array = if (storage.exists()) {
            try {
                JSONArray(storage.readText())
            } catch (_: Exception) {
                JSONArray()
            }
        } else {
            JSONArray()
        }
        array.put(entry.toJson())
        try {
            storage.writeText(array.toString())
        } catch (ioe: IOException) {
            LogManager.logError("Failed to persist detection history", ioe)
        }
    }

    @Synchronized
    fun load(context: Context, projectName: String): List<DetectionEntry> {
        val storage = historyFile(context, projectName)
        if (!storage.exists()) return emptyList()
        return try {
            val arr = JSONArray(storage.readText())
            buildList {
                for (i in 0 until arr.length()) {
                    val obj = arr.optJSONObject(i) ?: continue
                    add(DetectionEntry.fromJson(obj))
                }
            }.sortedBy { it.timestamp }
        } catch (e: Exception) {
            LogManager.logError("Failed to read detection history", e)
            emptyList()
        }
    }

    @Synchronized
    fun clearProject(context: Context, projectName: String) {
        val storage = historyFile(context, projectName)
        if (storage.exists()) {
            storage.delete()
        }
    }

    private fun historyFile(context: Context, projectName: String): File {
        val dir = ProjectRepository.getProjectAlbumDir(context, projectName)
        return File(dir, HISTORY_FILE)
    }
}
