package com.microai.colony.ui.screens.settings

import android.content.Context
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.microai.colony.data.repository.ColonyRepository
import com.microai.colony.utils.FileUtils
import dagger.hilt.android.lifecycle.HiltViewModel
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch
import javax.inject.Inject

/**
 * 设置界面状态
 */
data class SettingsUiState(
    val theme: Theme = Theme.SYSTEM,
    val language: Language = Language.SYSTEM,
    val storageUsage: Double = 0.0,
    val versionName: String = "1.0.0"
)

/**
 * 主题选项
 */
enum class Theme(val displayName: String) {
    SYSTEM("跟随系统"),
    LIGHT("浅色"),
    DARK("深色")
}

/**
 * 语言选项
 */
enum class Language(val displayName: String, val code: String) {
    SYSTEM("跟随系统", ""),
    CHINESE("简体中文", "zh"),
    ENGLISH("English", "en")
}

/**
 * 设置界面ViewModel
 */
@HiltViewModel
class SettingsViewModel @Inject constructor(
    @ApplicationContext private val context: Context,
    private val repository: ColonyRepository,
    private val fileUtils: FileUtils,
    private val dataStore: SettingsDataStore
) : ViewModel() {

    private val _uiState = MutableStateFlow(SettingsUiState())
    val uiState: StateFlow<SettingsUiState> = _uiState.asStateFlow()

    init {
        loadSettings()
        calculateStorageUsage()
    }

    /**
     * 加载设置
     */
    private fun loadSettings() {
        viewModelScope.launch {
            dataStore.getSettings().collect { settings ->
                _uiState.update { state ->
                    state.copy(
                        theme = settings.theme,
                        language = settings.language,
                        versionName = context.packageManager
                            .getPackageInfo(context.packageName, 0)
                            .versionName
                    )
                }
            }
        }
    }

    /**
     * 计算存储使用量
     */
    private fun calculateStorageUsage() {
        viewModelScope.launch {
            try {
                val totalSize = getTotalStorageSize()
                _uiState.update { it.copy(storageUsage = totalSize) }
            } catch (e: Exception) {
                // 处理错误
            }
        }
    }

    /**
     * 设置主题
     */
    fun setTheme(theme: Theme) {
        viewModelScope.launch {
            dataStore.setTheme(theme)
            _uiState.update { it.copy(theme = theme) }
        }
    }

    /**
     * 设置语言
     */
    fun setLanguage(language: Language) {
        viewModelScope.launch {
            dataStore.setLanguage(language)
            _uiState.update { it.copy(language = language) }
        }
    }

    /**
     * 清除数据
     */
    fun clearData() {
        viewModelScope.launch {
            try {
                // 清除数据库
                repository.clearAllData()
                
                // 清除图片文件
                fileUtils.clearImageCache(context)
                
                // 重新计算存储使用量
                calculateStorageUsage()
            } catch (e: Exception) {
                // 处理错误
            }
        }
    }

    /**
     * 获取总存储大小(MB)
     */
    private suspend fun getTotalStorageSize(): Double {
        // 获取图片文件夹大小
        val imagesFolderSize = context.getExternalFilesDir(null)?.let { dir ->
            dir.walk()
                .filter { it.isFile }
                .sumOf { it.length() }
        } ?: 0L

        return (imagesFolderSize.toDouble() / (1024 * 1024)) // 转换为MB
    }
}
