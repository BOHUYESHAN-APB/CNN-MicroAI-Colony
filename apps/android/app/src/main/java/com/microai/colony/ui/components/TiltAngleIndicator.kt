package com.microai.colony.ui.components

import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.layout.*
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.unit.dp
import kotlin.math.cos
import kotlin.math.sin

/**
 * 倾斜角度指示器
 */
@Composable
fun TiltAngleIndicator(
    angle: Double,
    modifier: Modifier = Modifier
) {
    val isIdealAngle = angle <= 5.0
    val indicatorColor = if (isIdealAngle) {
        MaterialTheme.colorScheme.primary
    } else {
        MaterialTheme.colorScheme.error
    }
    
    val animatedAngle by animateFloatAsState(
        targetValue = angle.toFloat(),
        label = "angle"
    )
    
    Column(
        modifier = modifier,
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        // 角度圆环
        Canvas(
            modifier = Modifier
                .size(80.dp)
                .padding(8.dp)
        ) {
            val center = Offset(size.width / 2, size.height / 2)
            val radius = size.width / 2 - 4.dp.toPx()
            
            // 绘制背景圆环
            drawCircle(
                color = Color.Gray.copy(alpha = 0.2f),
                radius = radius,
                style = androidx.compose.ui.graphics.drawscope.Stroke(
                    width = 4.dp.toPx()
                ),
                center = center
            )
            
            // 绘制角度指示线
            val angleRad = Math.toRadians(animatedAngle.toDouble())
            val endX = center.x + radius * cos(angleRad).toFloat()
            val endY = center.y + radius * sin(angleRad).toFloat()
            
            drawLine(
                color = indicatorColor,
                start = center,
                end = Offset(endX, endY),
                strokeWidth = 4.dp.toPx(),
                cap = StrokeCap.Round
            )
        }
        
        // 角度文本
        Text(
            text = String.format("%.1f°", angle),
            style = MaterialTheme.typography.titleMedium,
            color = indicatorColor
        )
    }
}

/**
 * 拍摄提示
 */
@Composable
fun ShootingHint(
    angle: Double,
    modifier: Modifier = Modifier
) {
    val isIdealAngle = angle <= 5.0
    val (text, color) = if (isIdealAngle) {
        "角度合适" to MaterialTheme.colorScheme.primary
    } else {
        "请调整角度" to MaterialTheme.colorScheme.error
    }
    
    Text(
        text = text,
        style = MaterialTheme.typography.bodyMedium,
        color = color,
        modifier = modifier
    )
}
