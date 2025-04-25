package com.microai.colony.utils

import android.content.Context
import android.widget.Toast
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import com.microai.colony.R

/**
 * UI工具类和组件
 */
object UiUtils {
    /**
     * 显示Toast
     */
    fun showToast(context: Context, message: String) {
        Toast.makeText(context, message, Toast.LENGTH_SHORT).show()
    }
    
    /**
     * 显示长Toast
     */
    fun showLongToast(context: Context, message: String) {
        Toast.makeText(context, message, Toast.LENGTH_LONG).show()
    }
}

/**
 * 通用加载中组件
 */
@Composable
fun LoadingScreen(
    modifier: Modifier = Modifier,
    message: String = stringResource(R.string.loading)
) {
    Column(
        modifier = modifier.fillMaxSize(),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        CircularProgressIndicator(
            color = MaterialTheme.colorScheme.primary
        )
        Text(
            text = message,
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurface
        )
    }
}

/**
 * 通用错误显示组件
 */
@Composable
fun ErrorScreen(
    message: String,
    onRetry: () -> Unit
) {
    Column(
        modifier = Modifier.fillMaxSize(),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        Text(
            text = message,
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.error
        )
        androidx.compose.material3.Button(
            onClick = onRetry,
            content = { Text(stringResource(R.string.btn_retry)) }
        )
    }
}

/**
 * 空数据显示组件
 */
@Composable
fun EmptyScreen(
    message: String = stringResource(R.string.no_data)
) {
    Column(
        modifier = Modifier.fillMaxSize(),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        Text(
            text = message,
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )
    }
}

/**
 * 置信度颜色
 */
fun getConfidenceColor(confidence: Float) = when {
    confidence >= 0.9f -> MaterialTheme.colorScheme.primary
    confidence >= 0.7f -> MaterialTheme.colorScheme.secondary
    else -> MaterialTheme.colorScheme.error
}

/**
 * 置信度文本
 */
fun getConfidenceText(confidence: Float) = when {
    confidence >= 0.9f -> "高"
    confidence >= 0.7f -> "中"
    else -> "低"
}
