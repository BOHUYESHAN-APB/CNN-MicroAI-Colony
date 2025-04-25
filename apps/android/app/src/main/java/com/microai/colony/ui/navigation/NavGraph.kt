package com.microai.colony.ui.navigation

import androidx.compose.runtime.Composable
import androidx.navigation.NavHostController
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import com.microai.colony.ui.screens.detection.DetectionScreen
import com.microai.colony.ui.screens.history.HistoryScreen
import com.microai.colony.ui.screens.home.HomeScreen
import com.microai.colony.ui.screens.settings.SettingsScreen
import com.microai.colony.ui.screens.analysis.AnalysisScreen

/**
 * 导航路径
 */
sealed class NavRoutes(val route: String) {
    object Home : NavRoutes("home")
    object Detection : NavRoutes("detection")
    object History : NavRoutes("history")
    object Analysis : NavRoutes("analysis")
    object Settings : NavRoutes("settings")
    
    // 带参数的路由
    object DetectionResult : NavRoutes("detection_result/{imageUri}") {
        fun createRoute(imageUri: String) = "detection_result/$imageUri"
    }
    
    object HistoryDetail : NavRoutes("history_detail/{id}") {
        fun createRoute(id: Long) = "history_detail/$id"
    }
}

/**
 * 应用导航图
 */
@Composable
fun ColonyNavGraph(
    navController: NavHostController,
    startDestination: String = NavRoutes.Home.route
) {
    NavHost(
        navController = navController,
        startDestination = startDestination
    ) {
        composable(NavRoutes.Home.route) {
            HomeScreen(
                onNavigateToDetection = {
                    navController.navigate(NavRoutes.Detection.route)
                },
                onNavigateToHistory = {
                    navController.navigate(NavRoutes.History.route)
                },
                onNavigateToAnalysis = {
                    navController.navigate(NavRoutes.Analysis.route)
                }
            )
        }
        
        composable(NavRoutes.Detection.route) {
            DetectionScreen(
                onNavigateBack = {
                    navController.popBackStack()
                },
                onDetectionComplete = { imageUri ->
                    navController.navigate(NavRoutes.DetectionResult.createRoute(imageUri))
                }
            )
        }
        
        composable(NavRoutes.History.route) {
            HistoryScreen(
                onNavigateBack = {
                    navController.popBackStack()
                },
                onItemClick = { id ->
                    navController.navigate(NavRoutes.HistoryDetail.createRoute(id))
                }
            )
        }
        
        composable(NavRoutes.Analysis.route) {
            AnalysisScreen(
                onNavigateBack = {
                    navController.popBackStack()
                }
            )
        }
        
        composable(NavRoutes.Settings.route) {
            SettingsScreen(
                onNavigateBack = {
                    navController.popBackStack()
                }
            )
        }
    }
}

/**
 * 导航操作扩展
 */
fun NavHostController.navigateAndPopUp(route: String, popUp: String) {
    navigate(route) {
        popUpTo(popUp) {
            inclusive = true
        }
    }
}

fun NavHostController.navigateSingleTop(route: String) {
    navigate(route) {
        launchSingleTop = true
    }
}

fun NavHostController.clearAndNavigate(route: String) {
    navigate(route) {
        popUpTo(0) {
            inclusive = true
        }
    }
}
