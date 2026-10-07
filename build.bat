@echo off
setlocal
cd /d %~dp0
python scripts\build_release.py
if errorlevel 1 exit /b 1
echo.
echo Success: dist\Marrow.exe
endlocal
