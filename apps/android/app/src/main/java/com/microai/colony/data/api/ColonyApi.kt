package com.microai.colony.data.api

import okhttp3.MultipartBody
import retrofit2.Response
import retrofit2.http.*
import java.io.File

/**
 * 菌落检测API接口定义
 */
interface ColonyApi {
    /**
     * 单张图片分析
     */
    @Multipart
    @POST("api/analyze")
    suspend fun analyzeImage(
        @Part image: MultipartBody.Part,
        @Part("model_type") modelType: String = "balanced",
        @Part("preprocess_methods") preprocessMethods: List<String>? = null
    ): Response<AnalysisResponse>
    
    /**
     * 批量分析图片
     */
    @Multipart
    @POST("api/analyze_batch")
    suspend fun analyzeBatch(
        @Part images: List<MultipartBody.Part>,
        @Part("model_type") modelType: String = "balanced",
        @Part("preprocess_methods") preprocessMethods: List<String>? = null
    ): Response<List<AnalysisResponse>>
    
    /**
     * 实时视频流分析
     */
    @Streaming
    @POST("api/stream_analyze")
    suspend fun analyzeStream(
        @Body frameData: ByteArray,
        @Query("model_type") modelType: String = "balanced"
    ): Response<StreamAnalysisResponse>
    
    /**
     * LLM分析
     */
    @POST("api/llm_analyze")
    suspend fun getLlmAnalysis(
        @Body request: LlmAnalysisRequest
    ): Response<LlmAnalysisResponse>
    
    /**
     * 获取统计数据
     */
    @GET("api/statistics")
    suspend fun getStatistics(
        @Query("start_date") startDate: String? = null,
        @Query("end_date") endDate: String? = null
    ): Response<StatisticsResponse>
}

/**
 * 分析响应
 */
data class AnalysisResponse(
    val status: String,
    val colonyCount: Int,
    val confidence: Float,
    val boxes: List<Box>,
    val imageWidth: Int,
    val imageHeight: Int,
    val error: String? = null
) {
    data class Box(
        val x1: Float,
        val y1: Float,
        val x2: Float,
        val y2: Float,
        val confidence: Float
    )
}

/**
 * 流分析响应
 */
data class StreamAnalysisResponse(
    val status: String,
    val frames: List<FrameResult>,
    val error: String? = null
) {
    data class FrameResult(
        val timestamp: Long,
        val colonyCount: Int,
        val confidence: Float,
        val boxes: List<AnalysisResponse.Box>
    )
}

/**
 * LLM分析请求
 */
data class LlmAnalysisRequest(
    val detectionResults: List<DetectionData>
) {
    data class DetectionData(
        val colonyCount: Int,
        val confidence: Float,
        val timestamp: Long
    )
}

/**
 * LLM分析响应
 */
data class LlmAnalysisResponse(
    val analysis: String,
    val density: Float,
    val distribution: String,
    val recommendations: List<String>
)

/**
 * 统计响应
 */
data class StatisticsResponse(
    val totalDetections: Int,
    val averageCount: Float,
    val confidenceDistribution: Map<String, Int>,
    val timeSeriesData: List<TimePoint>
) {
    data class TimePoint(
        val timestamp: Long,
        val count: Int
    )
}
