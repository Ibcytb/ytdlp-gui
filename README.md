# YouTube Downloader GUI (yt-dlp)

A modern, user-friendly Windows GUI application for downloading YouTube videos using yt-dlp.

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

## 🎯 Features (기능)

- **Modern GUI**: Clean and intuitive interface using CustomTkinter
- **Video & Audio Download**: Download videos or extract audio only (MP3)
- **Quality Selection**: Choose from multiple quality options (best, 1080p, 720p, 480p, 360p)
- **Progress Tracking**: Real-time download progress and status
- **Custom Download Location**: Choose where to save your downloads
- **Detailed Logging**: View download progress and errors in real-time

## 📋 Requirements (요구사항)

- Python 3.8 or higher
- Windows OS (primary target)
- Internet connection
- yt-dlp (automatically installed with requirements)

## 🚀 Quick Start (빠른 시작)

### Method 1: Run from Source (소스에서 실행)

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd ytdlp-gui
   ```

2. **Run the application:**
   - **Windows**: Double-click `run.bat`
   - **Linux/Mac**: Run `bash run.sh`

   Or manually:
   ```bash
   # Create virtual environment
   python -m venv venv

   # Activate virtual environment
   # Windows:
   venv\Scripts\activate
   # Linux/Mac:
   source venv/bin/activate

   # Install dependencies
   pip install -r requirements.txt

   # Run the application
   python youtube_downloader.py
   ```

### Method 2: Build Executable (실행 파일 빌드)

For a standalone Windows executable:

```bash
# Using Python build script
python build.py

# Or using batch file (Windows only)
build_windows.bat
```

The executable will be created in the `dist/` folder.

## 📦 Installation (설치)

### Install Dependencies (의존성 설치)

```bash
pip install -r requirements.txt
```

### Required Packages:

- `yt-dlp`: YouTube video downloader
- `customtkinter`: Modern GUI framework
- `Pillow`: Image processing
- `pyinstaller`: For building executables

## 💡 Usage (사용법)

1. **Enter Video URL**: Paste the YouTube video URL
2. **Select Format**: Choose between Video or Audio only
3. **Select Quality**: Pick your preferred quality
4. **Choose Download Location**: Browse to select where to save
5. **Click Download**: Start downloading!

### Screenshots (스크린샷)

The application features:
- URL input field
- Format selection (Video/Audio)
- Quality dropdown menu
- Download location selector
- Progress bar with status
- Real-time log output

## 🛠️ Building for Windows (Windows용 빌드)

### Using the Build Script:

```bash
python build.py
```

### Manual PyInstaller Build:

```bash
pyinstaller --noconfirm --onefile --windowed \
    --name "YouTubeDownloader" \
    --add-data "venv/Lib/site-packages/customtkinter;customtkinter/" \
    youtube_downloader.py
```

## 📁 Project Structure (프로젝트 구조)

```
ytdlp-gui/
├── youtube_downloader.py   # Main application
├── requirements.txt        # Python dependencies
├── build.py               # Build script
├── build_windows.bat      # Windows build script
├── run.bat               # Windows run script
├── run.sh                # Linux/Mac run script
├── .gitignore           # Git ignore file
└── README.md            # This file
```

## 🔧 Configuration (설정)

The application uses the following default settings:

- **Default Download Location**: User's Downloads folder
- **Appearance**: Dark mode
- **Theme**: Blue

You can modify these in the `youtube_downloader.py` file.

## ⚠️ Troubleshooting (문제 해결)

### yt-dlp not found

If you get an error that yt-dlp is not found:

```bash
pip install yt-dlp
# Or globally:
pip install --user yt-dlp
```

### Build Issues

If you encounter issues building the executable:

1. Make sure all dependencies are installed
2. Try updating PyInstaller: `pip install --upgrade pyinstaller`
3. Check that customtkinter is properly installed

### Download Errors

- Verify the URL is correct and accessible
- Check your internet connection
- Some videos may have download restrictions
- Try updating yt-dlp: `pip install --upgrade yt-dlp`

## 📝 License

This project is open source and available under the MIT License.

## 🤝 Contributing (기여하기)

Contributions are welcome! Feel free to:

- Report bugs
- Suggest new features
- Submit pull requests

## 📚 About yt-dlp

[yt-dlp](https://github.com/yt-dlp/yt-dlp) is a feature-rich command-line audio/video downloader with enhanced capabilities compared to youtube-dl. It supports:

- YouTube and 1000+ other sites
- Playlist downloads
- Subtitle downloads
- Format selection
- And much more!

## ⚡ Tips (팁)

- For best quality, select "best" in the quality dropdown
- Audio-only downloads are saved as MP3 files
- The application shows real-time progress in the log window
- Downloaded files are named automatically based on the video title

## 🔗 Links

- [yt-dlp GitHub](https://github.com/yt-dlp/yt-dlp)
- [CustomTkinter Documentation](https://github.com/TomSchimansky/CustomTkinter)

---

Made with ❤️ using Python and CustomTkinter