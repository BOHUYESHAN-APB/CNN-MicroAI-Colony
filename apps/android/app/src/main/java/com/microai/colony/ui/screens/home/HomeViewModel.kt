package com.microai.colony.ui.screens.home

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.microai.colony.data.model.DetectionResult
import com.microai.colony.data.repository.ColonyRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch
import javax.inject.Inject

/**
 * 主页状态
 */
data class HomeUiState(
    val recentRecords: List<DetectionResult> = emptyList(),
    val isLoading: Boolean = false,
    val error: String? = null
)

/**
 * 主页ViewModel
 */
@HiltViewModel
class HomeViewModel @Inject constructor(
    private val repository: ColonyRepository
) : ViewModel() {
    
    private val _uiState = MutableStateFlow(HomeUiState(isLoading = true))
    val uiState: StateFlow<HomeUiState> = _uiState.asStateFlow()
    
    init {
        loadRecentRecords()
    }
    
    /**
     * 加载最近记录
     */
    private fun loadRecentRecords() {
        viewModelScope.launch {
            repository.getRecentDetections()
                .catch { e ->
                    _uiState.update { state ->
                        state.copy(
                            isLoading = false,
                            error = e.message
                        )
                    }
                }
                .collect { records ->
                    _uiState.update { state ->
                        state.copy(
                            recentRecords = records,
                            isLoading = false,
                            error = null
                        )
                    }
                }
        }
    }
    
    /**
     * 刷新数据
     */
    fun refresh() {
        _uiState.update { it.copy(isLoading = true) }
        loadRecentRecords()
    }
    
    /**
     * 清除错误
     */
    fun clearError() {
        _uiState.update { it.copy(error = null) }
    }
    
    /**
     * 删除记录
     */
    fun deleteRecord(record: DetectionResult) {
        viewModelScope.launch {
            repository.deleteDetection(record)
                .onSuccess {
                    // 刷新列表
                    loadRecentRecords()
                }
                .onFailure { e ->
                    _uiState.update { state ->
                        state.copy(error = e.message)
                    }
                }
        }
    }
}
