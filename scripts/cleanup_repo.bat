@echo off
setlocal enabledelayedexpansion

:: 设置UTF-8编码
chcp 65001 > nul

echo 仓库清理脚本 - 自动创建备份并执行清理

:: 检查是否在Git仓库中
if not exist ".git" (
    echo 错误：当前目录不是Git仓库
    exit /b 1
)

:: 创建时间戳
for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set datetime=%%I
set timestamp=%datetime:~0,8%_%datetime:~8,6%

:: 创建备份
echo 创建备份...
set "backup_dir=backup_%timestamp%"
mkdir "%backup_dir%"
if errorlevel 1 (
    echo 错误：无法创建备份目录
    exit /b 1
)

:: 备份.git目录
echo 备份.git目录...
xcopy /E /I /H ".git" "%backup_dir%\.git"
if errorlevel 1 (
    echo 错误：备份.git目录失败
    exit /b 1
)

:: 创建仓库镜像
echo 创建仓库镜像...
git clone --mirror . "%backup_dir%\repo.git"
if errorlevel 1 (
    echo 错误：创建仓库镜像失败
    exit /b 1
)

:: 更新.gitignore
echo 配置.gitignore...
(
echo # Python
echo venv/
echo env/
echo __pycache__/
echo *.pyc
echo *.pyo
echo *.pyd
echo.
echo # Model files
echo checkpoints/
echo *.weights
echo *.pth
echo *.h5
echo *.onnx
echo.
echo # Large files
echo *.zip
echo *.tar.gz
echo *.rar
echo.
echo # Development
echo .vscode/
echo .idea/
echo *.log
echo.
echo # Data
echo data/raw/
echo pic/higher-resolution/
echo pic/lower-resolution/
) > .gitignore

:: 配置Git LFS
echo 配置Git LFS...
git lfs install
if errorlevel 1 (
    echo 错误：Git LFS安装失败
    echo 请先安装Git LFS：https://git-lfs.com
    exit /b 1
)

:: 配置LFS跟踪
for %%f in (
    "*.pth" "*.weights" "*.h5" "*.onnx"
    "*.jpg" "*.png" "*.jpeg" "*.gif"
    "*.zip" "*.tar.gz" "*.rar"
) do (
    git lfs track %%f
)

:: 提交.gitattributes
git add .gitattributes
git commit -m "Configure Git LFS tracking"

:: 下载BFG
if not exist "bfg.jar" (
    echo 下载BFG工具...
    powershell -Command "& {Invoke-WebRequest -Uri 'https://repo1.maven.org/maven2/com/madgag/bfg/1.14.0/bfg-1.14.0.jar' -OutFile 'bfg.jar'}"
)

:: 使用BFG清理大文件
echo 清理大文件...
java -jar bfg.jar --strip-blobs-bigger-than 100M .
if errorlevel 1 (
    echo 错误：BFG清理失败
    echo 请确保已安装Java
    exit /b 1
)

:: 清理和压缩仓库
echo 压缩仓库...
git reflog expire --expire=now --all
git gc --prune=now --aggressive

echo.
echo 清理完成！请检查以下内容：
echo.
echo 1. 检查清理结果：
echo    git status
echo    git lfs ls-files
echo.
echo 2. 如果确认无误，强制推送更改：
echo    git push origin --force --all
echo    git push origin --force --tags
echo.
echo 3. 如果需要回滚，使用备份恢复：
echo    xcopy /E /I /H "%backup_dir%\.git" .git
echo.
echo 备份目录：%backup_dir%
echo 更多详细说明请查看：CLEANUP_STEPS.md
echo.
pause
