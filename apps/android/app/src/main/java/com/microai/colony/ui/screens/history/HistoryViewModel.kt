package com.microai.colony.ui.screens.history

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
 * 历史界面状态
 */
data class HistoryUiState(
    val records: List<DetectionResult> = emptyList(),
    val isLoading: Boolean = false,
    val error: String? = null,
    val selectedFilter: TimeFilter = TimeFilter.ALL
)

/**
 * 历史界面ViewModel
 */
@HiltViewModel
class HistoryViewModel @Inject constructor(
    private val repository: ColonyRepository,
    private val dateUtils: DateUtils
) : ViewModel() {

    private val _uiState = MutableStateFlow(HistoryUiState(isLoading = true))
    val uiState: StateFlow<HistoryUiState> = _uiState.asStateFlow()

    init {
        loadRecords()
    }

    /**
     * 加载记录
     */
    private fun loadRecords() {
        viewModelScope.launch {
            repository.getAllDetections()
                .catch { e ->
                    _uiState.update { state ->
                        state.copy(
                            isLoading = false,
                            error = e.message
                        )
                    }
                }
                .collect { records ->
                    val filteredRecords = filterRecords(records, _uiState.value.selectedFilter)
                    _uiState.update { state ->
                        state.copy(
                            records = filteredRecords,
                            isLoading = false,
                            error = null
                        )
                    }
                }
        }
    }

    /**
     * 设置时间筛选
     */
    fun setFilter(filter: TimeFilter) {
        _uiState.update { state ->
            state.copy(selectedFilter = filter)
        }
        loadRecords()
    }

    /**
     * 删除记录
     */
    fun deleteRecord(record: DetectionResult) {
        viewModelScope.launch {
            repository.deleteDetection(record)
                .onSuccess {
                    loadRecords()
                }
                .onFailure { e ->
                    _uiState.update { state ->
                        state.copy(error = e.message)
                    }
                }
        }
    }

    /**
     * 清除错误
     */
    fun clearError() {
        _uiState.update { it.copy(error = null) }
    }

    /**
     * 重试
     */
    fun retry() {
        _uiState.update { it.copy(isLoading = true, error = null) }
        loadRecords()
    }

    /**
     * 根据时间筛选记录
     */
    private fun filterRecords(records: List<DetectionResult>, filter: TimeFilter): List<DetectionResult> {
        val startTime = when (filter) {
            TimeFilter.ALL -> null
            TimeFilter.TODAY -> dateUtils.getTodayStart()
            TimeFilter.WEEK -> dateUtils.getWeekStart()
            TimeFilter.MONTH -> dateUtils.getMonthStart()
        }

        return if (startTime != null) {
            records.filter { it.timestamp.after(startTime) }
        } else {
            records
        }
    }

    override fun onCleared() {
        super.onCleared()
    }
}
