package com.microai.colony.ui.screens.detection

import android.content.Context
import com.microai.colony.data.repository.ColonyRepository
import com.microai.colony.utils.FileUtils
import com.microai.colony.utils.SensorUtils
import io.mockk.*
import io.mockk.impl.annotations.MockK
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.flow.flowOf
import kotlinx.coroutines.test.*
import org.junit.After
import org.junit.Before
import org.junit.Test
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertNull
import kotlin.test.assertTrue

@OptIn(ExperimentalCoroutinesApi::class)
class DetectionViewModelTest {

    @MockK
    lateinit var context: Context

    @MockK
    lateinit var repository: ColonyRepository

    @MockK
    lateinit var fileUtils: FileUtils

    @MockK
    lateinit var sensorUtils: SensorUtils

    private lateinit var viewModel: DetectionViewModel
    private val testDispatcher = StandardTestDispatcher()

    @Before
    fun setup() {
        MockKAnnotations.init(this)
        Dispatchers.setMain(testDispatcher)
        
        // 模拟传感器数据流
        coEvery { sensorUtils.getTiltAngle() } returns flowOf(3.0)
        every { sensorUtils.isIdealAngle(any()) } returns true
        
        viewModel = DetectionViewModel(
            context = context,
            repository = repository,
            fileUtils = fileUtils,
            sensorUtils = sensorUtils
        )
    }

    @After
    fun tearDown() {
        Dispatchers.resetMain()
    }

    @Test
    fun `test initial state`() = runTest {
        with(viewModel.uiState.value) {
            assertFalse(isLoading)
            assertNull(error)
            assertFalse(isFlashEnabled)
            assertEquals(0.0, tiltAngle)
            assertTrue(isIdealAngle)
        }
    }

    @Test
    fun `test angle state updates`() = runTest {
        // 模拟角度变化
        coEvery { sensorUtils.getTiltAngle() } returns flowOf(6.0)
        every { sensorUtils.isIdealAngle(6.0) } returns false
        
        // 初始化触发角度观察
        viewModel = DetectionViewModel(context, repository, fileUtils, sensorUtils)
        testScheduler.advanceUntilIdle()
        
        with(viewModel.uiState.value) {
            assertEquals(6.0, tiltAngle)
            assertFalse(isIdealAngle)
        }
    }

    @Test
    fun `test capture image with valid angle`() = runTest {
        // 设置理想角度
        coEvery { sensorUtils.getTiltAngle() } returns flowOf(3.0)
        every { sensorUtils.isIdealAngle(3.0) } returns true
        
        // 尝试拍照
        viewModel.captureImage()
        testScheduler.advanceUntilIdle()
        
        // 验证拍照逻辑被调用
        verify { fileUtils.createImageFile(any()) }
    }

    @Test
    fun `test capture image with invalid angle`() = runTest {
        // 设置不理想的角度
        coEvery { sensorUtils.getTiltAngle() } returns flowOf(10.0)
        every { sensorUtils.isIdealAngle(10.0) } returns false
        
        // 尝试拍照
        viewModel = DetectionViewModel(context, repository, fileUtils, sensorUtils)
        testScheduler.advanceUntilIdle()
        viewModel.captureImage()
        
        // 验证拍照被阻止，显示错误消息
        with(viewModel.uiState.value) {
            assertEquals("请调整设备角度至5°以内", error)
        }
        
        // 验证拍照逻辑未被调用
        verify(exactly = 0) { fileUtils.createImageFile(any()) }
    }

    @Test
    fun `test error handling during angle detection`() = runTest {
        // 模拟传感器错误
        coEvery { sensorUtils.getTiltAngle() } throws RuntimeException("Sensor error")
        
        viewModel = DetectionViewModel(context, repository, fileUtils, sensorUtils)
        testScheduler.advanceUntilIdle()
        
        // 验证错误处理
        with(viewModel.uiState.value) {
            assertEquals(0.0, tiltAngle)
            assertTrue(isIdealAngle) // 默认为true，避免阻止用户操作
        }
    }

    @Test
    fun `test retry after error`() = runTest {
        // 首先触发错误
        coEvery { sensorUtils.getTiltAngle() } throws RuntimeException("Sensor error")
        viewModel = DetectionViewModel(context, repository, fileUtils, sensorUtils)
        testScheduler.advanceUntilIdle()
        
        // 然后恢复正常
        coEvery { sensorUtils.getTiltAngle() } returns flowOf(3.0)
        viewModel.retry()
        testScheduler.advanceUntilIdle()
        
        // 验证状态恢复
        with(viewModel.uiState.value) {
            assertNull(error)
            assertEquals(3.0, tiltAngle)
            assertTrue(isIdealAngle)
        }
    }
}
