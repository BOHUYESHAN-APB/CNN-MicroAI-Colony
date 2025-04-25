package com.microai.colony.ui.screens.analysis

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import com.github.mikephil.charting.data.Entry
import com.github.mikephil.charting.data.LineData
import com.github.mikephil.charting.data.LineDataSet
import com.microai.colony.R
import java.text.SimpleDateFormat
import java.util.*

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun AnalysisScreen(
    modifier: Modifier = Modifier,
    viewModel: AnalysisViewModel = hiltViewModel(),
    onNavigateBack: () -> Unit
) {
    val uiState by viewModel.uiState.collectAsState()
    
    Scaffold(
        topBar = {
            CenterAlignedTopAppBar(
                title = { Text(stringResource(R.string.analysis_title)) },
                navigationIcon = {
                    IconButton(onClick = onNavigateBack) {
                        Icon(Icons.Filled.ArrowBack, contentDescription = null)
                    }
                }
            )
        }
    ) { padding ->
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
            uiState.statistics == null -> {
                EmptyScreen()
            }
            else -> {
                AnalysisContent(
                    uiState = uiState,
                    modifier = modifier.padding(padding)
                )
            }
        }
    }
}

@Composable
private fun AnalysisContent(
    uiState: AnalysisUiState,
    modifier: Modifier = Modifier
) {
    Column(
        modifier = modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        // 数据概览卡片
        StatisticsCard(
            statistics = uiState.statistics!!,
            modifier = Modifier.fillMaxWidth()
        )
        
        // 趋势图
        TrendChart(
            data = uiState.statistics.timeSeriesData,
            modifier = Modifier
                .fillMaxWidth()
                .height(240.dp)
        )
        
        // LLM分析结果
        if (uiState.llmAnalysis != null) {
            LlmAnalysisCard(
                analysis = uiState.llmAnalysis,
                modifier = Modifier.fillMaxWidth()
            )
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun StatisticsCard(
    statistics: StatisticsData,
    modifier: Modifier = Modifier
) {
    OutlinedCard(
        modifier = modifier
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            Text(
                text = stringResource(R.string.total_detections, statistics.totalDetections),
                style = MaterialTheme.typography.titleMedium
            )
            Text(
                text = stringResource(R.string.average_count, statistics.averageCount),
                style = MaterialTheme.typography.bodyLarge
            )
            
            // 置信度分布
            Text(
                text = stringResource(R.string.confidence_analysis),
                style = MaterialTheme.typography.titleSmall,
                modifier = Modifier.padding(top = 8.dp)
            )
            statistics.confidenceDistribution.forEach { (level, count) ->
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween
                ) {
                    Text(text = level)
                    Text(text = "$count")
                }
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun LlmAnalysisCard(
    analysis: LlmAnalysisData,
    modifier: Modifier = Modifier
) {
    OutlinedCard(
        modifier = modifier
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            Text(
                text = "AI分析",
                style = MaterialTheme.typography.titleMedium
            )
            
            Text(
                text = analysis.analysis,
                style = MaterialTheme.typography.bodyMedium
            )
            
            if (analysis.recommendations.isNotEmpty()) {
                Text(
                    text = "建议",
                    style = MaterialTheme.typography.titleSmall,
                    modifier = Modifier.padding(top = 8.dp)
                )
                analysis.recommendations.forEach { recommendation ->
                    Text(
                        text = "• $recommendation",
                        style = MaterialTheme.typography.bodyMedium
                    )
                }
            }
        }
    }
}

@Composable
private fun TrendChart(
    data: List<TimePoint>,
    modifier: Modifier = Modifier
) {
    AndroidView(
        modifier = modifier,
        factory = { context ->
            LineChart(context).apply {
                description.isEnabled = false
                legend.isEnabled = true
                setTouchEnabled(true)
                setScaleEnabled(true)
                setPinchZoom(true)
                
                xAxis.valueFormatter = object : ValueFormatter() {
                    private val dateFormatter = SimpleDateFormat("MM/dd", Locale.getDefault())
                    
                    override fun getFormattedValue(value: Float): String {
                        return dateFormatter.format(Date(value.toLong()))
                    }
                }
            }
        },
        update = { chart ->
            val entries = data.map { point ->
                Entry(point.timestamp.toFloat(), point.count.toFloat())
            }
            
            val dataSet = LineDataSet(entries, "菌落数量").apply {
                color = android.graphics.Color.BLUE
                setCircleColor(android.graphics.Color.BLUE)
                lineWidth = 2f
                circleRadius = 4f
                setDrawCircleHole(false)
                mode = LineDataSet.Mode.CUBIC_BEZIER
            }
            
            chart.data = LineData(dataSet)
            chart.invalidate()
        }
    )
}
