package com.microai.colony.data.db

import android.content.Context
import androidx.room.*
import com.microai.colony.data.model.DetectionResult
import com.google.gson.Gson
import com.google.gson.reflect.TypeToken
import dagger.hilt.android.qualifiers.ApplicationContext
import java.util.Date
import javax.inject.Inject
import javax.inject.Singleton

@Database(
    entities = [DetectionResult::class],
    version = 1,
    exportSchema = false
)
@TypeConverters(Converters::class)
abstract class ColonyDatabase : RoomDatabase() {
    abstract fun detectionDao(): DetectionDao
    
    companion object {
        private const val DATABASE_NAME = "colony_database"
        
        @Volatile
        private var instance: ColonyDatabase? = null
        
        fun getInstance(context: Context): ColonyDatabase {
            return instance ?: synchronized(this) {
                instance ?: buildDatabase(context).also { instance = it }
            }
        }
        
        private fun buildDatabase(context: Context): ColonyDatabase {
            return Room.databaseBuilder(
                context.applicationContext,
                ColonyDatabase::class.java,
                DATABASE_NAME
            )
            .fallbackToDestructiveMigration()
            .build()
        }
    }
}

/**
 * 数据访问接口
 */
@Dao
interface DetectionDao {
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insert(detection: DetectionResult)
    
    @Delete
    suspend fun delete(detection: DetectionResult)
    
    @Query("SELECT * FROM detection_results ORDER BY timestamp DESC")
    fun getAllFlow(): Flow<List<DetectionResult>>
    
    @Query("SELECT * FROM detection_results ORDER BY timestamp DESC LIMIT :limit")
    fun getRecentFlow(limit: Int): Flow<List<DetectionResult>>
    
    @Query("DELETE FROM detection_results")
    suspend fun deleteAll()
}

/**
 * 类型转换器
 */
class Converters {
    private val gson = Gson()
    
    @TypeConverter
    fun fromTimestamp(value: Long?): Date? {
        return value?.let { Date(it) }
    }
    
    @TypeConverter
    fun dateToTimestamp(date: Date?): Long? {
        return date?.time
    }
    
    @TypeConverter
    fun fromBoxList(value: List<DetectionResult.Box>?): String {
        return gson.toJson(value)
    }
    
    @TypeConverter
    fun toBoxList(value: String): List<DetectionResult.Box>? {
        val type = object : TypeToken<List<DetectionResult.Box>>() {}.type
        return gson.fromJson(value, type)
    }
}

/**
 * 数据库提供者
 */
@Module
@InstallIn(SingletonComponent::class)
object DatabaseModule {
    @Provides
    @Singleton
    fun provideDatabase(@ApplicationContext context: Context): ColonyDatabase {
        return ColonyDatabase.getInstance(context)
    }
    
    @Provides
    fun provideDetectionDao(database: ColonyDatabase): DetectionDao {
        return database.detectionDao()
    }
}
