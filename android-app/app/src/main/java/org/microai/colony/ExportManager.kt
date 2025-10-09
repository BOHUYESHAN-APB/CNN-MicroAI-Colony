package com.bohuyshan.microai.colony

import android.content.Context
import android.graphics.BitmapFactory
import android.graphics.Paint
import android.graphics.RectF
import android.graphics.Typeface
import android.graphics.pdf.PdfDocument
import java.io.File
import java.io.FileOutputStream
import java.io.IOException
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

object ExportManager {
    private val dateFormatter = SimpleDateFormat("yyyy-MM-dd HH:mm:ss", Locale.getDefault())

    fun exportPdf(context: Context, projectName: String): File? {
        val entries = DetectionHistory.load(context, projectName)
        if (entries.isEmpty()) {
            LogManager.log("PDF export skipped: no detection history for $projectName")
            return null
        }
        val albumDir = ProjectRepository.getProjectAlbumDir(context, projectName)
        val reportDir = File(albumDir, "reports").apply { if (!exists()) mkdirs() }
        val outFile = File(reportDir, "report_${System.currentTimeMillis()}.pdf")
        val pdf = PdfDocument()
        val pageWidth = 595
        val pageHeight = 842
        val padding = 32f
        val titlePaint = Paint().apply {
            textSize = 20f
            isAntiAlias = true
            typeface = Typeface.create(Typeface.DEFAULT, Typeface.BOLD)
        }
        val bodyPaint = Paint().apply {
            textSize = 14f
            isAntiAlias = true
        }
        entries.forEachIndexed { index, entry ->
            val pageInfo = PdfDocument.PageInfo.Builder(pageWidth, pageHeight, index + 1).create()
            val page = pdf.startPage(pageInfo)
            val canvas = page.canvas
            var cursorY = padding
            val title = context.getString(R.string.export_pdf_project_title, projectName)
            canvas.drawText(title, padding, cursorY, titlePaint)
            cursorY += titlePaint.textSize + 12f

            val infoLines = listOf(
                context.getString(R.string.export_pdf_source_image, entry.sourceFileName),
                context.getString(R.string.export_pdf_annotated_image, entry.annotatedFileName),
                context.getString(R.string.export_pdf_detected_at, dateFormatter.format(Date(entry.timestamp))),
                context.getString(R.string.export_pdf_detection_count, entry.detectionCount),
                context.getString(R.string.export_pdf_threshold_nms, entry.threshold, entry.nms),
                if (entry.usedFallback) {
                    context.getString(R.string.export_pdf_used_full_image)
                } else {
                    context.getString(R.string.export_pdf_used_cropped)
                }
            )
            infoLines.forEach { line ->
                canvas.drawText(line, padding, cursorY, bodyPaint)
                cursorY += bodyPaint.textSize + 8f
            }
            cursorY += 8f

            val imageFile = File(albumDir, entry.annotatedFileName)
            if (imageFile.exists()) {
                val bitmap = BitmapFactory.decodeFile(imageFile.absolutePath)
                if (bitmap != null) {
                    val maxWidth = pageWidth - (padding * 2)
                    val maxHeight = pageHeight - cursorY - 120f
                    val scale = minOf(maxWidth / bitmap.width.toFloat(), maxHeight / bitmap.height.toFloat(), 1f)
                    val dest = RectF(
                        padding,
                        cursorY,
                        padding + bitmap.width * scale,
                        cursorY + bitmap.height * scale
                    )
                    canvas.drawBitmap(bitmap, null, dest, null)
                    cursorY = dest.bottom + 16f
                    bitmap.recycle()
                } else {
                    canvas.drawText(context.getString(R.string.export_pdf_warn_decode, entry.annotatedFileName), padding, cursorY, bodyPaint)
                    cursorY += bodyPaint.textSize + 8f
                }
            } else {
                canvas.drawText(context.getString(R.string.export_pdf_warn_missing, entry.annotatedFileName), padding, cursorY, bodyPaint)
                cursorY += bodyPaint.textSize + 8f
            }

            if (entry.detections.isNotEmpty()) {
                canvas.drawText(context.getString(R.string.export_pdf_detections_heading), padding, cursorY, bodyPaint)
                cursorY += bodyPaint.textSize + 8f
                entry.detections.take(10).forEach { det ->
                    val line = String.format(
                        Locale.getDefault(),
                        "%.2f  %.0f,%.0f,%.0f,%.0f",
                        det.score,
                        det.left,
                        det.top,
                        det.right,
                        det.bottom
                    )
                    canvas.drawText(line, padding, cursorY, bodyPaint)
                    cursorY += bodyPaint.textSize + 6f
                }
                if (entry.detections.size > 10) {
                    canvas.drawText(
                        context.getString(R.string.export_pdf_detections_omitted, entry.detections.size - 10),
                        padding,
                        cursorY,
                        bodyPaint
                    )
                }
            }
            pdf.finishPage(page)
        }
        try {
            FileOutputStream(outFile).use { pdf.writeTo(it) }
        } catch (ioe: IOException) {
            LogManager.logError("Failed to write PDF export", ioe)
            pdf.close()
            outFile.delete()
            return null
        }
        pdf.close()
    LogManager.log("PDF export completed: ${outFile.absolutePath}")
        return outFile
    }

    fun exportCsv(context: Context, projectName: String): File? {
        val entries = DetectionHistory.load(context, projectName)
        if (entries.isEmpty()) {
            LogManager.log("CSV export skipped: no detection history for $projectName")
            return null
        }
        val albumDir = ProjectRepository.getProjectAlbumDir(context, projectName)
        val reportDir = File(albumDir, "reports").apply { if (!exists()) mkdirs() }
        val outFile = File(reportDir, "report_${System.currentTimeMillis()}.csv")
        val header = listOf(
            "source",
            "annotated",
            "timestamp",
            "datetime",
            "detections",
            "threshold",
            "nms",
            "used_fallback",
            "boxes"
        )
        val builder = StringBuilder()
        builder.appendLine(header.joinToString(",") { csvEscape(it) })
        entries.forEach { entry ->
            val boxes = entry.detections.joinToString(" | ") { det ->
                String.format(
                    Locale.getDefault(),
                    "%.2f:[%.0f,%.0f,%.0f,%.0f]",
                    det.score,
                    det.left,
                    det.top,
                    det.right,
                    det.bottom
                )
            }
            val row = listOf(
                entry.sourceFileName,
                entry.annotatedFileName,
                entry.timestamp.toString(),
                dateFormatter.format(Date(entry.timestamp)),
                entry.detectionCount.toString(),
                String.format(Locale.getDefault(), "%.2f", entry.threshold),
                String.format(Locale.getDefault(), "%.2f", entry.nms),
                entry.usedFallback.toString(),
                boxes
            ).joinToString(",") { csvEscape(it) }
            builder.appendLine(row)
        }
        return try {
            outFile.writeText(builder.toString())
            LogManager.log("CSV export completed: ${outFile.absolutePath}")
            outFile
        } catch (ioe: IOException) {
            LogManager.logError("Failed to write CSV export", ioe)
            null
        }
    }

    private fun csvEscape(value: String): String {
        val escaped = value.replace("\"", "\"\"")
        return "\"$escaped\""
    }
}
