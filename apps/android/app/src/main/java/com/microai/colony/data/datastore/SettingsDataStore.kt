package com.microai.colony.data.datastore

import android.content.Context
import androidx.datastore.core.DataStore
import androidx.datastore.preferences.core.*
import androidx.datastore.preferences.preferencesDataStore
import com.microai.colony.ui.screens.settings.Language
import com.microai.colony.ui.screens.settings.Theme
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.catch
import kotlinx.coroutines.flow.map
import java.io.IOException
import javax.inject.Inject
import javax.inject.Singleton

/**
 * 设置数据
 */
data class Settings(
    val theme: Theme = Theme.SYSTEM,
    val language: Language = Language.SYSTEM
)

/**
 * 设置数据存储
 */
@Singleton
class SettingsDataStore @Inject constructor(
    @ApplicationContext private val context: Context
) {
    companion object {
        private val Context.dataStore: DataStore<Preferences> by preferencesDataStore(
            name = "settings"
        )

        // 键定义
        private val THEME_KEY = stringPreferencesKey("theme")
        private val LANGUAGE_KEY = stringPreferencesKey("language")
    }

    /**
     * 获取设置
     */
    fun getSettings(): Flow<Settings> = context.dataStore.data
        .catch { exception ->
            if (exception is IOException) {
                emit(emptyPreferences())
            } else {
                throw exception
            }
        }
        .map { preferences ->
            Settings(
                theme = preferences[THEME_KEY]?.let { Theme.valueOf(it) } ?: Theme.SYSTEM,
                language = preferences[LANGUAGE_KEY]?.let { Language.valueOf(it) } ?: Language.SYSTEM
            )
        }

    /**
     * 设置主题
     */
    suspend fun setTheme(theme: Theme) {
        context.dataStore.edit { preferences ->
            preferences[THEME_KEY] = theme.name
        }
    }

    /**
     * 设置语言
     */
    suspend fun setLanguage(language: Language) {
        context.dataStore.edit { preferences ->
            preferences[LANGUAGE_KEY] = language.name
        }
    }

    /**
     * 清除所有设置
     */
    suspend fun clearSettings() {
        context.dataStore.edit { preferences ->
            preferences.clear()
        }
    }
}

/**
 * DataStore依赖注入模块
 */
@Module
@InstallIn(SingletonComponent::class)
object DataStoreModule {
    @Provides
    @Singleton
    fun provideSettingsDataStore(
        @ApplicationContext context: Context
    ): SettingsDataStore = SettingsDataStore(context)
}
