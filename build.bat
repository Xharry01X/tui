@echo off
title Building Chatty Patty
chcp 65001 > nul

echo.
echo ========================================
echo        BUILDING Chatty Patty
echo ========================================
echo.


python -c "import pyinstaller" 2>nul
if errorlevel 1 (
    echo Installing PyInstaller...
    pip install pyinstaller
)

:: Install textual
pip install textual

echo.
echo Building executable...
echo.

:: Build the executable
pyinstaller --onefile --console ^
    --name "ChattyPatty" ^
    --collect-all textual ^
    main.py

if errorlevel 1 (
    echo.
    echo Build failed!
    pause
    exit /b 1
)

echo.
echo ========================================
echo        BUILD COMPLETE!
echo ========================================
echo.
echo Executable: dist\ChattyPatty.exe
echo.
echo To run: dist\ChattyPatty.exe
echo.
pause