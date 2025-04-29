package com.microai.colony.data.db

import androidx.room.Database
import androidx.room.RoomDatabase
import androidx.room.TypeConverters
import com.microai.colony.data.model.DetectionResult
import com.microai.colony.data.model.ModelInfo
import com.microai.colony.utils.Converters

@Database(
    entities = [
        ModelInfo::class,
        DetectionResult::class
    ],
    version = 1,
    exportSchema = false
)
@TypeConverters(Converters::class)
abstract class ColonyDatabase : RoomDatabase() {
    abstract fun modelDao(): ModelDao
    
    companion object {
        const val DATABASE_NAME = "colony_db"
    }
}
