@echo off
REM Create temporary directory for best model checkpoint
mkdir temp_checkpoints

REM Copy best model files
xcopy /s /i /y checkpoints\run_20250303_142756\checkpoint_epoch_31.pth temp_checkpoints\
xcopy /s /i /y checkpoints\run_20250303_142756\metrics_history.json temp_checkpoints\
xcopy /s /i /y checkpoints\run_20250303_142756\training.log temp_checkpoints\

REM Remove old checkpoints directory and rename temp
rmdir /s /q checkpoints
rename temp_checkpoints checkpoints

REM Remove empty init files
for /r . %%f in (__init__.py) do if %%~zf==0 del "%%f"

echo Cleanup completed. Kept best model checkpoint and removed unnecessary files.
