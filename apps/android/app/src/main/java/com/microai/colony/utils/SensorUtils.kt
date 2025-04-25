package com.microai.colony.utils

import android.content.Context
import android.hardware.Sensor
import android.hardware.SensorEvent
import android.hardware.SensorEventListener
import android.hardware.SensorManager
import kotlinx.coroutines.channels.awaitClose
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.callbackFlow
import javax.inject.Inject
import javax.inject.Singleton
import kotlin.math.abs

/**
 * 传感器工具类
 */
@Singleton
class SensorUtils @Inject constructor(
    context: Context
) {
    private val sensorManager = context.getSystemService(Context.SENSOR_SERVICE) as SensorManager
    
    /**
     * 获取设备倾斜角度流
     */
    fun getTiltAngle(): Flow<Double> = callbackFlow {
        val rotationSensor = sensorManager.getDefaultSensor(Sensor.TYPE_ROTATION_VECTOR)
        
        val listener = object : SensorEventListener {
            private val rotationMatrix = FloatArray(9)
            private val orientationAngles = FloatArray(3)
            
            override fun onSensorChanged(event: SensorEvent) {
                // 获取旋转矩阵
                SensorManager.getRotationMatrixFromVector(rotationMatrix, event.values)
                // 获取方向角
                SensorManager.getOrientation(rotationMatrix, orientationAngles)
                
                // 计算倾斜角度
                val pitch = Math.toDegrees(orientationAngles[1].toDouble())
                val roll = Math.toDegrees(orientationAngles[2].toDouble())
                
                // 计算设备与水平面的夹角
                val tiltAngle = calculateTiltAngle(pitch, roll)
                trySend(tiltAngle)
            }
            
            override fun onAccuracyChanged(sensor: Sensor?, accuracy: Int) {}
        }
        
        if (rotationSensor != null) {
            sensorManager.registerListener(
                listener,
                rotationSensor,
                SensorManager.SENSOR_DELAY_UI
            )
        }
        
        awaitClose {
            sensorManager.unregisterListener(listener)
        }
    }
    
    /**
     * 计算倾斜角度
     * @return 返回设备与水平面的夹角(绝对值，单位：度)
     */
    private fun calculateTiltAngle(pitch: Double, roll: Double): Double {
        // 使用勾股定理计算设备与水平面的夹角
        return abs(Math.sqrt(pitch * pitch + roll * roll))
    }
    
    /**
     * 检查是否在理想角度范围内
     */
    fun isIdealAngle(angle: Double): Boolean {
        return angle <= 5.0 // 5度以内为理想角度
    }
}
