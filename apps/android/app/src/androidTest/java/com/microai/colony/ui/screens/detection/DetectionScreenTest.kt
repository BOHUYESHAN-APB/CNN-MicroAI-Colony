package com.microai.colony.ui.screens.detection

import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.test.rule.GrantPermissionRule
import com.microai.colony.ui.theme.ColonyTheme
import dagger.hilt.android.testing.HiltAndroidRule
import dagger.hilt.android.testing.HiltAndroidTest
import io.mockk.MockKAnnotations
import io.mockk.every
import io.mockk.impl.annotations.MockK
import kotlinx.coroutines.flow.flowOf
import org.junit.Before
import org.junit.Rule
import org.junit.Test

@HiltAndroidTest
class DetectionScreenTest {

    @get:Rule(order = 0)
    val hiltRule = HiltAndroidRule(this)

    @get:Rule(order = 1)
    val composeTestRule = createComposeRule()

    @get:Rule(order = 2)
    val permissionRule: GrantPermissionRule = GrantPermissionRule.grant(
        android.Manifest.permission.CAMERA,
        android.Manifest.permission.HIGH_SAMPLING_RATE_SENSORS
    )

    @MockK
    lateinit var viewModel: DetectionViewModel

    @Before
    fun setUp() {
        MockKAnnotations.init(this)
        
        // 模拟ViewModel状态
        every { viewModel.uiState } returns flowOf(
            DetectionUiState(
                tiltAngle = 3.0,
                isIdealAngle = true
            )
        )
    }

    @Test
    fun testAngleIndicatorDisplayed() {
        composeTestRule.setContent {
            ColonyTheme {
                DetectionScreen(
                    viewModel = viewModel,
                    onNavigateBack = {},
                    onDetectionComplete = {}
                )
            }
        }

        // 验证角度指示器显示
        composeTestRule
            .onNodeWithText("3.0°")
            .assertIsDisplayed()
    }

    @Test
    fun testAngleIndicatorUpdates() {
        // 模拟角度变化
        every { viewModel.uiState } returns flowOf(
            DetectionUiState(
                tiltAngle = 6.0,
                isIdealAngle = false
            )
        )

        composeTestRule.setContent {
            ColonyTheme {
                DetectionScreen(
                    viewModel = viewModel,
                    onNavigateBack = {},
                    onDetectionComplete = {}
                )
            }
        }

        // 验证角度指示器更新
        composeTestRule
            .onNodeWithText("6.0°")
            .assertIsDisplayed()

        // 验证提示文本
        composeTestRule
            .onNodeWithText("请调整角度")
            .assertIsDisplayed()
    }

    @Test
    fun testCaptureButtonDisabledOnInvalidAngle() {
        // 模拟不理想角度
        every { viewModel.uiState } returns flowOf(
            DetectionUiState(
                tiltAngle = 10.0,
                isIdealAngle = false
            )
        )

        composeTestRule.setContent {
            ColonyTheme {
                DetectionScreen(
                    viewModel = viewModel,
                    onNavigateBack = {},
                    onDetectionComplete = {}
                )
            }
        }

        // 验证拍照按钮是否禁用
        composeTestRule
            .onNodeWithContentDescription("拍照")
            .assertIsNotEnabled()
    }

    @Test
    fun testCaptureButtonEnabledOnValidAngle() {
        // 模拟理想角度
        every { viewModel.uiState } returns flowOf(
            DetectionUiState(
                tiltAngle = 3.0,
                isIdealAngle = true
            )
        )

        composeTestRule.setContent {
            ColonyTheme {
                DetectionScreen(
                    viewModel = viewModel,
                    onNavigateBack = {},
                    onDetectionComplete = {}
                )
            }
        }

        // 验证拍照按钮是否启用
        composeTestRule
            .onNodeWithContentDescription("拍照")
            .assertIsEnabled()
    }

    @Test
    fun testErrorDisplay() {
        // 模拟错误状态
        every { viewModel.uiState } returns flowOf(
            DetectionUiState(
                error = "请调整设备角度至5°以内"
            )
        )

        composeTestRule.setContent {
            ColonyTheme {
                DetectionScreen(
                    viewModel = viewModel,
                    onNavigateBack = {},
                    onDetectionComplete = {}
                )
            }
        }

        // 验证错误提示显示
        composeTestRule
            .onNodeWithText("请调整设备角度至5°以内")
            .assertIsDisplayed()
    }

    @Test
    fun testPermissionRequest() {
        // 模拟缺少权限的情况
        composeTestRule.setContent {
            ColonyTheme {
                DetectionScreen(
                    viewModel = viewModel,
                    onNavigateBack = {},
                    onDetectionComplete = {}
                )
            }
        }

        // 验证权限请求界面
        composeTestRule
            .onNodeWithText("需要传感器权限")
            .assertIsDisplayed()
    }
}
