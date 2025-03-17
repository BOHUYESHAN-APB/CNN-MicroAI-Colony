#!/usr/bin/env python3
"""
Create translation files using basic format
"""
import os
import json

def create_translations():
    """Create translation files in a simple format"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    translations_dir = os.path.join(base_dir, "app", "resources", "i18n")

    # Create translations directory if it doesn't exist
    os.makedirs(translations_dir, exist_ok=True)

    # Translation data
    translations = {
        "en": {
            "main.title": "CNN Analyzer",
            "status.language_changed": "Language changed to {locale}",
            "error.language_change_failed": "Failed to change language to {locale}",
            "menu.language": "Language",
            "menu.file": "File",
            "menu.help": "Help",
            "menu.help.about": "About",
            "dialog.error": "Error",
            "settings.title": "Settings",
            "settings.language": "Language",
            "settings.theme": "Theme",
            "settings.tab.general": "General",
            "settings.tab.display": "Display",
            "settings.tab.analysis": "Analysis",
            "dialog.ok": "OK",
            "dialog.cancel": "Cancel",
            "dialog.apply": "Apply"
        },
        "zh_CN": {
            "main.title": "CNN分析器",
            "status.language_changed": "已切换语言至{locale}",
            "error.language_change_failed": "切换语言至{locale}失败",
            "menu.language": "语言",
            "menu.file": "文件",
            "menu.help": "帮助",
            "menu.help.about": "关于",
            "dialog.error": "错误",
            "settings.title": "设置",
            "settings.language": "语言",
            "settings.theme": "主题",
            "settings.tab.general": "常规",
            "settings.tab.display": "显示",
            "settings.tab.analysis": "分析",
            "dialog.ok": "确定",
            "dialog.cancel": "取消",
            "dialog.apply": "应用"
        },
        "zh_TW": {
            "main.title": "CNN分析器",
            "status.language_changed": "已切換語言至{locale}",
            "error.language_change_failed": "切換語言至{locale}失敗",
            "menu.language": "語言",
            "menu.file": "檔案",
            "menu.help": "說明",
            "menu.help.about": "關於",
            "dialog.error": "錯誤",
            "settings.title": "設定",
            "settings.language": "語言",
            "settings.theme": "主題",
            "settings.tab.general": "一般",
            "settings.tab.display": "顯示",
            "settings.tab.analysis": "分析",
            "dialog.ok": "確定",
            "dialog.cancel": "取消",
            "dialog.apply": "套用"
        }
    }

    # Save each translation to a file
    for locale, messages in translations.items():
        file_path = os.path.join(translations_dir, f"{locale}.json")
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(messages, f, ensure_ascii=False, indent=4)
        print(f"Generated {file_path}")

if __name__ == "__main__":
    create_translations()
