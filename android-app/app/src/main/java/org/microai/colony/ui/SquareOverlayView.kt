package com.bohuyshan.microai.colony.ui

import android.content.Context
import android.graphics.Canvas
import android.graphics.Paint
import android.graphics.RectF
import android.util.AttributeSet
import android.view.View
import androidx.core.content.ContextCompat
import com.bohuyshan.microai.colony.R

/**
 * Displays a centered square overlay to guide the user for model input cropping.
 */
class SquareOverlayView @JvmOverloads constructor(
    context: Context,
    attrs: AttributeSet? = null,
    defStyleAttr: Int = 0
) : View(context, attrs, defStyleAttr) {

    private val framePaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = ContextCompat.getColor(context, R.color.colorSecondary)
        style = Paint.Style.STROKE
        strokeWidth = resources.displayMetrics.density * 2
    }
    private val dimPaint = Paint().apply {
        color = ContextCompat.getColor(context, android.R.color.black)
        alpha = 80
    }
    private val squareRect = RectF()

    override fun onSizeChanged(w: Int, h: Int, oldw: Int, oldh: Int) {
        super.onSizeChanged(w, h, oldw, oldh)
        updateSquareRect(w, h)
    }

    override fun onDraw(canvas: Canvas) {
        super.onDraw(canvas)
        if (squareRect.isEmpty) return

        // Dim outside region
        canvas.drawRect(0f, 0f, width.toFloat(), squareRect.top, dimPaint)
        canvas.drawRect(0f, squareRect.bottom, width.toFloat(), height.toFloat(), dimPaint)
        canvas.drawRect(0f, squareRect.top, squareRect.left, squareRect.bottom, dimPaint)
        canvas.drawRect(squareRect.right, squareRect.top, width.toFloat(), squareRect.bottom, dimPaint)

        // Draw square frame
        canvas.drawRect(squareRect, framePaint)
    }

    fun getSquareRect(): RectF = RectF(squareRect)

    fun getSquareRectNormalized(): RectF {
        if (width == 0 || height == 0 || squareRect.isEmpty) return RectF(0f, 0f, 1f, 1f)
        return RectF(
            squareRect.left / width,
            squareRect.top / height,
            squareRect.right / width,
            squareRect.bottom / height
        )
    }

    private fun updateSquareRect(w: Int, h: Int) {
        if (w == 0 || h == 0) {
            squareRect.setEmpty()
            return
        }
        val size = minOf(w, h)
        val left = (w - size) / 2f
        val top = (h - size) / 2f
        squareRect.set(left, top, left + size, top + size)
        invalidate()
    }
}
