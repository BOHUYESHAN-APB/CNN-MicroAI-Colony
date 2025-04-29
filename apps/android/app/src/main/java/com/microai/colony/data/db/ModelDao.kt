package com.microai.colony.data.db

import androidx.room.*
import com.microai.colony.data.model.ModelInfo
import kotlinx.coroutines.flow.Flow

@Dao
interface ModelDao {
    @Query("SELECT * FROM models ORDER BY importedAt DESC")
    fun getAllModels(): Flow<List<ModelInfo>>
    
    @Query("SELECT * FROM models WHERE isActive = 1")
    fun getActiveModel(): Flow<ModelInfo?>
    
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertModel(model: ModelInfo)
    
    @Delete
    suspend fun deleteModel(model: ModelInfo)
    
    @Query("UPDATE models SET isActive = CASE WHEN id = :modelId THEN 1 ELSE 0 END")
    suspend fun setActiveModel(modelId: String)
    
    @Query("SELECT * FROM models WHERE id = :modelId")
    suspend fun getModelById(modelId: String): ModelInfo?
    
    @Query("DELETE FROM models WHERE id = :modelId")
    suspend fun deleteModelById(modelId: String)
    
    @Update
    suspend fun updateModel(model: ModelInfo)
}
