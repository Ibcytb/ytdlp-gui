@echo off
echo Building YouTube Downloader for Windows...
echo.

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

REM Build executable
echo.
echo Building executable with PyInstaller...
pyinstaller --noconfirm --onefile --windowed ^
    --name "YouTubeDownloader" ^
    --icon=NONE ^
    --add-data "venv/Lib/site-packages/customtkinter;customtkinter/" ^
    youtube_downloader.py

echo.
echo Build complete! Executable is in the 'dist' folder.
echo.
pause
