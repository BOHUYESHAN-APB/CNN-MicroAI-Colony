package com.microai.colony.data.model

import androidx.room.Entity
import androidx.room.PrimaryKey
import java.util.Date

/**
 * 检测结果数据模型
 */
@Entity(tableName = "detection_results")
data class DetectionResult(
    @PrimaryKey(autoGenerate = true)
    val id: Long = 0,
    
    // 基础信息
    val imageUri: String,
    val timestamp: Date,
    val isSynced: Boolean = false,
    
    // 检测结果
    val colonyCount: Int,
    val confidence: Float,
    val boxes: List<Box>,
    
    // 分析结果
    val density: Float? = null,
    val distribution: String? = null,
    val llmAnalysis: String? = null
) {
    /**
     * 检测框数据类
     */
    data class Box(
        val x1: Float,
        val y1: Float,
        val x2: Float,
        val y2: Float,
        val confidence: Float
    )
    
    /**
     * 获取置信度等级
     */
    fun getConfidenceLevel(): ConfidenceLevel {
        return when {
            confidence >= 0.9f -> ConfidenceLevel.HIGH
            confidence >= 0.7f -> ConfidenceLevel.MEDIUM
            else -> ConfidenceLevel.LOW
        }
    }
}

/**
 * 置信度等级
 */
enum class ConfidenceLevel {
    HIGH,
    MEDIUM,
    LOW
}
