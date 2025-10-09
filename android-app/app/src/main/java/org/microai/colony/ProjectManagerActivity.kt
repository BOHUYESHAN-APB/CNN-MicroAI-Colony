package com.bohuyshan.microai.colony

import android.os.Bundle
import android.view.LayoutInflater
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import com.google.android.material.appbar.MaterialToolbar
import com.google.android.material.dialog.MaterialAlertDialogBuilder
import com.google.android.material.floatingactionbutton.FloatingActionButton

class ProjectManagerActivity : AppCompatActivity() {

    private lateinit var adapter: ProjectAdapter

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_project_manager)

        val toolbar = findViewById<MaterialToolbar>(R.id.project_toolbar)
        val list = findViewById<RecyclerView>(R.id.project_list)
        val fab = findViewById<FloatingActionButton>(R.id.fab_add_project)

        toolbar.setNavigationOnClickListener { finish() }

        adapter = ProjectAdapter(
            onSelect = { project ->
                ProjectRepository.setCurrentProject(this, project.name)
                Toast.makeText(this, getString(R.string.project_switched_message, project.name), Toast.LENGTH_SHORT).show()
                refreshProjects()
            },
            onDelete = { project -> confirmDelete(project) }
        )

        list.layoutManager = LinearLayoutManager(this)
        list.adapter = adapter

        fab.setOnClickListener { showAddDialog() }

        refreshProjects()
    }

    private fun refreshProjects() {
        val projects = ProjectRepository.getProjects(this)
        val current = ProjectRepository.getCurrentProject(this)
        adapter.submit(projects, current)
    }

    private fun showAddDialog() {
        val input = LayoutInflater.from(this).inflate(R.layout.dialog_text_input, null)
        val editText = input.findViewById<com.google.android.material.textfield.TextInputEditText>(R.id.dialog_input)
        editText.hint = getString(R.string.project_name_hint)

        val dialog = MaterialAlertDialogBuilder(this)
            .setTitle(R.string.project_add_title)
            .setView(input)
            .setNegativeButton(R.string.common_cancel, null)
            .setPositiveButton(R.string.common_save, null)
            .create()

        dialog.setOnShowListener {
            dialog.getButton(androidx.appcompat.app.AlertDialog.BUTTON_POSITIVE).setOnClickListener {
                val name = editText.text.toString().trim()
                if (name.isEmpty()) {
                    editText.error = getString(R.string.project_name_empty_error)
                } else {
                    ProjectRepository.addProject(this, name)
                    Toast.makeText(this, getString(R.string.project_created_message, name), Toast.LENGTH_SHORT).show()
                    refreshProjects()
                    dialog.dismiss()
                }
            }
        }
        dialog.show()
    }

    private fun confirmDelete(project: ProjectRepository.Project) {
        val current = ProjectRepository.getCurrentProject(this)
        if (current.equals(project.name, ignoreCase = true)) {
            Toast.makeText(this, getString(R.string.project_delete_blocked), Toast.LENGTH_SHORT).show()
            return
        }
        MaterialAlertDialogBuilder(this)
            .setTitle(R.string.project_delete_title)
            .setMessage(getString(R.string.project_delete_message, project.name))
            .setNegativeButton(R.string.common_cancel, null)
            .setPositiveButton(R.string.common_delete) { _, _ ->
                ProjectRepository.removeProject(this, project.name)
                refreshProjects()
            }
            .show()
    }
}
