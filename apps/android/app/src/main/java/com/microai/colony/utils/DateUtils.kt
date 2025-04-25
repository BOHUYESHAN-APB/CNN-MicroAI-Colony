package com.microai.colony.utils

import java.text.SimpleDateFormat
import java.util.*
import javax.inject.Inject
import javax.inject.Singleton

/**
 * 日期工具类
 */
@Singleton
class DateUtils @Inject constructor() {
    companion object {
        private const val DATE_FORMAT = "yyyy-MM-dd"
        private const val TIME_FORMAT = "HH:mm:ss"
        private const val DATETIME_FORMAT = "yyyy-MM-dd HH:mm:ss"
        private const val FILE_DATE_FORMAT = "yyyyMMdd_HHmmss"
    }
    
    private val dateFormatter = SimpleDateFormat(DATE_FORMAT, Locale.getDefault())
    private val timeFormatter = SimpleDateFormat(TIME_FORMAT, Locale.getDefault())
    private val dateTimeFormatter = SimpleDateFormat(DATETIME_FORMAT, Locale.getDefault())
    private val fileDateFormatter = SimpleDateFormat(FILE_DATE_FORMAT, Locale.getDefault())
    
    /**
     * 格式化日期
     */
    fun formatDate(date: Date): String = dateFormatter.format(date)
    
    /**
     * 格式化时间
     */
    fun formatTime(date: Date): String = timeFormatter.format(date)
    
    /**
     * 格式化日期时间
     */
    fun formatDateTime(date: Date): String = dateTimeFormatter.format(date)
    
    /**
     * 格式化文件日期
     */
    fun formatFileDate(date: Date): String = fileDateFormatter.format(date)
    
    /**
     * 获取今天开始时间
     */
    fun getTodayStart(): Date {
        return Calendar.getInstance().apply {
            set(Calendar.HOUR_OF_DAY, 0)
            set(Calendar.MINUTE, 0)
            set(Calendar.SECOND, 0)
            set(Calendar.MILLISECOND, 0)
        }.time
    }
    
    /**
     * 获取本周开始时间
     */
    fun getWeekStart(): Date {
        return Calendar.getInstance().apply {
            set(Calendar.DAY_OF_WEEK, Calendar.MONDAY)
            set(Calendar.HOUR_OF_DAY, 0)
            set(Calendar.MINUTE, 0)
            set(Calendar.SECOND, 0)
            set(Calendar.MILLISECOND, 0)
        }.time
    }
    
    /**
     * 获取本月开始时间
     */
    fun getMonthStart(): Date {
        return Calendar.getInstance().apply {
            set(Calendar.DAY_OF_MONTH, 1)
            set(Calendar.HOUR_OF_DAY, 0)
            set(Calendar.MINUTE, 0)
            set(Calendar.SECOND, 0)
            set(Calendar.MILLISECOND, 0)
        }.time
    }
    
    /**
     * 获取相对时间描述
     */
    fun getRelativeTimeSpan(date: Date): String {
        val now = System.currentTimeMillis()
        val time = date.time
        val diff = now - time
        
        return when {
            diff < 60 * 1000 -> "刚刚"
            diff < 60 * 60 * 1000 -> "${diff / (60 * 1000)}分钟前"
            diff < 24 * 60 * 60 * 1000 -> "${diff / (60 * 60 * 1000)}小时前"
            diff < 48 * 60 * 60 * 1000 -> "昨天"
            diff < 7 * 24 * 60 * 60 * 1000 -> "${diff / (24 * 60 * 60 * 1000)}天前"
            else -> formatDate(date)
        }
    }
    
    /**
     * 解析日期字符串
     */
    fun parseDateTime(dateStr: String): Date? {
        return try {
            dateTimeFormatter.parse(dateStr)
        } catch (e: Exception) {
            null
        }
    }
    
    /**
     * 检查是否是同一天
     */
    fun isSameDay(date1: Date, date2: Date): Boolean {
        val cal1 = Calendar.getInstance().apply { time = date1 }
        val cal2 = Calendar.getInstance().apply { time = date2 }
        
        return cal1.get(Calendar.YEAR) == cal2.get(Calendar.YEAR) &&
                cal1.get(Calendar.DAY_OF_YEAR) == cal2.get(Calendar.DAY_OF_YEAR)
    }
}
