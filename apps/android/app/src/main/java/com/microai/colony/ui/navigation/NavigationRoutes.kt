package com.microai.colony.ui.navigation

sealed class NavigationRoutes(val route: String) {
    data object Home : NavigationRoutes("home")
    data object Detection : NavigationRoutes("detection")
    data object History : NavigationRoutes("history")
    data object Analysis : NavigationRoutes("analysis")
    data object Settings : NavigationRoutes("settings")
    data object ModelImport : NavigationRoutes("model_import")
}
