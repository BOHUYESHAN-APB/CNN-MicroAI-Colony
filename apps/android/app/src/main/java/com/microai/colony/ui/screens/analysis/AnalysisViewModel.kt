package com.microai.colony.ui.screens.analysis

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.microai.colony.data.model.DetectionResult
import com.microai.colony.data.repository.ColonyRepository
import com.microai.colony.utils.DateUtils
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch
import java.util.*
import javax.inject.Inject

/**
 * 分析界面状态
 */
data class AnalysisUiState(
    val isLoading: Boolean = false,
    val error: String? = null,
    val statistics: StatisticsData? = null,
    val llmAnalysis: LlmAnalysisData? = null
)

/**
 * 统计数据
 */
data class StatisticsData(
    val totalDetections: Int,
    val averageCount: Float,
    val confidenceDistribution: Map<String, Int>,
    val timeSeriesData: List<TimePoint>
)

/**
 * LLM分析数据
 */
data class LlmAnalysisData(
    val analysis: String,
    val density: Float,
    val distribution: String,
    val recommendations: List<String>
)

/**
 * 时间点数据
 */
data class TimePoint(
    val timestamp: Long,
    val count: Int
)

/**
 * 分析界面ViewModel
 */
@HiltViewModel
class AnalysisViewModel @Inject constructor(
    private val repository: ColonyRepository,
    private val dateUtils: DateUtils
) : ViewModel() {

    private val _uiState = MutableStateFlow(AnalysisUiState(isLoading = true))
    val uiState: StateFlow<AnalysisUiState> = _uiState.asStateFlow()

    init {
        loadData()
    }

    /**
     * 加载数据
     */
    private fun loadData() {
        viewModelScope.launch {
            try {
                repository.getAllDetections()
                    .collect { records ->
                        if (records.isNotEmpty()) {
                            val statistics = calculateStatistics(records)
                            getLlmAnalysis(records)
                            _uiState.update { state ->
                                state.copy(
                                    isLoading = false,
                                    statistics = statistics,
                                    error = null
                                )
                            }
                        } else {
                            _uiState.update { state ->
                                state.copy(
                                    isLoading = false,
                                    statistics = null,
                                    error = null
                                )
                            }
                        }
                    }
            } catch (e: Exception) {
                _uiState.update { state ->
                    state.copy(
                        isLoading = false,
                        error = e.message
                    )
                }
            }
        }
    }

    /**
     * 计算统计数据
     */
    private fun calculateStatistics(records: List<DetectionResult>): StatisticsData {
        // 总数和平均值
        val totalDetections = records.size
        val averageCount = records.map { it.colonyCount }.average().toFloat()

        // 置信度分布
        val confidenceDistribution = records
            .groupBy { getConfidenceLevel(it.confidence) }
            .mapValues { it.value.size }
            .toSortedMap()

        // 时间序列数据
        val timeSeriesData = records
            .groupBy { dateUtils.formatDate(it.timestamp) }
            .map { (_, groupRecords) ->
                TimePoint(
                    timestamp = groupRecords.first().timestamp.time,
                    count = groupRecords.sumOf { it.colonyCount }
                )
            }
            .sortedBy { it.timestamp }

        return StatisticsData(
            totalDetections = totalDetections,
            averageCount = averageCount,
            confidenceDistribution = confidenceDistribution,
            timeSeriesData = timeSeriesData
        )
    }

    /**
     * 获取LLM分析
     */
    private fun getLlmAnalysis(records: List<DetectionResult>) {
        viewModelScope.launch {
            repository.getLlmAnalysis(records)
                .onSuccess { analysis ->
                    _uiState.update { state ->
                        state.copy(
                            llmAnalysis = LlmAnalysisData(
                                analysis = analysis,
                                density = calculateDensity(records),
                                distribution = calculateDistribution(records),
                                recommendations = generateRecommendations(records)
                            )
                        )
                    }
                }
                .onFailure { e ->
                    _uiState.update { state ->
                        state.copy(error = e.message)
                    }
                }
        }
    }

    /**
     * 计算密度
     */
    private fun calculateDensity(records: List<DetectionResult>): Float {
        // 实现密度计算逻辑
        return 0f
    }

    /**
     * 计算分布情况
     */
    private fun calculateDistribution(records: List<DetectionResult>): String {
        // 实现分布计算逻辑
        return ""
    }

    /**
     * 生成建议
     */
    private fun generateRecommendations(records: List<DetectionResult>): List<String> {
        // 实现建议生成逻辑
        return emptyList()
    }

    /**
     * 重试
     */
    fun retry() {
        _uiState.update { it.copy(isLoading = true, error = null) }
        loadData()
    }

    /**
     * 获取置信度等级
     */
    private fun getConfidenceLevel(confidence: Float): String {
        return when {
            confidence >= 0.9f -> "高"
            confidence >= 0.7f -> "中"
            else -> "低"
        }
    }
}
