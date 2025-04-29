package com.microai.colony.data.repository

import android.content.Context
import android.net.Uri
import com.microai.colony.data.db.ModelDao
import com.microai.colony.data.model.ModelInfo
import com.microai.colony.utils.FileUtils
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.flow.Flow
import java.util.UUID
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class ModelRepository @Inject constructor(
    @ApplicationContext private val context: Context,
    private val modelDao: ModelDao
) {
    fun getAllModels(): Flow<List<ModelInfo>> = modelDao.getAllModels()
    
    fun getActiveModel(): Flow<ModelInfo?> = modelDao.getActiveModel()
    
    suspend fun importModel(uri: Uri, name: String): Result<ModelInfo> = runCatching {
        val (file, hash, size) = FileUtils.copyModelFile(context, uri).getOrThrow()
        
        val extension = file.extension
        require(extension in ModelInfo.SUPPORTED_TYPES) {
            "Unsupported model type: $extension"
        }
        
        val model = ModelInfo(
            id = UUID.randomUUID().toString(),
            name = name,
            path = file.absolutePath,
            type = extension,
            size = size,
            importedAt = System.currentTimeMillis(),
            hash = hash
        )
        
        modelDao.insertModel(model)
        model
    }
    
    suspend fun deleteModel(model: ModelInfo): Result<Unit> = runCatching {
        if (FileUtils.deleteModel(context, model)) {
            modelDao.deleteModel(model)
        } else {
            throw IllegalStateException("Failed to delete model file")
        }
    }
    
    suspend fun setActiveModel(modelId: String) {
        modelDao.setActiveModel(modelId)
    }
    
    suspend fun getModelFile(model: ModelInfo) = FileUtils.getModelFile(context, model)
}
