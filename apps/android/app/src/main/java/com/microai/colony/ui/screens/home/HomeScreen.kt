package com.microai.colony.ui.screens.home

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import com.microai.colony.R
import com.microai.colony.data.model.DetectionResult

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun HomeScreen(
    modifier: Modifier = Modifier,
    viewModel: HomeViewModel = hiltViewModel(),
    onNavigateToDetection: () -> Unit,
    onNavigateToHistory: () -> Unit,
    onNavigateToAnalysis: () -> Unit
) {
    val uiState by viewModel.uiState.collectAsState()
    
    Scaffold(
        topBar = {
            CenterAlignedTopAppBar(
                title = { Text(stringResource(R.string.main_title)) }
            )
        }
    ) { padding ->
        Column(
            modifier = modifier
                .fillMaxSize()
                .padding(padding)
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            // 主要功能按钮
            MainActionButtons(
                onRealTimeDetection = onNavigateToDetection,
                onPhotoDetection = onNavigateToDetection,
                modifier = Modifier.fillMaxWidth()
            )
            
            // 最近记录
            RecentRecords(
                records = uiState.recentRecords,
                onItemClick = { /* 处理记录点击 */ },
                modifier = Modifier.fillMaxWidth()
            )
        }
    }
}

@Composable
private fun MainActionButtons(
    onRealTimeDetection: () -> Unit,
    onPhotoDetection: () -> Unit,
    modifier: Modifier = Modifier
) {
    Column(
        modifier = modifier,
        verticalArrangement = Arrangement.spacedBy(8.dp)
    ) {
        Button(
            onClick = onRealTimeDetection,
            modifier = Modifier.fillMaxWidth(),
            colors = ButtonDefaults.buttonColors(
                containerColor = MaterialTheme.colorScheme.primary
            )
        ) {
            Icon(
                imageVector = Icons.Filled.Videocam,
                contentDescription = null,
                modifier = Modifier.padding(end = 8.dp)
            )
            Text(stringResource(R.string.btn_real_time))
        }
        
        Button(
            onClick = onPhotoDetection,
            modifier = Modifier.fillMaxWidth(),
            colors = ButtonDefaults.buttonColors(
                containerColor = MaterialTheme.colorScheme.secondary
            )
        ) {
            Icon(
                imageVector = Icons.Filled.PhotoCamera,
                contentDescription = null,
                modifier = Modifier.padding(end = 8.dp)
            )
            Text(stringResource(R.string.btn_photo))
        }
    }
}

@Composable
private fun RecentRecords(
    records: List<DetectionResult>,
    onItemClick: (DetectionResult) -> Unit,
    modifier: Modifier = Modifier
) {
    Column(modifier = modifier) {
        Text(
            text = stringResource(R.string.recent_records),
            style = MaterialTheme.typography.titleMedium,
            modifier = Modifier.padding(bottom = 8.dp)
        )
        
        if (records.isEmpty()) {
            EmptyScreen()
        } else {
            LazyRow(
                horizontalArrangement = Arrangement.spacedBy(8.dp),
                contentPadding = PaddingValues(horizontal = 4.dp)
            ) {
                items(records) { record ->
                    RecordItem(
                        record = record,
                        onClick = { onItemClick(record) }
                    )
                }
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun RecordItem(
    record: DetectionResult,
    onClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    Card(
        onClick = onClick,
        modifier = modifier.size(160.dp),
        elevation = CardDefaults.cardElevation(defaultElevation = 2.dp)
    ) {
        Column(
            modifier = Modifier.padding(8.dp),
            verticalArrangement = Arrangement.spacedBy(4.dp)
        ) {
            // 缩略图
            AsyncImage(
                model = record.imageUri,
                contentDescription = null,
                modifier = Modifier
                    .size(100.dp)
                    .align(Alignment.CenterHorizontally)
            )
            
            // 数量和置信度
            Text(
                text = "${record.colonyCount}个菌落",
                style = MaterialTheme.typography.bodyMedium
            )
            Text(
                text = "置信度: ${(record.confidence * 100).toInt()}%",
                style = MaterialTheme.typography.bodySmall,
                color = getConfidenceColor(record.confidence)
            )
        }
    }
}
