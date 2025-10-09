package com.bohuyshan.microai.colony

import android.content.Context

object InferencePreferences {
    private const val PREFS_NAME = "inference_prefs"
    private const val KEY_PREFERRED = "preferred_engine"
    private const val KEY_ALLOW_GPU = "allow_gpu"
    private const val KEY_ALLOW_NPU = "allow_npu"
    private const val KEY_ALLOW_CPU = "allow_cpu"

    enum class Engine(val key: String) {
        GPU("gpu"),
        NPU("npu"),
        CPU("cpu");

        companion object {
            fun fromKey(key: String?): Engine = when (key) {
                GPU.key -> GPU
                NPU.key -> NPU
                else -> CPU
            }
        }
    }

    private fun prefs(context: Context) =
        context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)

    fun getPreferredEngine(context: Context): Engine {
        val value = prefs(context).getString(KEY_PREFERRED, Engine.GPU.key)
        return Engine.fromKey(value)
    }

    fun setPreferredEngine(context: Context, engine: Engine) {
        prefs(context).edit().putString(KEY_PREFERRED, engine.key).apply()
    }

    fun isEngineAllowed(context: Context, engine: Engine): Boolean {
        val prefs = prefs(context)
        return when (engine) {
            Engine.GPU -> prefs.getBoolean(KEY_ALLOW_GPU, true)
            Engine.NPU -> prefs.getBoolean(KEY_ALLOW_NPU, true)
            Engine.CPU -> prefs.getBoolean(KEY_ALLOW_CPU, true)
        }
    }

    fun setEngineAllowed(context: Context, engine: Engine, allowed: Boolean) {
        val prefs = prefs(context)
        when (engine) {
            Engine.GPU -> prefs.edit().putBoolean(KEY_ALLOW_GPU, allowed).apply()
            Engine.NPU -> prefs.edit().putBoolean(KEY_ALLOW_NPU, allowed).apply()
            Engine.CPU -> prefs.edit().putBoolean(KEY_ALLOW_CPU, allowed).apply()
        }
    }
}
