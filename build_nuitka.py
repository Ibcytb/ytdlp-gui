#!/usr/bin/env python3
"""
Build script for IB YouTube Downloader using Nuitka
Alternative to PyInstaller - creates faster, smaller executables
"""

import subprocess
import sys
import os
from pathlib import Path

def main():
    print("=" * 50)
    print("IB YouTube Downloader - Nuitka Build")
    print("=" * 50)
    print()

    # Check if Nuitka is installed
    try:
        result = subprocess.run([sys.executable, "-m", "nuitka", "--version"],
                               capture_output=True, text=True)
        if result.returncode != 0:
            print("Nuitka not found. Installing...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "nuitka"])
    except FileNotFoundError:
        print("Nuitka not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "nuitka"])

    # Get customtkinter path for including data files
    import customtkinter
    ctk_path = Path(customtkinter.__file__).parent

    # Build command
    cmd = [
        sys.executable, "-m", "nuitka",
        "--standalone",
        "--onefile",
        "--windows-console-mode=disable",  # No console window (GUI app)
        "--output-filename=IB_YouTube_Downloader",
        f"--include-data-dir={ctk_path}=customtkinter",
        "--include-data-file=lang_ko.json=lang_ko.json",
        "--include-data-file=lang_en.json=lang_en.json",
        "--include-package=yt_dlp",
        "--include-package=customtkinter",
        "--include-package=PIL",
        "--enable-plugin=tk-inter",
        "--follow-imports",
        "--assume-yes-for-downloads",  # Auto download missing dependencies
        "youtube_downloader.py"
    ]

    # Add Windows-specific options
    if sys.platform == "win32":
        cmd.extend([
            "--windows-icon-from-ico=icon.ico" if os.path.exists("icon.ico") else "",
            "--company-name=IB",
            "--product-name=IB YouTube Downloader",
            "--file-version=1.0.0",
            "--product-version=1.0.0",
        ])
        # Remove empty strings
        cmd = [c for c in cmd if c]

    print("Build command:")
    print(" ".join(cmd))
    print()

    print("Starting Nuitka compilation...")
    print("This may take several minutes...")
    print()

    try:
        subprocess.check_call(cmd)

        print()
        print("=" * 50)
        print("Build completed successfully!")
        print("=" * 50)

        # Find the output
        if sys.platform == "win32":
            exe_name = "IB_YouTube_Downloader.exe"
        else:
            exe_name = "IB_YouTube_Downloader"

        # Check in dist folder or current directory
        possible_paths = [
            Path("IB_YouTube_Downloader.dist") / exe_name,
            Path(exe_name),
            Path("IB_YouTube_Downloader.onefile-build") / exe_name,
        ]

        for path in possible_paths:
            if path.exists():
                print(f"Executable location: {path.absolute()}")
                break
        else:
            print("Check the output directory for the executable.")

    except subprocess.CalledProcessError as e:
        print()
        print("=" * 50)
        print(f"Build failed with error code: {e.returncode}")
        print("=" * 50)
        print()
        print("Troubleshooting tips:")
        print("1. Make sure you have a C compiler installed")
        print("   - Windows: Visual Studio Build Tools or MinGW")
        print("   - Linux: gcc (sudo apt install build-essential)")
        print("   - macOS: Xcode Command Line Tools")
        print("2. Try running: pip install nuitka --upgrade")
        print("3. Check if all dependencies are installed")
        sys.exit(1)

if __name__ == "__main__":
    main()
