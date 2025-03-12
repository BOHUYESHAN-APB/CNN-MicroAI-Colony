@echo off
echo Running debug script...
echo Current directory: %CD%
echo.
..\\.venv\Scripts\python.exe debug_config.py > debug_output.txt 2>&1
echo Debug output saved to debug_output.txt
type debug_output.txt
