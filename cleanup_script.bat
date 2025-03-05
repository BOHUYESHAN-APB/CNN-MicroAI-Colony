@echo off
chcp 65001 >nul
:: 自动生成的清理脚本 - 使用前请仔细审查！
mkdir backup 2>nul

:: 检查目录是否存在
if not exist backup\ (
    echo 错误：无法创建备份目录
    exit /b 1
)

:: 移动大文件到备份目录

:: 删除临时文件