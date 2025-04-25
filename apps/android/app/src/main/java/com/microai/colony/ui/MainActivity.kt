package com.microai.colony.ui

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.navigation.NavDestination.Companion.hierarchy
import androidx.navigation.NavGraph.Companion.findStartDestination
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.compose.rememberNavController
import com.microai.colony.R
import com.microai.colony.ui.navigation.ColonyNavGraph
import com.microai.colony.ui.navigation.NavRoutes
import com.microai.colony.ui.theme.ColonyTheme
import dagger.hilt.android.AndroidEntryPoint

@AndroidEntryPoint
class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            ColonyTheme {
                MainScreen()
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun MainScreen() {
    val navController = rememberNavController()
    val navBackStackEntry by navController.currentBackStackEntryAsState()
    val currentDestination = navBackStackEntry?.destination
    
    Scaffold(
        bottomBar = {
            NavigationBar {
                val items = listOf(
                    Triple(
                        NavRoutes.Home.route,
                        stringResource(R.string.main_title),
                        Icons.Filled.Home
                    ),
                    Triple(
                        NavRoutes.History.route,
                        stringResource(R.string.history_title),
                        Icons.Filled.History
                    ),
                    Triple(
                        NavRoutes.Analysis.route,
                        stringResource(R.string.analysis_title),
                        Icons.Filled.Analytics
                    ),
                    Triple(
                        NavRoutes.Settings.route,
                        stringResource(R.string.settings_title),
                        Icons.Filled.Settings
                    )
                )
                
                items.forEach { (route, title, icon) ->
                    NavigationBarItem(
                        icon = { Icon(icon, contentDescription = title) },
                        label = { Text(title) },
                        selected = currentDestination?.hierarchy?.any { it.route == route } == true,
                        onClick = {
                            navController.navigate(route) {
                                popUpTo(navController.graph.findStartDestination().id) {
                                    saveState = true
                                }
                                launchSingleTop = true
                                restoreState = true
                            }
                        }
                    )
                }
            }
        }
    ) { innerPadding ->
        Box(
            modifier = Modifier
                .fillMaxSize()
                .padding(innerPadding)
        ) {
            ColonyNavGraph(navController)
        }
    }
}

/**
 * 预览函数
 */
@Preview(showBackground = true)
@Composable
fun MainScreenPreview() {
    ColonyTheme {
        MainScreen()
    }
}
