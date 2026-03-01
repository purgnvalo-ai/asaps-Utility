@echo off
title FPS Utility — Build Script
color 0B

echo.
echo  ██████╗ ██╗   ██╗██╗██╗     ██████╗     ███████╗██╗  ██╗███████╗
echo  ██╔══██╗██║   ██║██║██║     ██╔══██╗    ██╔════╝╚██╗██╔╝██╔════╝
echo  ██████╔╝██║   ██║██║██║     ██║  ██║    █████╗   ╚███╔╝ █████╗
echo  ██╔══██╗██║   ██║██║██║     ██║  ██║    ██╔══╝   ██╔██╗ ██╔══╝
echo  ██████╔╝╚██████╔╝██║███████╗██████╔╝    ███████╗██╔╝ ██╗███████╗
echo  ╚═════╝  ╚═════╝ ╚═╝╚══════╝╚═════╝     ╚══════╝╚═╝  ╚═╝╚══════╝
echo.
echo  FPS Utility Lite — Build System
echo  ─────────────────────────────────────────────────────────────────
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Python not found. Download from https://python.org
    echo          Make sure to check "Add Python to PATH" during install.
    pause
    exit /b 1
)

echo  [1/4] Python found. Installing dependencies...
pip install pyinstaller --quiet
if errorlevel 1 (
    echo  [ERROR] Failed to install PyInstaller.
    pause
    exit /b 1
)
echo  [OK]   PyInstaller installed.
echo.

:: Create icon if not present
echo  [2/4] Preparing build files...
if not exist icon.ico (
    echo         No icon.ico found — building without custom icon.
    set ICON_FLAG=
) else (
    set ICON_FLAG=--icon=icon.ico
)

echo  [3/4] Compiling FPS Utility Lite.exe ...
echo.
pyinstaller ^
    --onefile ^
    --windowed ^
    --name "FPS Utility Lite" ^
    --uac-admin ^
    --clean ^
    %ICON_FLAG% ^
    main.py

if errorlevel 1 (
    echo.
    echo  [ERROR] Build failed. Check the output above for details.
    pause
    exit /b 1
)

echo.
echo  [4/4] Cleaning up build artifacts...
rmdir /s /q build >nul 2>&1
del /q "FPS Utility Lite.spec" >nul 2>&1

echo.
echo  ─────────────────────────────────────────────────────────────────
echo  [DONE]  dist\FPS Utility Lite.exe is ready!
echo.
echo  Right-click → Run as Administrator (required for system tweaks)
echo  ─────────────────────────────────────────────────────────────────
echo.
pause
