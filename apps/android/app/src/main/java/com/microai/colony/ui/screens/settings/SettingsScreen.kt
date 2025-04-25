package com.microai.colony.ui.screens.settings

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import com.microai.colony.R

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SettingsScreen(
    modifier: Modifier = Modifier,
    viewModel: SettingsViewModel = hiltViewModel(),
    onNavigateBack: () -> Unit
) {
    val uiState by viewModel.uiState.collectAsState()
    
    var showThemeDialog by remember { mutableStateOf(false) }
    var showLanguageDialog by remember { mutableStateOf(false) }
    var showClearDataDialog by remember { mutableStateOf(false) }
    
    Scaffold(
        topBar = {
            CenterAlignedTopAppBar(
                title = { Text(stringResource(R.string.settings_title)) },
                navigationIcon = {
                    IconButton(onClick = onNavigateBack) {
                        Icon(Icons.Filled.ArrowBack, contentDescription = null)
                    }
                }
            )
        }
    ) { padding ->
        Column(
            modifier = modifier
                .fillMaxSize()
                .padding(padding)
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            // 主题设置
            SettingItem(
                icon = Icons.Filled.Palette,
                title = stringResource(R.string.theme_setting),
                subtitle = uiState.theme.displayName,
                onClick = { showThemeDialog = true }
            )
            
            // 语言设置
            SettingItem(
                icon = Icons.Filled.Language,
                title = stringResource(R.string.language_setting),
                subtitle = uiState.language.displayName,
                onClick = { showLanguageDialog = true }
            )
            
            // 检测配置
            SettingItem(
                icon = Icons.Filled.TuneVertical,
                title = stringResource(R.string.detection_config),
                onClick = { /* 打开检测配置 */ }
            )
            
            Divider(modifier = Modifier.padding(vertical = 8.dp))
            
            // 存储管理
            SettingItem(
                icon = Icons.Filled.Storage,
                title = stringResource(R.string.storage_management),
                subtitle = "${uiState.storageUsage}MB已使用",
                onClick = { showClearDataDialog = true }
            )
            
            // 版本信息
            SettingItem(
                icon = Icons.Filled.Info,
                title = "版本",
                subtitle = uiState.versionName,
                onClick = { /* 显示版本信息 */ }
            )
        }
    }
    
    // 主题选择对话框
    if (showThemeDialog) {
        ThemeDialog(
            currentTheme = uiState.theme,
            onThemeSelected = { 
                viewModel.setTheme(it)
                showThemeDialog = false
            },
            onDismiss = { showThemeDialog = false }
        )
    }
    
    // 语言选择对话框
    if (showLanguageDialog) {
        LanguageDialog(
            currentLanguage = uiState.language,
            onLanguageSelected = {
                viewModel.setLanguage(it)
                showLanguageDialog = false
            },
            onDismiss = { showLanguageDialog = false }
        )
    }
    
    // 清除数据确认对话框
    if (showClearDataDialog) {
        ClearDataDialog(
            onConfirm = {
                viewModel.clearData()
                showClearDataDialog = false
            },
            onDismiss = { showClearDataDialog = false }
        )
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun SettingItem(
    icon: ImageVector,
    title: String,
    subtitle: String? = null,
    onClick: () -> Unit
) {
    Card(
        onClick = onClick,
        modifier = Modifier.fillMaxWidth()
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp),
            horizontalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            Icon(
                imageVector = icon,
                contentDescription = null,
                tint = MaterialTheme.colorScheme.primary
            )
            
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    text = title,
                    style = MaterialTheme.typography.titleMedium
                )
                if (subtitle != null) {
                    Text(
                        text = subtitle,
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
            }
            
            Icon(
                imageVector = Icons.Filled.ChevronRight,
                contentDescription = null,
                tint = MaterialTheme.colorScheme.onSurfaceVariant
            )
        }
    }
}

@Composable
private fun ThemeDialog(
    currentTheme: Theme,
    onThemeSelected: (Theme) -> Unit,
    onDismiss: () -> Unit
) {
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("选择主题") },
        text = {
            Column {
                Theme.values().forEach { theme ->
                    RadioButton(
                        selected = theme == currentTheme,
                        onClick = { onThemeSelected(theme) },
                        label = { Text(theme.displayName) }
                    )
                }
            }
        },
        confirmButton = {
            TextButton(onClick = onDismiss) {
                Text("关闭")
            }
        }
    )
}

@Composable
private fun LanguageDialog(
    currentLanguage: Language,
    onLanguageSelected: (Language) -> Unit,
    onDismiss: () -> Unit
) {
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("选择语言") },
        text = {
            Column {
                Language.values().forEach { language ->
                    RadioButton(
                        selected = language == currentLanguage,
                        onClick = { onLanguageSelected(language) },
                        label = { Text(language.displayName) }
                    )
                }
            }
        },
        confirmButton = {
            TextButton(onClick = onDismiss) {
                Text("关闭")
            }
        }
    )
}

@Composable
private fun ClearDataDialog(
    onConfirm: () -> Unit,
    onDismiss: () -> Unit
) {
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("清除数据") },
        text = { Text("确定要清除所有数据吗？此操作不可恢复。") },
        confirmButton = {
            TextButton(
                onClick = onConfirm,
                colors = ButtonDefaults.textButtonColors(
                    contentColor = MaterialTheme.colorScheme.error
                )
            ) {
                Text("清除")
            }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) {
                Text("取消")
            }
        }
    )
}

@Composable
private fun RadioButton(
    selected: Boolean,
    onClick: () -> Unit,
    label: @Composable () -> Unit
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(vertical = 4.dp),
        horizontalArrangement = Arrangement.spacedBy(8.dp)
    ) {
        RadioButton(
            selected = selected,
            onClick = onClick
        )
        label()
    }
}
