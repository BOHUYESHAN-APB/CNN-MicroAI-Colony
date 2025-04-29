package com.microai.colony.ui.navigation

import androidx.compose.runtime.Composable
import androidx.navigation.NavHostController
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import com.microai.colony.ui.screens.analysis.AnalysisScreen
import com.microai.colony.ui.screens.detection.DetectionScreen
import com.microai.colony.ui.screens.history.HistoryScreen
import com.microai.colony.ui.screens.home.HomeScreen
import com.microai.colony.ui.screens.model.ModelImportScreen
import com.microai.colony.ui.screens.settings.SettingsScreen

@Composable
fun NavGraph(
    navController: NavHostController,
    startDestination: String = NavigationRoutes.Home.route
) {
    NavHost(
        navController = navController,
        startDestination = startDestination
    ) {
        composable(NavigationRoutes.Home.route) {
            HomeScreen(
                onNavigateToDetection = { 
                    navController.navigate(NavigationRoutes.Detection.route)
                },
                onNavigateToModelImport = {
                    navController.navigate(NavigationRoutes.ModelImport.route)
                }
            )
        }
        
        composable(NavigationRoutes.Detection.route) {
            DetectionScreen(
                onNavigateBack = { navController.popBackStack() }
            )
        }
        
        composable(NavigationRoutes.History.route) {
            HistoryScreen(
                onNavigateBack = { navController.popBackStack() }
            )
        }
        
        composable(NavigationRoutes.Analysis.route) {
            AnalysisScreen(
                onNavigateBack = { navController.popBackStack() }
            )
        }
        
        composable(NavigationRoutes.Settings.route) {
            SettingsScreen(
                onNavigateBack = { navController.popBackStack() }
            )
        }
        
        composable(NavigationRoutes.ModelImport.route) {
            ModelImportScreen(
                onNavigateBack = { navController.popBackStack() }
            )
        }
    }
}
