package com.microai.colony.ui.screens.model

import android.net.Uri
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.Delete
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import com.microai.colony.data.model.ModelInfo
import java.io.File

@Composable
fun ModelImportScreen(
    onNavigateBack: () -> Unit,
    viewModel: ModelImportViewModel = hiltViewModel()
) {
    val context = LocalContext.current
    val uiState by viewModel.uiState.collectAsState()
    val models by viewModel.models.collectAsState()
    var showImportDialog by remember { mutableStateOf(false) }
    var selectedUri by remember { mutableStateOf<Uri?>(null) }
    var modelName by remember { mutableStateOf("") }

    val launcher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.GetContent()
    ) { uri: Uri? ->
        uri?.let {
            selectedUri = it
            showImportDialog = true
        }
    }

    LaunchedEffect(uiState) {
        if (uiState is ModelImportUiState.Success) {
            showImportDialog = false
            selectedUri = null
            modelName = ""
            viewModel.resetState()
        }
    }

    Scaffold(
        topBar = {
            SmallTopAppBar(
                title = { Text("Model Management") },
                navigationIcon = {
                    IconButton(onClick = onNavigateBack) {
                        Icon(Icons.Default.Add, null)
                    }
                }
            )
        },
        floatingActionButton = {
            FloatingActionButton(
                onClick = { launcher.launch("*/*") }
            ) {
                Icon(Icons.Default.Add, "Import Model")
            }
        }
    ) { padding ->
        Box(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
        ) {
            LazyColumn(
                modifier = Modifier.fillMaxSize(),
                contentPadding = PaddingValues(16.dp)
            ) {
                items(models) { model ->
                    ModelItem(
                        model = model,
                        onDelete = { viewModel.deleteModel(model) },
                        onActivate = { viewModel.setActiveModel(model.id) }
                    )
                    Spacer(modifier = Modifier.height(8.dp))
                }
            }

            if (uiState is ModelImportUiState.Loading) {
                CircularProgressIndicator(
                    modifier = Modifier.align(Alignment.Center)
                )
            }

            if (showImportDialog && selectedUri != null) {
                AlertDialog(
                    onDismissRequest = { showImportDialog = false },
                    title = { Text("Import Model") },
                    text = {
                        OutlinedTextField(
                            value = modelName,
                            onValueChange = { modelName = it },
                            label = { Text("Model Name") }
                        )
                    },
                    confirmButton = {
                        Button(
                            onClick = {
                                viewModel.importModel(selectedUri!!, modelName)
                            },
                            enabled = modelName.isNotBlank()
                        ) {
                            Text("Import")
                        }
                    },
                    dismissButton = {
                        TextButton(onClick = { showImportDialog = false }) {
                            Text("Cancel")
                        }
                    }
                )
            }
            
            if (uiState is ModelImportUiState.Error) {
                val error = (uiState as ModelImportUiState.Error).message
                AlertDialog(
                    onDismissRequest = { viewModel.resetState() },
                    title = { Text("Error") },
                    text = { Text(error) },
                    confirmButton = {
                        Button(onClick = { viewModel.resetState() }) {
                            Text("OK")
                        }
                    }
                )
            }
        }
    }
}

@Composable
private fun ModelItem(
    model: ModelInfo,
    onDelete: () -> Unit,
    onActivate: () -> Unit
) {
    Card(
        modifier = Modifier.fillMaxWidth()
    ) {
        Row(
            modifier = Modifier
                .padding(16.dp)
                .fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Column {
                Text(
                    text = model.name,
                    style = MaterialTheme.typography.titleMedium
                )
                Text(
                    text = "Type: ${model.type}",
                    style = MaterialTheme.typography.bodyMedium
                )
                Text(
                    text = "Size: ${File(model.path).length() / 1024}KB",
                    style = MaterialTheme.typography.bodySmall
                )
            }
            
            Row {
                if (!model.isActive) {
                    TextButton(onClick = onActivate) {
                        Text("Activate")
                    }
                }
                
                IconButton(onClick = onDelete) {
                    Icon(Icons.Default.Delete, "Delete Model")
                }
            }
        }
    }
}
