package com.microai.colony.di

import android.content.Context
import androidx.room.Room
import com.microai.colony.data.db.ColonyDatabase
import com.microai.colony.data.db.ModelDao
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.android.qualifiers.ApplicationContext
import dagger.hilt.components.SingletonComponent
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
object DatabaseModule {
    
    @Provides
    @Singleton
    fun provideDatabase(
        @ApplicationContext context: Context
    ): ColonyDatabase = Room.databaseBuilder(
        context,
        ColonyDatabase::class.java,
        ColonyDatabase.DATABASE_NAME
    ).build()

    @Provides
    @Singleton
    fun provideModelDao(database: ColonyDatabase): ModelDao = database.modelDao()
}
