package com.microai.colony.utils

import android.content.Context
import android.hardware.Sensor
import android.hardware.SensorEvent
import android.hardware.SensorManager
import io.mockk.*
import io.mockk.impl.annotations.MockK
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.test.runTest
import org.junit.Before
import org.junit.Test
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertTrue

@OptIn(ExperimentalCoroutinesApi::class)
class SensorUtilsTest {

    @MockK
    lateinit var context: Context

    @MockK
    lateinit var sensorManager: SensorManager

    @MockK
    lateinit var rotationSensor: Sensor

    private lateinit var sensorUtils: SensorUtils

    @Before
    fun setup() {
        MockKAnnotations.init(this)
        every { context.getSystemService(Context.SENSOR_SERVICE) } returns sensorManager
        every { sensorManager.getDefaultSensor(Sensor.TYPE_ROTATION_VECTOR) } returns rotationSensor
        
        sensorUtils = SensorUtils(context)
    }

    @Test
    fun `test isIdealAngle with valid angle`() {
        // 测试理想角度范围
        assertTrue(sensorUtils.isIdealAngle(3.0))
        assertTrue(sensorUtils.isIdealAngle(5.0))
        assertFalse(sensorUtils.isIdealAngle(6.0))
    }

    @Test
    fun `test getTiltAngle emits correct angles`() = runTest {
        // 模拟传感器数据
        val rotationMatrix = FloatArray(9)
        val orientationAngles = FloatArray(3)
        
        // 设置模拟传感器事件
        val sensorEvent = mockk<SensorEvent> {
            every { values } returns FloatArray(3).apply {
                this[0] = 0.1f  // 模拟倾斜角度
                this[1] = 0.2f
                this[2] = 0.3f
            }
        }
        
        // 模拟传感器回调
        every { 
            sensorManager.registerListener(
                any(), 
                rotationSensor, 
                SensorManager.SENSOR_DELAY_UI
            )
        } answers {
            val listener = firstArg<android.hardware.SensorEventListener>()
            listener.onSensorChanged(sensorEvent)
            true
        }
        
        // 收集角度流的第一个值
        val angle = sensorUtils.getTiltAngle().first()
        
        // 验证角度计算结果
        assertEquals(expected = 5.0, actual = angle, absoluteTolerance = 0.1)
    }

    @Test
    fun `test sensor registration and unregistration`() {
        // 验证传感器注册
        verify { 
            sensorManager.registerListener(
                any(),
                rotationSensor,
                SensorManager.SENSOR_DELAY_UI
            )
        }
        
        // 验证传感器解注册
        verify { sensorManager.unregisterListener(any()) }
    }

    @Test
    fun `test getTiltAngle with null sensor`() = runTest {
        // 模拟无可用传感器
        every { sensorManager.getDefaultSensor(Sensor.TYPE_ROTATION_VECTOR) } returns null
        
        // 验证角度流为空
        val angle = sensorUtils.getTiltAngle().first()
        assertEquals(0.0, angle)
    }

    @Test
    fun `test error handling`() = runTest {
        // 模拟传感器错误
        every { 
            sensorManager.registerListener(
                any(), 
                rotationSensor, 
                SensorManager.SENSOR_DELAY_UI
            )
        } throws RuntimeException("Sensor error")
        
        // 验证错误处理
        val angle = sensorUtils.getTiltAngle().first()
        assertEquals(0.0, angle)
    }
}
