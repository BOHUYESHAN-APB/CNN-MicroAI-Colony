package com.microai.colony.ui.components

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp

/**
 * 权限请求组件
 */
@Composable
fun PermissionRequest(
    title: String,
    description: String,
    onRequestPermission: () -> Unit,
    modifier: Modifier = Modifier
) {
    Column(
        modifier = modifier
            .fillMaxSize()
            .padding(16.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        Icon(
            imageVector = Icons.Filled.PermDeviceInformation,
            contentDescription = null,
            modifier = Modifier.size(72.dp),
            tint = MaterialTheme.colorScheme.primary
        )
        
        Spacer(modifier = Modifier.height(16.dp))
        
        Text(
            text = title,
            style = MaterialTheme.typography.titleLarge,
            textAlign = TextAlign.Center
        )
        
        Spacer(modifier = Modifier.height(8.dp))
        
        Text(
            text = description,
            style = MaterialTheme.typography.bodyMedium,
            textAlign = TextAlign.Center,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )
        
        Spacer(modifier = Modifier.height(24.dp))
        
        Button(onClick = onRequestPermission) {
            Text(text = "授予权限")
        }
    }
}

/**
 * 多权限请求组件
 */
@Composable
fun MultiplePermissionsRequest(
    permissions: List<PermissionRequest>,
    onRequestPermissions: () -> Unit,
    modifier: Modifier = Modifier
) {
    Column(
        modifier = modifier
            .fillMaxSize()
            .padding(16.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        Icon(
            imageVector = Icons.Filled.Security,
            contentDescription = null,
            modifier = Modifier.size(72.dp),
            tint = MaterialTheme.colorScheme.primary
        )
        
        Spacer(modifier = Modifier.height(16.dp))
        
        Text(
            text = "需要以下权限",
            style = MaterialTheme.typography.titleLarge,
            textAlign = TextAlign.Center
        )
        
        Spacer(modifier = Modifier.height(16.dp))
        
        permissions.forEach { permission ->
            Surface(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(vertical = 4.dp),
                color = MaterialTheme.colorScheme.surfaceVariant,
                shape = MaterialTheme.shapes.medium
            ) {
                Column(
                    modifier = Modifier.padding(16.dp)
                ) {
                    Text(
                        text = permission.title,
                        style = MaterialTheme.typography.titleMedium
                    )
                    Text(
                        text = permission.description,
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
            }
        }
        
        Spacer(modifier = Modifier.height(24.dp))
        
        Button(onClick = onRequestPermissions) {
            Text(text = "授予权限")
        }
    }
}

/**
 * 权限请求数据类
 */
data class PermissionRequest(
    val permission: String,
    val title: String,
    val description: String
)

@Preview(showBackground = true)
@Composable
fun PermissionRequestPreview() {
    ColonyTheme {
        PermissionRequest(
            title = "相机权限",
            description = "需要相机权限来进行实时检测和拍照",
            onRequestPermission = {}
        )
    }
}

@Preview(showBackground = true)
@Composable
fun MultiplePermissionsRequestPreview() {
    ColonyTheme {
        MultiplePermissionsRequest(
            permissions = listOf(
                PermissionRequest(
                    permission = Manifest.permission.CAMERA,
                    title = "相机权限",
                    description = "需要相机权限来进行实时检测和拍照"
                ),
                PermissionRequest(
                    permission = Manifest.permission.READ_MEDIA_IMAGES,
                    title = "存储权限",
                    description = "需要存储权限来保存检测结果"
                )
            ),
            onRequestPermissions = {}
        )
    }
}
