@echo off
title Building Hello TUI
chcp 65001 > nul

echo.
echo ========================================
echo        BUILDING HELLO TUI
echo ========================================
echo.

:: Check if PyInstaller is installed
python -c "import pyinstaller" 2>nul
if errorlevel 1 (
    echo ❌ PyInstaller not found! Installing...
    pip install pyinstaller
)

:: Create directories if they don't exist
if not exist "..\dist" mkdir "..\dist"
if not exist "..\build" mkdir "..\build"

echo.
echo 🛠️  Building executable...
echo.

:: Build the executable
pyinstaller --onefile --console ^
    --name "HelloTUI" ^
    --distpath "..\dist" ^
    --workpath "..\build" ^
    --specpath "..\build" ^
    "..\src\hello_tui.py"

if errorlevel 1 (
    echo.
    echo ❌ Build failed!
    pause
    exit /b 1
)

echo.
echo ========================================
echo        BUILD COMPLETE! ✅
echo ========================================
echo.
echo 📁 Executable location: ..\dist\HelloTUI.exe
echo.
echo 🚀 To test the executable, run:
echo    dist\HelloTUI.exe
echo.
pause