package com.microai.colony.ui.screens.history

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import com.microai.colony.R
import com.microai.colony.data.model.DetectionResult
import com.microai.colony.utils.DateUtils

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun HistoryScreen(
    modifier: Modifier = Modifier,
    viewModel: HistoryViewModel = hiltViewModel(),
    onNavigateBack: () -> Unit,
    onItemClick: (Long) -> Unit
) {
    val uiState by viewModel.uiState.collectAsState()
    
    Scaffold(
        topBar = {
            CenterAlignedTopAppBar(
                title = { Text(stringResource(R.string.history_title)) },
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
        ) {
            // 筛选选项
            FilterChips(
                selectedFilter = uiState.selectedFilter,
                onFilterSelected = { viewModel.setFilter(it) },
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 16.dp, vertical = 8.dp)
            )
            
            when {
                uiState.isLoading -> {
                    LoadingScreen()
                }
                uiState.error != null -> {
                    ErrorScreen(
                        message = uiState.error!!,
                        onRetry = { viewModel.retry() }
                    )
                }
                uiState.records.isEmpty() -> {
                    EmptyScreen()
                }
                else -> {
                    HistoryList(
                        records = uiState.records,
                        onItemClick = onItemClick,
                        onDeleteClick = { viewModel.deleteRecord(it) }
                    )
                }
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun FilterChips(
    selectedFilter: TimeFilter,
    onFilterSelected: (TimeFilter) -> Unit,
    modifier: Modifier = Modifier
) {
    Row(
        modifier = modifier,
        horizontalArrangement = Arrangement.spacedBy(8.dp)
    ) {
        TimeFilter.values().forEach { filter ->
            FilterChip(
                selected = selectedFilter == filter,
                onClick = { onFilterSelected(filter) },
                label = {
                    Text(
                        text = when (filter) {
                            TimeFilter.ALL -> stringResource(R.string.filter_all)
                            TimeFilter.TODAY -> stringResource(R.string.filter_today)
                            TimeFilter.WEEK -> stringResource(R.string.filter_week)
                            TimeFilter.MONTH -> stringResource(R.string.filter_month)
                        }
                    )
                }
            )
        }
    }
}

@Composable
private fun HistoryList(
    records: List<DetectionResult>,
    onItemClick: (Long) -> Unit,
    onDeleteClick: (DetectionResult) -> Unit,
    modifier: Modifier = Modifier
) {
    LazyColumn(
        modifier = modifier.fillMaxSize(),
        contentPadding = PaddingValues(16.dp),
        verticalArrangement = Arrangement.spacedBy(8.dp)
    ) {
        items(
            items = records,
            key = { it.id }
        ) { record ->
            HistoryItem(
                record = record,
                onClick = { onItemClick(record.id) },
                onDeleteClick = { onDeleteClick(record) }
            )
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun HistoryItem(
    record: DetectionResult,
    onClick: () -> Unit,
    onDeleteClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    Card(
        onClick = onClick,
        modifier = modifier.fillMaxWidth()
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            // 缩略图
            AsyncImage(
                model = record.imageUri,
                contentDescription = null,
                modifier = Modifier
                    .size(80.dp)
                    .padding(end = 16.dp)
            )
            
            // 信息
            Column(
                modifier = Modifier.weight(1f)
            ) {
                Text(
                    text = "${record.colonyCount}个菌落",
                    style = MaterialTheme.typography.titleMedium
                )
                Text(
                    text = "置信度: ${(record.confidence * 100).toInt()}%",
                    style = MaterialTheme.typography.bodyMedium,
                    color = getConfidenceColor(record.confidence)
                )
                Text(
                    text = DateUtils.getRelativeTimeSpan(record.timestamp),
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
            
            // 删除按钮
            IconButton(onClick = onDeleteClick) {
                Icon(
                    imageVector = Icons.Filled.Delete,
                    contentDescription = null,
                    tint = MaterialTheme.colorScheme.error
                )
            }
        }
    }
}

/**
 * 时间筛选选项
 */
enum class TimeFilter {
    ALL,
    TODAY,
    WEEK,
    MONTH
}
