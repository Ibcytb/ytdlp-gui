"""
Build script for creating Windows executable
Run this script with: python build.py
"""
import subprocess
import sys
import os
from pathlib import Path


def main():
    print("=" * 60)
    print("YouTube Downloader - Build Script")
    print("=" * 60)
    print()

    # Check if running on Windows
    if sys.platform != "win32":
        print("Warning: This build script is designed for Windows.")
        print("You can still build, but the executable will be for your current platform.")
        response = input("Continue? (y/n): ")
        if response.lower() != 'y':
            sys.exit(0)

    # Install dependencies
    print("Installing dependencies...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])

    print()
    print("Building executable with PyInstaller...")

    # Get customtkinter path
    import customtkinter
    ctk_path = Path(customtkinter.__file__).parent

    # PyInstaller command
    cmd = [
        "pyinstaller",
        "--noconfirm",
        "--onefile",
        "--windowed",
        "--name", "YouTubeDownloader",
        f"--add-data={ctk_path};customtkinter/",
        "youtube_downloader.py"
    ]

    subprocess.check_call(cmd)

    print()
    print("=" * 60)
    print("Build completed successfully!")
    print("Executable location: dist/YouTubeDownloader.exe")
    print("=" * 60)
    print()
    print("Note: Make sure yt-dlp is installed on the target system")
    print("Users can install it with: pip install yt-dlp")


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as e:
        print(f"\nError during build: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nBuild cancelled by user")
        sys.exit(1)
