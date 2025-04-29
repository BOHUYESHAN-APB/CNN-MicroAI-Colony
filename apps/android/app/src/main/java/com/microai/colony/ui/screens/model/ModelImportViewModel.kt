package com.microai.colony.ui.screens.model

import android.net.Uri
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.microai.colony.data.model.ModelInfo
import com.microai.colony.data.repository.ModelRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class ModelImportViewModel @Inject constructor(
    private val modelRepository: ModelRepository
) : ViewModel() {

    private val _uiState = MutableStateFlow<ModelImportUiState>(ModelImportUiState.Initial)
    val uiState = _uiState.asStateFlow()

    private val _models = MutableStateFlow<List<ModelInfo>>(emptyList())
    val models = _models.asStateFlow()

    init {
        viewModelScope.launch {
            modelRepository.getAllModels().collect {
                _models.value = it
            }
        }
    }

    fun importModel(uri: Uri, name: String) {
        viewModelScope.launch {
            _uiState.value = ModelImportUiState.Loading
            
            modelRepository.importModel(uri, name)
                .onSuccess {
                    _uiState.value = ModelImportUiState.Success(it)
                }
                .onFailure { error ->
                    _uiState.value = ModelImportUiState.Error(error.message ?: "Unknown error")
                }
        }
    }

    fun deleteModel(model: ModelInfo) {
        viewModelScope.launch {
            modelRepository.deleteModel(model)
                .onFailure { error ->
                    _uiState.value = ModelImportUiState.Error(error.message ?: "Failed to delete model")
                }
        }
    }

    fun setActiveModel(modelId: String) {
        viewModelScope.launch {
            try {
                modelRepository.setActiveModel(modelId)
            } catch (e: Exception) {
                _uiState.value = ModelImportUiState.Error(e.message ?: "Failed to set active model")
            }
        }
    }

    fun resetState() {
        _uiState.value = ModelImportUiState.Initial
    }
}

sealed class ModelImportUiState {
    data object Initial : ModelImportUiState()
    data object Loading : ModelImportUiState()
    data class Success(val model: ModelInfo) : ModelImportUiState()
    data class Error(val message: String) : ModelImportUiState()
}
