@echo off
echo Starting IB YouTube Downloader...
echo.

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    call venv\Scripts\activate.bat
    echo Installing dependencies...
    pip install -r requirements.txt
) else (
    call venv\Scripts\activate.bat

    REM Check if dependencies are already installed
    echo Checking dependencies...
    python -c "import customtkinter; import yt_dlp" 2>nul
    if errorlevel 1 (
        echo Installing missing dependencies...
        pip install -r requirements.txt
    ) else (
        echo All dependencies are installed. Skipping download...
    )
)

REM Run the application
python youtube_downloader.py

pause
