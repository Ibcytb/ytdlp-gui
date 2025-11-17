# YouTube Downloader Pro (yt-dlp)

A professional, feature-rich Windows GUI application for downloading YouTube videos and audio using yt-dlp.

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

## 🎯 Features (기능)

### Video Download
- **Complete Quality Range**: 144p, 240p, 360p, 480p, 640p, 720p, 1080p, 2K (1440p), 4K (2160p), 8K (4320p), and best quality
- **Video Codec Selection**: Choose from AV1, VP9, VP8, AVC (H.264), or automatic selection
- **Container Format Selection**: MP4, MKV, WebM, AVI (with automatic conversion if needed)

### Audio Download
- **High-Quality Audio Extraction**: 64, 96, 128, 192, 256, 320 kbps, or best quality
- **Multiple Audio Formats**: MP3, AAC, Opus, M4A, WAV, FLAC
- **Dedicated Audio Settings**: Separate interface for audio-only downloads

### General Features
- **Smart Video Analysis**: Analyze videos before download to detect available qualities and formats
- **Availability Detection**: Automatically marks unavailable quality/bitrate options as "(사용 불가)"
- **Responsive UI**: Window size adapts to your screen resolution and DPI scaling
- **Modern Scrollable GUI**: Clean and intuitive interface with CustomTkinter
- **Dynamic Options**: Interface adapts based on Video/Audio selection
- **Real-time Progress Tracking**: Live download progress and detailed status
- **Custom Download Location**: Choose where to save your downloads
- **Comprehensive Logging**: View detailed download progress, errors, and yt-dlp commands
- **Smart Format Selection**: Automatic fallback if requested format is unavailable

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
2. **Analyze Video** (Recommended): Click "Analyze" to detect available qualities
   - Shows maximum available video quality and audio bitrate
   - Automatically marks unavailable options as "(사용 불가)"
   - Displays video title for confirmation
3. **Select Download Type**: Choose between Video or Audio Only
4. **Configure Options**:
   - **For Video**:
     - Select video quality (144p to 8K)
     - Choose video codec (AV1, VP9, VP8, H.264, or any)
     - Pick container format (MP4, MKV, WebM, AVI)
   - **For Audio**:
     - Select audio quality/bitrate (64 kbps to 320 kbps or best)
     - Choose audio format (MP3, AAC, Opus, M4A, WAV, FLAC)
5. **Choose Download Location**: Browse to select where to save
6. **Click Download**: Start downloading!

### Interface (인터페이스)

The application features:
- **URL input field** with "Analyze" button
- **Analysis status bar** showing max quality, audio bitrate, and video title
- **Dynamic format selection** (Video/Audio) that adapts the interface
- **Responsive window** that scales with your screen resolution
- **Scrollable interface** for comfortable viewing of all options
- **Comprehensive video options panel**:
  - Quality selector with full range (144p-8K)
  - Video codec selector
  - Container format selector
- **Comprehensive audio options panel**:
  - Bitrate/quality selector (64-320 kbps)
  - Audio format selector
- **Download location browser**
- **Real-time progress bar** with percentage
- **Detailed log output** showing yt-dlp commands and progress
- **Smart availability indicators**: Options show "(사용 불가)" if not available

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

### Using the Analyzer
- **Always analyze first**: Click "Analyze" before downloading to see what's actually available
- The analyzer shows the maximum quality available for the specific video
- If you see "(사용 불가)", that quality is not available from YouTube for this video
- The "best" option always works and automatically selects the highest available quality
- Analysis may take 5-30 seconds depending on the video and network speed

### Video Downloads
- For highest quality, select "best" quality and "any" codec
- AV1 codec provides the best compression but may not be available for all videos
- VP9 is a good balance between quality and compatibility
- H.264 (AVC) has the widest compatibility across devices
- Use MP4 or MKV for maximum compatibility
- 8K and 4K videos may take significant time to download

### Audio Downloads
- For highest quality, select "best" or "320 kbps"
- MP3 is the most universally compatible format
- FLAC and WAV provide lossless quality but larger file sizes
- Opus provides excellent quality at lower bitrates
- AAC is a good choice for Apple devices

### General
- The log window shows the exact yt-dlp command being executed
- If a specific codec or quality isn't available, yt-dlp will automatically fall back to the next best option
- Downloaded files are named automatically based on the video title
- The application automatically merges video and audio streams for the best quality

## 🔗 Links

- [yt-dlp GitHub](https://github.com/yt-dlp/yt-dlp)
- [CustomTkinter Documentation](https://github.com/TomSchimansky/CustomTkinter)

---

Made with ❤️ using Python and CustomTkinter