package com.bohuyshan.microai.colony

import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.ImageButton
import android.widget.TextView
import androidx.recyclerview.widget.RecyclerView
import com.google.android.material.button.MaterialButton
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

class ProjectAdapter(
    private val onSelect: (ProjectRepository.Project) -> Unit,
    private val onDelete: (ProjectRepository.Project) -> Unit
) : RecyclerView.Adapter<ProjectAdapter.ProjectViewHolder>() {

    private val items = mutableListOf<ProjectRepository.Project>()
    private var currentProject: String = ProjectRepository.DEFAULT_PROJECT_NAME
    private val dateFormat = SimpleDateFormat("yyyy-MM-dd HH:mm", Locale.getDefault())

    fun submit(projects: List<ProjectRepository.Project>, current: String) {
        items.clear()
        items.addAll(projects.sortedBy { it.createdAt })
        currentProject = current
        notifyDataSetChanged()
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): ProjectViewHolder {
        val view = LayoutInflater.from(parent.context).inflate(R.layout.item_project, parent, false)
        return ProjectViewHolder(view)
    }

    override fun onBindViewHolder(holder: ProjectViewHolder, position: Int) {
        holder.bind(items[position], currentProject)
    }

    override fun getItemCount(): Int = items.size

    inner class ProjectViewHolder(itemView: View) : RecyclerView.ViewHolder(itemView) {
        private val nameTv: TextView = itemView.findViewById(R.id.tv_project_name)
        private val timeTv: TextView = itemView.findViewById(R.id.tv_project_time)
        private val selectBtn: MaterialButton = itemView.findViewById(R.id.btn_select)
        private val deleteBtn: ImageButton = itemView.findViewById(R.id.btn_delete)

        fun bind(project: ProjectRepository.Project, currentName: String) {
            nameTv.text = project.name
            val context = itemView.context
            val formattedDate = dateFormat.format(Date(project.createdAt))
            timeTv.text = context.getString(R.string.project_item_created_at, formattedDate)
            val isCurrent = project.name.equals(currentName, ignoreCase = true)
            selectBtn.text = if (isCurrent) {
                context.getString(R.string.project_item_current)
            } else {
                context.getString(R.string.project_item_set_current)
            }
            selectBtn.isEnabled = !isCurrent
            selectBtn.alpha = if (isCurrent) 0.6f else 1f

            selectBtn.setOnClickListener { onSelect(project) }
            deleteBtn.setOnClickListener { onDelete(project) }
        }
    }
}
