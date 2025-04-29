package com.microai.colony.utils

import androidx.room.TypeConverter
import com.google.gson.Gson
import com.google.gson.reflect.TypeToken

class Converters {
    @TypeConverter
    fun fromString(value: String): Map<String, String> {
        val mapType = object : TypeToken<Map<String, String>>() {}.type
        return Gson().fromJson(value, mapType)
    }

    @TypeConverter
    fun fromMap(map: Map<String, String>): String {
        return Gson().toJson(map)
    }
    
    @TypeConverter
    fun fromFloatArray(value: FloatArray?): String {
        if (value == null) return ""
        return value.joinToString(",")
    }

    @TypeConverter
    fun toFloatArray(value: String): FloatArray {
        if (value.isEmpty()) return FloatArray(0)
        return value.split(",").map { it.toFloat() }.toFloatArray()
    }
}
