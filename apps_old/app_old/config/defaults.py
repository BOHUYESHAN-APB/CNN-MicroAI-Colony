DEFAULTS = {
    "theme": {
        "default": "siui_dark",
        "available": ["siui_dark", "py_onedark"]
    },
    "locale": "en",
    "interface": {
        "start_maximized": False,
        "recent_projects": [],
        "toolbar_style": "icon_text",
        "status_bar": True,
        "last_directory": ""
    },
    "project": {
        "default_path": "",
        "auto_save": True,
        "save_interval": 300,
        "backup_count": 5
    },
    "analysis": {
        "default_iterations": 100,
        "confidence_threshold": 0.5,
        "min_size": 5,
        "max_size": 100,
        "use_gpu": True,
        "batch_size": 4,
        "parallel_processing": True
    },
    "export": {
        "json": True,
        "csv": True,
        "excel": False,
        "image": True,
        "format": {
            "date": "YYYY-MM-DD",
            "time": "HH:mm:ss",
            "decimal_places": 2,
            "delimiter": ","
        },
        "auto_export": False,
        "export_directory": ""
    },
    "display": {
        "chart_style": "dark",
        "result_preview_size": [400, 300],
        "thumbnail_size": 48,
        "show_confidence": True,
        "show_area": True,
        "show_density": True,
        "marker_color": "#00ff00",
        "marker_size": 2
    },
    "notifications": {
        "analysis_complete": True,
        "analysis_error": True,
        "auto_save": False,
        "updates": True
    },
    "updates": {
        "check_on_startup": True,
        "check_interval": 86400,
        "last_check": "",
        "channel": "stable",
        "auto_download": False
    },
    "advanced": {
        "debug_mode": False,
        "logging_level": "INFO",
        "max_recent_projects": 10,
        "clear_temp_on_exit": True,
        "temp_directory": "",
        "plugin_directory": ""
    }
}
