package com.microai.colony.data.repository

import android.content.Context
import android.net.Uri
import com.microai.colony.data.api.ColonyApi
import com.microai.colony.data.db.ColonyDatabase
import com.microai.colony.data.model.DetectionResult
import com.microai.colony.utils.FileUtils
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.withContext
import okhttp3.MediaType.Companion.toMediaTypeOrNull
import okhttp3.MultipartBody
import okhttp3.RequestBody.Companion.asRequestBody
import java.io.File
import java.util.Date
import javax.inject.Inject
import javax.inject.Singleton

/**
 * 菌落检测数据仓库
 */
@Singleton
class ColonyRepository @Inject constructor(
    @ApplicationContext private val context: Context,
    private val api: ColonyApi,
    private val database: ColonyDatabase,
    private val fileUtils: FileUtils
) {
    /**
     * 分析单张图片
     */
    suspend fun analyzeImage(imageUri: Uri): Result<DetectionResult> = withContext(Dispatchers.IO) {
        try {
            // 转换图片文件
            val imageFile = fileUtils.createTempFileFromUri(context, imageUri)
            val requestBody = imageFile.asRequestBody("image/*".toMediaTypeOrNull())
            val part = MultipartBody.Part.createFormData("file", imageFile.name, requestBody)
            
            // 发送API请求
            val response = api.analyzeImage(part)
            if (!response.isSuccessful) {
                return@withContext Result.failure(Exception("Analysis failed: ${response.message()}"))
            }
            
            // 保存结果
            val result = response.body()?.let { apiResponse ->
                DetectionResult(
                    imageUri = imageUri.toString(),
                    timestamp = Date(),
                    colonyCount = apiResponse.colonyCount,
                    confidence = apiResponse.confidence,
                    boxes = apiResponse.boxes.map { box ->
                        DetectionResult.Box(
                            x1 = box.x1,
                            y1 = box.y1,
                            x2 = box.x2,
                            y2 = box.y2,
                            confidence = box.confidence
                        )
                    }
                )
            } ?: throw Exception("Empty response")
            
            // 保存到数据库
            database.detectionDao().insert(result)
            
            Result.success(result)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
    
    /**
     * 获取所有检测记录
     */
    fun getAllDetections(): Flow<List<DetectionResult>> {
        return database.detectionDao().getAllFlow()
    }
    
    /**
     * 获取最近的检测记录
     */
    fun getRecentDetections(limit: Int = 10): Flow<List<DetectionResult>> {
        return database.detectionDao().getRecentFlow(limit)
    }
    
    /**
     * 获取LLM分析
     */
    suspend fun getLlmAnalysis(detectionResults: List<DetectionResult>): Result<String> = 
        withContext(Dispatchers.IO) {
            try {
                val request = LlmAnalysisRequest(
                    detectionResults = detectionResults.map { result ->
                        LlmAnalysisRequest.DetectionData(
                            colonyCount = result.colonyCount,
                            confidence = result.confidence,
                            timestamp = result.timestamp.time
                        )
                    }
                )
                
                val response = api.getLlmAnalysis(request)
                if (!response.isSuccessful) {
                    return@withContext Result.failure(Exception("LLM analysis failed: ${response.message()}"))
                }
                
                val analysis = response.body()?.analysis
                    ?: return@withContext Result.failure(Exception("Empty LLM response"))
                    
                Result.success(analysis)
            } catch (e: Exception) {
                Result.failure(e)
            }
        }
    
    /**
     * 删除检测记录
     */
    suspend fun deleteDetection(result: DetectionResult) = withContext(Dispatchers.IO) {
        try {
            // 删除数据库记录
            database.detectionDao().delete(result)
            
            // 删除关联的图片文件
            Uri.parse(result.imageUri).path?.let { path ->
                File(path).delete()
            }
            
            Result.success(Unit)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
    
    /**
     * 清除所有数据
     */
    suspend fun clearAllData() = withContext(Dispatchers.IO) {
        try {
            // 清除数据库
            database.clearAllTables()
            
            // 清除图片文件
            fileUtils.clearImageCache(context)
            
            Result.success(Unit)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
}
