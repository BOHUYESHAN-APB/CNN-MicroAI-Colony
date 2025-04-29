package com.microai.colony.data.model

import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "models")
data class ModelInfo(
    @PrimaryKey
    val id: String,
    val name: String,
    val path: String,
    val type: String, // "pt", "pth", "onnx"等
    val size: Long,
    val importedAt: Long,
    val isActive: Boolean = false,
    val hash: String? = null, // 文件校验值
    val metadata: Map<String, String> = emptyMap() // 额外的模型信息
) {
    companion object {
        val SUPPORTED_TYPES = listOf("pt", "pth", "onnx")
    }
}
