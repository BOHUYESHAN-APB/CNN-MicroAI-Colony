package com.bohuyshan.microai.colony

import android.content.Context
import org.json.JSONArray
import org.json.JSONObject
import java.io.File

object ProjectRepository {
    private const val PREFS_NAME = "microai_project_prefs"
    private const val KEY_PROJECTS = "projects"
    private const val KEY_CURRENT = "current_project"
    const val DEFAULT_PROJECT_NAME = "Default Project"

    data class Project(
        val name: String,
        val createdAt: Long
    )

    private fun prefs(context: Context) =
        context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)

    private fun defaultProjectName(context: Context): String =
        context.getString(R.string.project_default_name)

    fun getProjects(context: Context): List<Project> {
        val projects = loadProjects(context)
        return projects.ifEmpty {
            val defaultName = defaultProjectName(context)
            val default = Project(defaultName, System.currentTimeMillis())
            saveProjects(context, listOf(default))
            setCurrentProject(context, default.name)
            listOf(default)
        }
    }

    fun addProject(context: Context, name: String): Project {
        val trimmed = name.trim()
    require(trimmed.isNotEmpty()) { "Project name cannot be empty" }
        val projects = loadProjects(context).toMutableList()
        if (projects.any { it.name.equals(trimmed, ignoreCase = true) }) {
            val existing = projects.first { it.name.equals(trimmed, ignoreCase = true) }
            setCurrentProject(context, existing.name)
            return existing
        }
        val project = Project(trimmed, System.currentTimeMillis())
        projects.add(project)
        saveProjects(context, projects)
        setCurrentProject(context, project.name)
        return project
    }

    fun setCurrentProject(context: Context, name: String) {
        val projects = loadProjects(context)
        val exists = projects.any { it.name.equals(name, ignoreCase = true) }
        if (!exists) {
            val fallback = getProjects(context).first().name
            prefs(context).edit().putString(KEY_CURRENT, fallback).apply()
        } else {
            prefs(context).edit().putString(KEY_CURRENT, name).apply()
        }
    }

    fun getCurrentProject(context: Context): String {
        val prefs = prefs(context)
        val stored = prefs.getString(KEY_CURRENT, null)
        if (stored != null && loadProjects(context).any { it.name.equals(stored, ignoreCase = true) }) {
            return stored
        }
        val first = getProjects(context).first().name
        prefs.edit().putString(KEY_CURRENT, first).apply()
        return first
    }

    fun removeProject(context: Context, name: String) {
        val projects = loadProjects(context).toMutableList()
    if (projects.size <= 1) return // Ensure at least one project remains
        val removed = projects.removeIf { it.name.equals(name, ignoreCase = true) }
        if (removed) {
            saveProjects(context, projects)
            val current = prefs(context).getString(KEY_CURRENT, defaultProjectName(context))
            if (current.equals(name, ignoreCase = true)) {
                val fallback = projects.firstOrNull()?.name ?: defaultProjectName(context)
                prefs(context).edit().putString(KEY_CURRENT, fallback).apply()
            }
            // Delete the corresponding directory on disk
            val dir = getProjectAlbumDir(context, name)
            if (dir.exists()) {
                dir.deleteRecursively()
            }
        }
    }

    fun getProjectAlbumDir(context: Context, name: String): File {
        val base = File(context.filesDir, "album")
        if (!base.exists()) base.mkdirs()
        val slug = slugify(name)
        val dir = File(base, slug)
        if (!dir.exists()) dir.mkdirs()
        return dir
    }

    fun slugify(name: String): String {
        val trimmed = name.trim().ifEmpty { DEFAULT_PROJECT_NAME }
        return trimmed.replace("[^a-zA-Z0-9-_]".toRegex(), "_")
    }

    private fun loadProjects(context: Context): MutableList<Project> {
        val prefs = prefs(context)
        val raw = prefs.getString(KEY_PROJECTS, null) ?: return mutableListOf()
        if (raw.isBlank()) return mutableListOf()
        val arr = JSONArray(raw)
        val list = mutableListOf<Project>()
        for (i in 0 until arr.length()) {
            val obj = arr.optJSONObject(i) ?: continue
            val rawName = obj.optString("name")
            if (rawName.isBlank()) continue
            val createdAt = obj.optLong("createdAt", System.currentTimeMillis())
            list.add(Project(rawName, createdAt))
        }
        return list
    }

    private fun saveProjects(context: Context, projects: List<Project>) {
        val arr = JSONArray()
        projects.sortedBy { it.createdAt }.forEach { project ->
            val obj = JSONObject()
            obj.put("name", project.name)
            obj.put("createdAt", project.createdAt)
            arr.put(obj)
        }
        prefs(context).edit().putString(KEY_PROJECTS, arr.toString()).apply()
    }
}
