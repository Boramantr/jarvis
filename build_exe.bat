@echo off
REM ============================================================
REM  JARVIS — .exe build script
REM  Output: dist\JARVIS\JARVIS.exe (+ _internal\)
REM ============================================================
title JARVIS Build
cd /d "%~dp0"

echo [1/3] PyInstaller kontrol ediliyor...
python -m PyInstaller --version >nul 2>&1
if errorlevel 1 (
    echo PyInstaller kuruluyor...
    python -m pip install pyinstaller
)

echo [2/3] Build baslatiliyor (birkac dakika surebilir)...
python -m PyInstaller jarvis.spec --noconfirm --clean

echo [3/3] Tamamlandi.
echo.
echo Calistirmak icin: dist\JARVIS\JARVIS.exe
echo API anahtarini dist\JARVIS\config\api_keys.json icine koyabilirsiniz.
pause
