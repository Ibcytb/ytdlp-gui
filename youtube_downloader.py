import customtkinter as ctk
from tkinter import filedialog, messagebox
import os
import sys
import threading
import subprocess
import json
import re
import platform
import tempfile
import shutil
from pathlib import Path
from urllib.request import urlretrieve
try:
    from PIL import Image
    from io import BytesIO
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

# Set appearance
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class LanguageManager:
    def __init__(self, lang_code="ko"):
        self.lang_code = lang_code
        self.translations = {}
        self.load_language(lang_code)

    def load_language(self, lang_code):
        """Load language file (JSON format)"""
        lang_file = Path(__file__).parent / f"lang_{lang_code}.json"
        try:
            with open(lang_file, 'r', encoding='utf-8') as f:
                self.translations = json.load(f)
            self.lang_code = lang_code
        except FileNotFoundError:
            print(f"Language file not found: {lang_file}")
            # Fallback to English
            if lang_code != "en":
                self.load_language("en")

    def get(self, key, **kwargs):
        """Get translated text"""
        text = self.translations.get(key, key)
        if kwargs:
            return text.format(**kwargs)
        return text


class BrowserDetector:
    """Detect installed browsers and their profiles"""

    @staticmethod
    def get_user_home():
        """Get user home directory"""
        return Path.home()

    @staticmethod
    def detect_browsers():
        """Detect installed browsers on the system"""
        browsers = {}
        home = BrowserDetector.get_user_home()
        system = platform.system()

        if system == "Windows":
            browser_paths = {
                "chrome": home / "AppData/Local/Google/Chrome/User Data",
                "firefox": home / "AppData/Roaming/Mozilla/Firefox/Profiles",
                "edge": home / "AppData/Local/Microsoft/Edge/User Data",
                "opera": home / "AppData/Roaming/Opera Software/Opera Stable",
                "brave": home / "AppData/Local/BraveSoftware/Brave-Browser/User Data",
                "chromium": home / "AppData/Local/Chromium/User Data",
            }
        elif system == "Darwin":  # macOS
            browser_paths = {
                "chrome": home / "Library/Application Support/Google/Chrome",
                "firefox": home / "Library/Application Support/Firefox/Profiles",
                "edge": home / "Library/Application Support/Microsoft Edge",
                "opera": home / "Library/Application Support/com.operasoftware.Opera",
                "brave": home / "Library/Application Support/BraveSoftware/Brave-Browser",
                "safari": home / "Library/Safari",
                "chromium": home / "Library/Application Support/Chromium",
            }
        else:  # Linux
            browser_paths = {
                "chrome": home / ".config/google-chrome",
                "firefox": home / ".mozilla/firefox",
                "chromium": home / ".config/chromium",
                "opera": home / ".config/opera",
                "brave": home / ".config/BraveSoftware/Brave-Browser",
            }

        for browser, path in browser_paths.items():
            if path.exists():
                browsers[browser] = path

        return browsers

    @staticmethod
    def get_profiles(browser_name, browser_path):
        """Get user profiles for a specific browser"""
        profiles = []

        try:
            if browser_name == "firefox":
                # Firefox profiles are in subdirectories
                if browser_path.exists():
                    for profile_dir in browser_path.iterdir():
                        if profile_dir.is_dir() and not profile_dir.name.startswith('.'):
                            profiles.append(profile_dir.name)
            else:
                # Chromium-based browsers
                if browser_path.exists():
                    # Check for Default profile
                    if (browser_path / "Default").exists():
                        profiles.append("Default")

                    # Check for Profile 1, Profile 2, etc.
                    profile_num = 1
                    while (browser_path / f"Profile {profile_num}").exists():
                        profiles.append(f"Profile {profile_num}")
                        profile_num += 1
        except Exception as e:
            print(f"Error getting profiles for {browser_name}: {e}")

        return profiles if profiles else ["Default"]


class YouTubeDownloaderGUI:
    def __init__(self):
        self.window = ctk.CTk()

        # Language manager
        self.lang = LanguageManager("ko")  # Default Korean

        self.window.title(self.lang.get("app_title"))

        # Default download path
        self.download_path = str(Path.home() / "Downloads")

        # Available formats data
        self.available_formats = None
        self.max_height = None
        self.max_audio_bitrate = None

        # Auto-analysis flag
        self.auto_analyzing = False
        self.last_url = ""

        # Thumbnail cache
        self.thumbnail_cache_dir = Path(tempfile.gettempdir()) / "ytdlp_gui_thumbnails"
        self.thumbnail_cache_dir.mkdir(exist_ok=True)
        self.thumbnail_cache = {}  # url -> (local_path, ctk_image)

        # Detect installed browsers
        self.browsers = BrowserDetector.detect_browsers()
        self.browser_profiles = {}

        # Set responsive window size
        self.set_responsive_size()

        # Check and update yt-dlp
        self.check_ytdlp_update()

        # Initialize UI
        self.create_widgets()

        # Center window
        self.center_window()

    def set_responsive_size(self):
        """Set window size based on screen resolution and DPI scaling"""
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()

        # Calculate appropriate window size
        window_height = min(int(screen_height * 0.80), 1100)
        window_width = min(int(window_height * 0.9), 950)

        # Ensure minimum size
        window_width = max(window_width, 750)
        window_height = max(window_height, 750)

        self.window.geometry(f"{window_width}x{window_height}")
        self.window.minsize(750, 750)

    def center_window(self):
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f'{width}x{height}+{x}+{y}')

    def check_ytdlp_update(self):
        """Check and update yt-dlp at startup"""
        def update_thread():
            try:
                # Check if yt-dlp is installed
                result = subprocess.run(
                    ["yt-dlp", "--version"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )

                if result.returncode == 0:
                    # Update yt-dlp
                    subprocess.run(
                        ["yt-dlp", "-U"],
                        capture_output=True,
                        timeout=30
                    )
            except:
                pass

        thread = threading.Thread(target=update_thread)
        thread.daemon = True
        thread.start()

    def create_widgets(self):
        # Create scrollable frame
        self.main_frame = ctk.CTkScrollableFrame(self.window)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Top bar with title and settings
        top_frame = ctk.CTkFrame(self.main_frame)
        top_frame.pack(pady=(10, 20), padx=20, fill="x")

        title_label = ctk.CTkLabel(
            top_frame,
            text=self.lang.get("app_title").split("(")[0].strip(),
            font=ctk.CTkFont(size=28, weight="bold")
        )
        title_label.pack(side="left", padx=10)

        # Language selector and tools
        lang_frame = ctk.CTkFrame(top_frame)
        lang_frame.pack(side="right", padx=10)

        lang_label = ctk.CTkLabel(lang_frame, text=self.lang.get("language"), font=ctk.CTkFont(size=12))
        lang_label.pack(side="left", padx=5)

        self.lang_var = ctk.StringVar(value="한국어")
        lang_menu = ctk.CTkComboBox(
            lang_frame,
            values=["English", "한국어"],
            variable=self.lang_var,
            command=self.change_language,
            width=100
        )
        lang_menu.pack(side="left", padx=5)

        # Edit translation button
        edit_trans_btn = ctk.CTkButton(
            lang_frame,
            text="✏",  # Edit icon
            command=self.open_translation_editor,
            width=30
        )
        edit_trans_btn.pack(side="left", padx=2)

        # Add language button
        add_lang_btn = ctk.CTkButton(
            lang_frame,
            text="+",  # Add icon
            command=self.add_new_language,
            width=30
        )
        add_lang_btn.pack(side="left", padx=2)

        # URL Frame
        url_frame = ctk.CTkFrame(self.main_frame)
        url_frame.pack(pady=10, padx=20, fill="x")

        url_label = ctk.CTkLabel(url_frame, text=self.lang.get("video_url"), font=ctk.CTkFont(size=14, weight="bold"))
        url_label.pack(anchor="w", padx=10, pady=(10, 5))

        # Use textbox for multiple URLs
        self.url_entry = ctk.CTkTextbox(
            url_frame,
            height=80,
            font=ctk.CTkFont(size=12)
        )
        self.url_entry.pack(padx=10, pady=(0, 5), fill="x")
        self.url_entry.insert("1.0", "https://www.youtube.com/watch?v=...")

        # Info label for multiple URLs
        url_info_label = ctk.CTkLabel(
            url_frame,
            text=self.lang.get("multi_url_info") if hasattr(self, 'lang') else "Enter one URL per line for batch download",
            font=ctk.CTkFont(size=10),
            text_color="gray"
        )
        url_info_label.pack(anchor="w", padx=10, pady=(0, 5))

        # Bind URL entry to detect paste
        self.url_entry.bind('<KeyRelease>', self.on_url_change)
        self.url_entry.bind('<<Paste>>', self.on_url_paste)

        # Analysis Status Textbox (for multiple results)
        self.analysis_status = ctk.CTkTextbox(
            url_frame,
            height=60,
            font=ctk.CTkFont(size=11)
        )
        self.analysis_status.pack(padx=10, pady=(5, 10), fill="x")
        self.analysis_status.configure(state="disabled")  # Read-only

        # Cookie Settings Frame
        cookie_frame = ctk.CTkFrame(self.main_frame)
        cookie_frame.pack(pady=10, padx=20, fill="x")

        cookie_title = ctk.CTkLabel(cookie_frame, text=self.lang.get("cookie_settings"), font=ctk.CTkFont(size=14, weight="bold"))
        cookie_title.pack(anchor="w", padx=10, pady=(10, 5))

        cookie_options_frame = ctk.CTkFrame(cookie_frame)
        cookie_options_frame.pack(padx=10, pady=(0, 10), fill="x")

        self.use_cookies_var = ctk.BooleanVar(value=False)
        cookie_check = ctk.CTkCheckBox(
            cookie_options_frame,
            text=self.lang.get("use_cookies"),
            variable=self.use_cookies_var,
            command=self.toggle_cookie_options
        )
        cookie_check.grid(row=0, column=0, padx=10, pady=5, sticky="w")

        browser_label = ctk.CTkLabel(cookie_options_frame, text=self.lang.get("browser"), font=ctk.CTkFont(size=12))
        browser_label.grid(row=1, column=0, padx=10, pady=5, sticky="w")

        # Get list of detected browsers or show message
        browser_list = list(self.browsers.keys()) if self.browsers else [self.lang.get("no_browsers_found")]
        default_browser = browser_list[0] if browser_list else ""

        self.browser_var = ctk.StringVar(value=default_browser)
        self.browser_menu = ctk.CTkComboBox(
            cookie_options_frame,
            values=browser_list,
            variable=self.browser_var,
            width=150,
            state="disabled",
            command=self.on_browser_change
        )
        self.browser_menu.grid(row=1, column=1, padx=10, pady=5, sticky="w")

        profile_label = ctk.CTkLabel(cookie_options_frame, text=self.lang.get("profile"), font=ctk.CTkFont(size=12))
        profile_label.grid(row=2, column=0, padx=10, pady=5, sticky="w")

        self.profile_var = ctk.StringVar(value="Default")
        self.profile_menu = ctk.CTkComboBox(
            cookie_options_frame,
            values=["Default"],
            variable=self.profile_var,
            width=150,
            state="disabled"
        )
        self.profile_menu.grid(row=2, column=1, padx=10, pady=(5, 10), sticky="w")

        # Load initial profiles
        if self.browsers and default_browser:
            self.load_browser_profiles(default_browser)

        # Format Selection Frame
        self.format_frame = ctk.CTkFrame(self.main_frame)
        self.format_frame.pack(pady=10, padx=20, fill="x")

        format_title = ctk.CTkLabel(self.format_frame, text=self.lang.get("download_type"), font=ctk.CTkFont(size=14, weight="bold"))
        format_title.pack(anchor="w", padx=10, pady=(10, 5))

        format_select_frame = ctk.CTkFrame(self.format_frame)
        format_select_frame.pack(padx=10, pady=(0, 10), fill="x")

        # Use checkboxes instead of radio buttons for multiple selection
        self.download_video_var = ctk.BooleanVar(value=True)
        format_check1 = ctk.CTkCheckBox(
            format_select_frame,
            text=self.lang.get("video"),
            variable=self.download_video_var,
            command=self.toggle_options,
            font=ctk.CTkFont(size=13)
        )
        format_check1.pack(side="left", padx=20, pady=10)

        self.download_audio_var = ctk.BooleanVar(value=False)
        format_check2 = ctk.CTkCheckBox(
            format_select_frame,
            text=self.lang.get("audio_only"),
            variable=self.download_audio_var,
            command=self.toggle_options,
            font=ctk.CTkFont(size=13)
        )
        format_check2.pack(side="left", padx=20, pady=10)

        self.download_thumbnail_var = ctk.BooleanVar(value=False)
        format_check3 = ctk.CTkCheckBox(
            format_select_frame,
            text=self.lang.get("thumbnail_only"),
            variable=self.download_thumbnail_var,
            command=self.toggle_options,
            font=ctk.CTkFont(size=13)
        )
        format_check3.pack(side="left", padx=20, pady=10)

        self.download_subtitle_var = ctk.BooleanVar(value=False)
        format_check4 = ctk.CTkCheckBox(
            format_select_frame,
            text=self.lang.get("batch_subtitle") if "batch_subtitle" in self.lang.translations else "자막",
            variable=self.download_subtitle_var,
            command=self.toggle_options,
            font=ctk.CTkFont(size=13)
        )
        format_check4.pack(side="left", padx=20, pady=10)

        # Embed Options Frame
        embed_frame = ctk.CTkFrame(self.format_frame)
        embed_frame.pack(padx=10, pady=(0, 10), fill="x")

        embed_title = ctk.CTkLabel(
            embed_frame,
            text=self.lang.get("embed_options"),
            font=ctk.CTkFont(size=12, weight="bold")
        )
        embed_title.grid(row=0, column=0, columnspan=2, padx=10, pady=(5, 5), sticky="w")

        self.embed_thumbnail_var = ctk.BooleanVar(value=False)
        embed_thumbnail_check = ctk.CTkCheckBox(
            embed_frame,
            text=self.lang.get("embed_thumbnail"),
            variable=self.embed_thumbnail_var,
            font=ctk.CTkFont(size=12)
        )
        embed_thumbnail_check.grid(row=1, column=0, padx=10, pady=5, sticky="w")

        self.embed_metadata_var = ctk.BooleanVar(value=False)
        embed_metadata_check = ctk.CTkCheckBox(
            embed_frame,
            text=self.lang.get("embed_metadata"),
            variable=self.embed_metadata_var,
            font=ctk.CTkFont(size=12)
        )
        embed_metadata_check.grid(row=1, column=1, padx=10, pady=5, sticky="w")

        # Video Options Frame
        self.video_options_frame = ctk.CTkFrame(self.main_frame)
        self.video_options_frame.pack(pady=10, padx=20, fill="x")

        video_title = ctk.CTkLabel(
            self.video_options_frame,
            text=self.lang.get("video_options"),
            font=ctk.CTkFont(size=14, weight="bold")
        )
        video_title.grid(row=0, column=0, columnspan=3, padx=10, pady=(10, 15), sticky="w")

        # Video Quality
        quality_label = ctk.CTkLabel(self.video_options_frame, text=self.lang.get("quality"), font=ctk.CTkFont(size=13))
        quality_label.grid(row=1, column=0, padx=10, pady=10, sticky="w")

        self.video_quality_var = ctk.StringVar(value=self.lang.get("quality_best"))
        self.quality_values = []
        self.update_quality_display()

        self.quality_menu = ctk.CTkComboBox(
            self.video_options_frame,
            values=self.quality_values,
            variable=self.video_quality_var,
            width=200
        )
        self.quality_menu.grid(row=1, column=1, columnspan=2, padx=10, pady=10, sticky="w")

        # Video Codec
        codec_label = ctk.CTkLabel(self.video_options_frame, text=self.lang.get("video_codec"), font=ctk.CTkFont(size=13))
        codec_label.grid(row=2, column=0, padx=10, pady=10, sticky="w")

        self.video_codec_var = ctk.StringVar(value=self.lang.get("codec_any"))
        codec_values = [
            self.lang.get("codec_any"),
            self.lang.get("codec_av1"),
            self.lang.get("codec_vp9"),
            self.lang.get("codec_vp8"),
            self.lang.get("codec_avc")
        ]
        self.codec_menu = ctk.CTkComboBox(
            self.video_options_frame,
            values=codec_values,
            variable=self.video_codec_var,
            width=200
        )
        self.codec_menu.grid(row=2, column=1, columnspan=2, padx=10, pady=10, sticky="w")

        # Audio Bitrate for Video
        audio_br_label = ctk.CTkLabel(self.video_options_frame, text=self.lang.get("audio_bitrate"), font=ctk.CTkFont(size=13))
        audio_br_label.grid(row=3, column=0, padx=10, pady=10, sticky="w")

        self.video_audio_quality_var = ctk.StringVar(value=self.lang.get("bitrate_best"))
        self.video_audio_values = []
        self.update_audio_quality_display()

        self.video_audio_menu = ctk.CTkComboBox(
            self.video_options_frame,
            values=self.video_audio_values,
            variable=self.video_audio_quality_var,
            width=200
        )
        self.video_audio_menu.grid(row=3, column=1, columnspan=2, padx=10, pady=10, sticky="w")

        # Video Container
        container_label = ctk.CTkLabel(self.video_options_frame, text=self.lang.get("container"), font=ctk.CTkFont(size=13))
        container_label.grid(row=4, column=0, padx=10, pady=10, sticky="w")

        self.video_container_var = ctk.StringVar(value="mp4")
        self.container_menu = ctk.CTkComboBox(
            self.video_options_frame,
            values=["mp4", "mkv", "webm", "avi", self.lang.get("custom_format")],
            variable=self.video_container_var,
            command=self.on_container_change,
            width=200
        )
        self.container_menu.grid(row=4, column=1, columnspan=2, padx=10, pady=10, sticky="w")

        self.custom_container_entry = ctk.CTkEntry(
            self.video_options_frame,
            placeholder_text="e.g., mov, flv",
            width=200
        )

        # Audio Options Frame
        self.audio_options_frame = ctk.CTkFrame(self.main_frame)

        audio_title = ctk.CTkLabel(
            self.audio_options_frame,
            text=self.lang.get("audio_options"),
            font=ctk.CTkFont(size=14, weight="bold")
        )
        audio_title.grid(row=0, column=0, columnspan=3, padx=10, pady=(10, 15), sticky="w")

        # Audio Quality (Bitrate)
        audio_quality_label = ctk.CTkLabel(self.audio_options_frame, text=self.lang.get("audio_quality"), font=ctk.CTkFont(size=13))
        audio_quality_label.grid(row=1, column=0, padx=10, pady=10, sticky="w")

        self.audio_quality_var = ctk.StringVar(value=self.lang.get("bitrate_192"))
        self.audio_quality_values = []
        self.update_audio_quality_display()

        self.audio_quality_menu = ctk.CTkComboBox(
            self.audio_options_frame,
            values=self.audio_quality_values,
            variable=self.audio_quality_var,
            width=200
        )
        self.audio_quality_menu.grid(row=1, column=1, columnspan=2, padx=10, pady=10, sticky="w")

        # Audio Format
        audio_format_label = ctk.CTkLabel(self.audio_options_frame, text=self.lang.get("audio_format"), font=ctk.CTkFont(size=13))
        audio_format_label.grid(row=2, column=0, padx=10, pady=10, sticky="w")

        self.audio_format_var = ctk.StringVar(value="mp3")
        self.audio_format_menu = ctk.CTkComboBox(
            self.audio_options_frame,
            values=["mp3", "aac", "opus", "m4a", "wav", "flac", self.lang.get("custom_format")],
            variable=self.audio_format_var,
            command=self.on_audio_format_change,
            width=200
        )
        self.audio_format_menu.grid(row=2, column=1, columnspan=2, padx=10, pady=10, sticky="w")

        self.custom_audio_entry = ctk.CTkEntry(
            self.audio_options_frame,
            placeholder_text="e.g., ogg, wma",
            width=200
        )

        # Subtitle Options Frame
        self.subtitle_options_frame = ctk.CTkFrame(self.main_frame)

        subtitle_title = ctk.CTkLabel(
            self.subtitle_options_frame,
            text=self.lang.get("batch_subtitle") if "batch_subtitle" in self.lang.translations else "자막 옵션",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        subtitle_title.grid(row=0, column=0, columnspan=3, padx=10, pady=(10, 15), sticky="w")

        # Subtitle Format
        subtitle_format_label = ctk.CTkLabel(self.subtitle_options_frame, text=self.lang.get("subtitle_format") if "subtitle_format" in self.lang.translations else "자막 형식:", font=ctk.CTkFont(size=13))
        subtitle_format_label.grid(row=1, column=0, padx=10, pady=10, sticky="w")

        self.subtitle_format_var = ctk.StringVar(value="srt")
        self.subtitle_format_menu = ctk.CTkComboBox(
            self.subtitle_options_frame,
            values=["srt", "vtt", "ass", "sbv"],
            variable=self.subtitle_format_var,
            width=200
        )
        self.subtitle_format_menu.grid(row=1, column=1, columnspan=2, padx=10, pady=10, sticky="w")

        # Subtitle Language
        subtitle_language_label = ctk.CTkLabel(self.subtitle_options_frame, text="자막 언어:", font=ctk.CTkFont(size=13))
        subtitle_language_label.grid(row=2, column=0, padx=10, pady=10, sticky="w")

        self.subtitle_language_var = ctk.StringVar(value="en")
        self.subtitle_language_entry = ctk.CTkEntry(
            self.subtitle_options_frame,
            textvariable=self.subtitle_language_var,
            placeholder_text="e.g., en, ko, es",
            width=200
        )
        self.subtitle_language_entry.grid(row=2, column=1, columnspan=2, padx=10, pady=10, sticky="w")

        # Download Path Frame
        path_frame = ctk.CTkFrame(self.main_frame)
        path_frame.pack(pady=10, padx=20, fill="x")

        path_label = ctk.CTkLabel(path_frame, text=self.lang.get("download_location"), font=ctk.CTkFont(size=14, weight="bold"))
        path_label.pack(anchor="w", padx=10, pady=(10, 5))

        path_select_frame = ctk.CTkFrame(path_frame)
        path_select_frame.pack(padx=10, pady=(0, 10), fill="x")

        self.path_entry = ctk.CTkEntry(
            path_select_frame,
            placeholder_text=self.download_path,
            height=35
        )
        self.path_entry.pack(side="left", padx=(0, 5), fill="x", expand=True)
        self.path_entry.insert(0, self.download_path)

        browse_button = ctk.CTkButton(
            path_select_frame,
            text=self.lang.get("browse"),
            command=self.browse_folder,
            width=100
        )
        browse_button.pack(side="right")

        # Progress Frame (in main window, not scrollable)
        self.progress_frame = ctk.CTkFrame(self.window)
        self.progress_frame.pack(pady=10, padx=20, fill="x", side="bottom")

        self.progress_label = ctk.CTkLabel(
            self.progress_frame,
            text=self.lang.get("ready"),
            font=ctk.CTkFont(size=12)
        )
        self.progress_label.pack(padx=10, pady=(10, 5))

        self.progress_bar = ctk.CTkProgressBar(self.progress_frame)
        self.progress_bar.pack(padx=10, pady=(0, 10), fill="x")
        self.progress_bar.set(0)

        # Download Button (in main window, not scrollable)
        self.download_button = ctk.CTkButton(
            self.window,
            text=self.lang.get("download"),
            command=self.start_download,
            height=45,
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.download_button.pack(pady=10, padx=20, fill="x", side="bottom")

        # Log Frame (back in scrollable frame)
        log_frame = ctk.CTkFrame(self.main_frame)
        log_frame.pack(pady=10, padx=20, fill="both", expand=True)

        log_label = ctk.CTkLabel(log_frame, text=self.lang.get("log"), font=ctk.CTkFont(size=14, weight="bold"))
        log_label.pack(anchor="w", padx=10, pady=(10, 5))

        self.log_text = ctk.CTkTextbox(log_frame, height=150, font=ctk.CTkFont(size=11))
        self.log_text.pack(padx=10, pady=(0, 10), fill="both", expand=True)

        # Bind mousewheel for faster scrolling
        self.bind_mousewheel(self.log_text)
        self.bind_mousewheel(self.url_entry)

        # Initialize options visibility
        self.toggle_options()

    def bind_mousewheel(self, widget):
        """Bind mousewheel for faster scrolling"""
        def on_mousewheel(event):
            # Scroll 5 lines at a time (default is 1)
            # CTkTextbox uses internal _textbox widget
            if hasattr(widget, '_textbox'):
                widget._textbox.yview_scroll(int(-5 * (event.delta / 120)), "units")
            return "break"

        def on_scroll_up(event):
            if hasattr(widget, '_textbox'):
                widget._textbox.yview_scroll(-5, "units")
            return "break"

        def on_scroll_down(event):
            if hasattr(widget, '_textbox'):
                widget._textbox.yview_scroll(5, "units")
            return "break"

        # Bind for Windows and Linux
        widget.bind("<MouseWheel>", on_mousewheel)
        # Bind for Linux (alternative)
        widget.bind("<Button-4>", on_scroll_up)
        widget.bind("<Button-5>", on_scroll_down)

    def change_language(self, choice):
        """Change application language"""
        lang_code = "ko" if choice == "한국어" else "en"
        self.lang.load_language(lang_code)

        # Refresh UI
        messagebox.showinfo(
            self.lang.get("success_title"),
            "Language changed. Please restart the application for full effect." if lang_code == "en"
            else "언어가 변경되었습니다. 완전한 적용을 위해 프로그램을 재시작하세요."
        )

    def toggle_cookie_options(self):
        """Enable/disable cookie options"""
        if self.use_cookies_var.get():
            self.browser_menu.configure(state="normal")
            self.profile_menu.configure(state="normal")
        else:
            self.browser_menu.configure(state="disabled")
            self.profile_menu.configure(state="disabled")

    def on_browser_change(self, choice=None):
        """Handle browser selection change"""
        browser_name = self.browser_var.get()
        if browser_name and browser_name != self.lang.get("no_browsers_found"):
            self.load_browser_profiles(browser_name)

    def load_browser_profiles(self, browser_name):
        """Load profiles for selected browser"""
        if browser_name in self.browsers:
            browser_path = self.browsers[browser_name]
            profiles = BrowserDetector.get_profiles(browser_name, browser_path)
            self.browser_profiles[browser_name] = profiles

            # Update profile menu
            if profiles:
                self.profile_menu.configure(values=profiles)
                self.profile_var.set(profiles[0])
            else:
                self.profile_menu.configure(values=["Default"])
                self.profile_var.set("Default")

    def on_url_change(self, event=None):
        """Detect URL change and trigger auto-analysis"""
        current_text = self.url_entry.get("1.0", "end").strip()

        # Get all valid URLs
        urls = [line.strip() for line in current_text.split('\n')
                if line.strip() and line.strip().startswith("http")
                and "youtube.com/watch?v=..." not in line]

        # Update UI based on URL count
        self.update_ui_for_url_count(len(urls))

        # Get first valid URL for auto-analysis
        current_url = urls[0] if urls else ""

        if current_url and current_url != self.last_url:
            self.last_url = current_url
            # Delay analysis slightly to allow full URL to be pasted
            self.window.after(500, lambda: self.auto_analyze_video(current_url))

    def on_url_paste(self, event=None):
        """Detect paste event"""
        # Wait for paste to complete
        self.window.after(100, self.on_url_change)

    def update_ui_for_url_count(self, url_count):
        """Update UI based on number of URLs"""
        if url_count > 1:
            # Multiple URLs - hide download type section and change button text
            self.format_frame.pack_forget()
            self.video_options_frame.pack_forget()
            self.audio_options_frame.pack_forget()
            self.subtitle_options_frame.pack_forget()
            self.download_button.configure(text=self.lang.get("batch_download_button")
                                          if "batch_download_button" in self.lang.translations
                                          else "일괄 다운로드 및 옵션 변경")
        else:
            # Single or no URL - show normal UI
            is_visible = False
            try:
                # Check if format_frame is currently visible
                if self.format_frame.winfo_manager():
                    is_visible = True
            except:
                pass

            if not is_visible:
                # If not visible, show it
                # Insert format_frame after URL frame (which is at index 2)
                children = list(self.main_frame.children.values())
                if len(children) >= 3:
                    self.format_frame.pack(pady=10, padx=20, fill="x", after=children[2])
                else:
                    self.format_frame.pack(pady=10, padx=20, fill="x")

            self.download_button.configure(text=self.lang.get("download"))

            # Update options visibility based on checkboxes
            self.toggle_options()

    def auto_analyze_video(self, url):
        """Automatically analyze video when URL is pasted"""
        if not self.auto_analyzing:
            # Check if URL still exists in textbox
            current_text = self.url_entry.get("1.0", "end").strip()
            if url in current_text:
                self.analyze_video()

    def on_container_change(self, choice):
        """Handle custom container format"""
        if choice == self.lang.get("custom_format"):
            self.custom_container_entry.grid(row=5, column=1, columnspan=2, padx=10, pady=5, sticky="w")
        else:
            self.custom_container_entry.grid_forget()

    def on_audio_format_change(self, choice):
        """Handle custom audio format"""
        if choice == self.lang.get("custom_format"):
            self.custom_audio_entry.grid(row=3, column=1, columnspan=2, padx=10, pady=5, sticky="w")
        else:
            self.custom_audio_entry.grid_forget()

    def update_quality_display(self):
        """Update quality dropdown with translated values"""
        self.quality_values = [
            self.lang.get("quality_best"),
            self.lang.get("quality_8k"),
            self.lang.get("quality_4k"),
            self.lang.get("quality_2k"),
            self.lang.get("quality_1080p"),
            self.lang.get("quality_720p"),
            self.lang.get("quality_640p"),
            self.lang.get("quality_480p"),
            self.lang.get("quality_360p"),
            self.lang.get("quality_240p"),
            self.lang.get("quality_144p")
        ]

    def update_audio_quality_display(self):
        """Update audio quality dropdown with translated values"""
        self.audio_quality_values = [
            self.lang.get("bitrate_best"),
            self.lang.get("bitrate_320"),
            self.lang.get("bitrate_256"),
            self.lang.get("bitrate_192"),
            self.lang.get("bitrate_128"),
            self.lang.get("bitrate_96"),
            self.lang.get("bitrate_64")
        ]
        self.video_audio_values = self.audio_quality_values.copy()

    def toggle_options(self):
        """Toggle between video, audio, subtitle and thumbnail options based on checkboxes"""
        # Show video options if video is checked
        if self.download_video_var.get():
            self.video_options_frame.pack(pady=10, padx=20, fill="x", after=self.video_options_frame.master.children[list(self.video_options_frame.master.children.keys())[3]])
        else:
            self.video_options_frame.pack_forget()

        # Show audio options if audio is checked
        if self.download_audio_var.get():
            self.audio_options_frame.pack(pady=10, padx=20, fill="x", after=self.audio_options_frame.master.children[list(self.audio_options_frame.master.children.keys())[3]])
        else:
            self.audio_options_frame.pack_forget()

        # Show subtitle options if subtitle is checked
        if self.download_subtitle_var.get():
            self.subtitle_options_frame.pack(pady=10, padx=20, fill="x", after=self.subtitle_options_frame.master.children[list(self.subtitle_options_frame.master.children.keys())[3]])
        else:
            self.subtitle_options_frame.pack_forget()

    def download_and_cache_thumbnail(self, thumbnail_url, url_hash):
        """Download thumbnail and cache it as temporary file"""
        if not thumbnail_url:
            return None

        # Check if already cached
        if thumbnail_url in self.thumbnail_cache:
            cached_path, cached_image = self.thumbnail_cache[thumbnail_url]
            if os.path.exists(cached_path):
                return cached_path, cached_image

        try:
            # Download thumbnail to temp file
            file_ext = os.path.splitext(thumbnail_url.split('?')[0])[1] or '.jpg'
            temp_path = self.thumbnail_cache_dir / f"thumb_{url_hash}{file_ext}"

            urlretrieve(thumbnail_url, str(temp_path))

            # Create CTkImage if PIL is available
            ctk_image = None
            if HAS_PIL:
                try:
                    img = Image.open(temp_path)
                    img.thumbnail((120, 68), Image.Resampling.LANCZOS)
                    ctk_image = ctk.CTkImage(light_image=img, dark_image=img, size=(120, 68))
                except Exception as e:
                    self.log_message(f"Failed to create thumbnail image: {str(e)}")

            # Cache the result
            self.thumbnail_cache[thumbnail_url] = (str(temp_path), ctk_image)
            return str(temp_path), ctk_image

        except Exception as e:
            self.log_message(f"Failed to download thumbnail: {str(e)}")
            return None

    def analyze_video(self):
        """Analyze video URL to get available formats"""
        # Get all valid URLs from textbox
        current_text = self.url_entry.get("1.0", "end").strip()
        urls = []
        for line in current_text.split('\n'):
            line = line.strip()
            if line and line.startswith("http") and "youtube.com/watch?v=..." not in line:
                urls.append(line)

        if not urls:
            return

        # Check if yt-dlp is installed
        if not self.check_ytdlp():
            messagebox.showerror(
                self.lang.get("error_title"),
                self.lang.get("error_ytdlp_not_found")
            )
            return

        self.auto_analyzing = True
        # Clear previous analysis results
        self.analysis_status.configure(state="normal")
        self.analysis_status.delete("1.0", "end")
        self.analysis_status.insert("1.0", self.lang.get("analyzing") + "\n")
        self.analysis_status.configure(state="disabled")

        # Start analysis in separate thread for all URLs
        thread = threading.Thread(target=self._analyze_video_thread, args=(urls,))
        thread.daemon = True
        thread.start()

    def _analyze_video_thread(self, urls):
        """Thread function to analyze video formats for multiple URLs"""
        # Convert single URL to list for backward compatibility
        if isinstance(urls, str):
            urls = [urls]

        try:
            for idx, url in enumerate(urls, 1):
                self.log_message(f"Analyzing {idx}/{len(urls)}: {url}")

                # Get video information with JSON output
                cmd = ["yt-dlp", "-J", "--no-playlist", url]

                # Add cookie options if enabled
                if self.use_cookies_var.get():
                    browser = self.browser_var.get()
                    profile = self.profile_var.get()
                    if browser and browser != self.lang.get("no_browsers_found"):
                        browser_profile = f"{browser}:{profile}" if profile and profile != "Default" else browser
                        cmd.extend(["--cookies-from-browser", browser_profile])

                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=30
                )

                if result.returncode != 0:
                    error_msg = f"✗ Video {idx}: {self.lang.get('analysis_failed')}\n"
                    self.analysis_status.configure(state="normal")
                    self.analysis_status.insert("end", error_msg)
                    self.analysis_status.configure(state="disabled")
                    self.log_message(f"Analysis error: {result.stderr}")
                    continue

                # Parse JSON output
                data = json.loads(result.stdout)
                formats = data.get("formats", [])

                # Find max video height and audio bitrate
                max_height = 0
                max_audio_br = 0

                for fmt in formats:
                    # Check video height
                    if fmt.get("height"):
                        max_height = max(max_height, fmt["height"])

                    # Check audio bitrate
                    if fmt.get("abr"):
                        max_audio_br = max(max_audio_br, fmt["abr"])
                    elif fmt.get("tbr") and not fmt.get("height"):  # Audio-only format
                        max_audio_br = max(max_audio_br, fmt["tbr"])

                # Store max values from last analyzed video for quality options
                self.max_height = max_height
                self.max_audio_bitrate = int(max_audio_br)

                # Update UI
                self.update_quality_options()

                video_title = data.get("title", "Unknown")

                # Download and cache thumbnail
                thumbnail_url = data.get("thumbnail", "")
                if thumbnail_url:
                    url_hash = abs(hash(url)) % (10 ** 8)
                    self.download_and_cache_thumbnail(thumbnail_url, url_hash)

                # Add result to analysis status textbox
                result_msg = f"✓ Video {idx}: {video_title[:40]}... | {max_height}p, {int(max_audio_br)} kbps\n"
                self.analysis_status.configure(state="normal", text_color=("green", "green"))
                self.analysis_status.insert("end", result_msg)
                self.analysis_status.configure(state="disabled")
                self.log_message(f"Analysis complete - Max video: {max_height}p, Max audio: {int(max_audio_br)} kbps")

        except subprocess.TimeoutExpired:
            error_msg = f"✗ {self.lang.get('analysis_timeout')}\n"
            self.analysis_status.configure(state="normal")
            self.analysis_status.insert("end", error_msg)
            self.analysis_status.configure(state="disabled")
            self.log_message("Analysis timeout - URL may be invalid or network is slow")
        except json.JSONDecodeError:
            error_msg = f"✗ {self.lang.get('analysis_failed')}\n"
            self.analysis_status.configure(state="normal")
            self.analysis_status.insert("end", error_msg)
            self.analysis_status.configure(state="disabled")
            self.log_message("Failed to parse video information")
        except Exception as e:
            error_msg = f"✗ {self.lang.get('analysis_error')}: {str(e)}\n"
            self.analysis_status.configure(state="normal")
            self.analysis_status.insert("end", error_msg)
            self.analysis_status.configure(state="disabled")
            self.log_message(f"Analysis error: {str(e)}")
        finally:
            self.auto_analyzing = False

    def update_quality_options(self):
        """Update quality options based on analysis results - remove or disable unavailable"""
        if self.max_height is None:
            return

        # Quality mapping
        quality_map = [
            (self.lang.get("quality_best"), 999999, "best"),
            (self.lang.get("quality_8k"), 4320, "8K"),
            (self.lang.get("quality_4k"), 2160, "4K"),
            (self.lang.get("quality_2k"), 1440, "2K"),
            (self.lang.get("quality_1080p"), 1080, "1080p"),
            (self.lang.get("quality_720p"), 720, "720p"),
            (self.lang.get("quality_640p"), 640, "640p"),
            (self.lang.get("quality_480p"), 480, "480p"),
            (self.lang.get("quality_360p"), 360, "360p"),
            (self.lang.get("quality_240p"), 240, "240p"),
            (self.lang.get("quality_144p"), 144, "144p")
        ]

        # Only include available qualities
        updated_options = []
        for label, height, key in quality_map:
            if key == "best" or height <= self.max_height:
                updated_options.append(label)

        self.quality_menu.configure(values=updated_options)

        # Audio quality mapping
        audio_map = [
            (self.lang.get("bitrate_best"), 999999, "best"),
            (self.lang.get("bitrate_320"), 320, "320"),
            (self.lang.get("bitrate_256"), 256, "256"),
            (self.lang.get("bitrate_192"), 192, "192"),
            (self.lang.get("bitrate_128"), 128, "128"),
            (self.lang.get("bitrate_96"), 96, "96"),
            (self.lang.get("bitrate_64"), 64, "64")
        ]

        # Only include available audio qualities
        updated_audio = []
        for label, bitrate, key in audio_map:
            if key == "best" or bitrate <= self.max_audio_bitrate:
                updated_audio.append(label)

        self.audio_quality_menu.configure(values=updated_audio)
        self.video_audio_menu.configure(values=updated_audio)

    def browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.download_path = folder
            self.path_entry.delete(0, "end")
            self.path_entry.insert(0, folder)

    def add_new_language(self):
        """Add a new language"""
        # Create dialog window
        dialog = ctk.CTkToplevel(self.window)
        dialog.title("Add New Language")
        dialog.geometry("400x250")
        dialog.grab_set()  # Make modal

        # Language name input
        ctk.CTkLabel(dialog, text="Language Name (display):", font=ctk.CTkFont(size=12)).pack(pady=(20, 5), padx=20, anchor="w")
        lang_name_entry = ctk.CTkEntry(dialog, placeholder_text="e.g., Español")
        lang_name_entry.pack(pady=5, padx=20, fill="x")

        # Language code input
        ctk.CTkLabel(dialog, text="Language Code (2 letters):", font=ctk.CTkFont(size=12)).pack(pady=(10, 5), padx=20, anchor="w")
        lang_code_entry = ctk.CTkEntry(dialog, placeholder_text="e.g., es")
        lang_code_entry.pack(pady=5, padx=20, fill="x")

        # Base language to copy from
        ctk.CTkLabel(dialog, text="Copy from:", font=ctk.CTkFont(size=12)).pack(pady=(10, 5), padx=20, anchor="w")
        base_lang_var = ctk.StringVar(value="English")
        base_lang_menu = ctk.CTkComboBox(dialog, values=["English", "한국어"], variable=base_lang_var)
        base_lang_menu.pack(pady=5, padx=20, fill="x")

        def create_language():
            """Create new language file"""
            lang_name = lang_name_entry.get().strip()
            lang_code = lang_code_entry.get().strip().lower()

            if not lang_name or not lang_code:
                messagebox.showerror("Error", "Please enter both language name and code")
                return

            if len(lang_code) != 2:
                messagebox.showerror("Error", "Language code must be 2 letters (e.g., es, fr, de)")
                return

            # Check if language file already exists
            new_lang_file = Path(__file__).parent / f"lang_{lang_code}.json"
            if new_lang_file.exists():
                messagebox.showerror("Error", f"Language file lang_{lang_code}.json already exists")
                return

            # Copy from base language
            base_code = "en" if base_lang_var.get() == "English" else "ko"
            base_file = Path(__file__).parent / f"lang_{base_code}.json"

            try:
                with open(base_file, 'r', encoding='utf-8') as f:
                    translations = json.load(f)

                # Save new language file
                with open(new_lang_file, 'w', encoding='utf-8') as f:
                    json.dump(translations, f, ensure_ascii=False, indent=2)

                # Update language menu
                current_langs = list(self.lang_var._variable._tk.call("set", self.lang_var._variable._name))
                if lang_name not in current_langs:
                    # Find the ComboBox widget and update its values
                    # We need to refresh the window
                    messagebox.showinfo("Success", f"Language '{lang_name}' created successfully!\n\nFile: lang_{lang_code}.json\n\nPlease restart the application to see the new language in the menu.")

                dialog.destroy()

            except Exception as e:
                messagebox.showerror("Error", f"Failed to create language: {str(e)}")

        # Buttons
        button_frame = ctk.CTkFrame(dialog)
        button_frame.pack(pady=20, padx=20, fill="x")

        create_button = ctk.CTkButton(button_frame, text="Create", command=create_language)
        create_button.pack(side="left", padx=5)

        cancel_button = ctk.CTkButton(button_frame, text="Cancel", command=dialog.destroy)
        cancel_button.pack(side="left", padx=5)

    def open_translation_editor(self):
        """Open translation editor window"""
        editor_window = ctk.CTkToplevel(self.window)
        editor_window.title(self.lang.get("translation_editor"))
        editor_window.geometry("700x500")

        # Get current language file
        lang_file = Path(__file__).parent / f"lang_{self.lang.lang_code}.json"

        # Load current translations
        with open(lang_file, 'r', encoding='utf-8') as f:
            translations = json.load(f)

        # Create scrollable frame
        scroll_frame = ctk.CTkScrollableFrame(editor_window)
        scroll_frame.pack(pady=10, padx=10, fill="both", expand=True)

        # Create entry fields for each translation
        entries = {}
        row = 0
        for key, value in sorted(translations.items()):
            # Key label
            key_label = ctk.CTkLabel(scroll_frame, text=key, font=ctk.CTkFont(size=11, weight="bold"))
            key_label.grid(row=row, column=0, padx=5, pady=5, sticky="w")

            # Value entry
            entry = ctk.CTkEntry(scroll_frame, width=400)
            entry.insert(0, value)
            entry.grid(row=row, column=1, padx=5, pady=5, sticky="ew")
            entries[key] = entry

            row += 1

        scroll_frame.grid_columnconfigure(1, weight=1)

        # Button frame
        button_frame = ctk.CTkFrame(editor_window)
        button_frame.pack(pady=10, padx=10, fill="x")

        def save_translations():
            """Save edited translations"""
            new_translations = {}
            for key, entry in entries.items():
                new_translations[key] = entry.get()

            # Save to file
            with open(lang_file, 'w', encoding='utf-8') as f:
                json.dump(new_translations, f, ensure_ascii=False, indent=2)

            # Reload translations
            self.lang.load_language(self.lang.lang_code)

            messagebox.showinfo(self.lang.get("success_title"), "Translations saved successfully!")
            editor_window.destroy()

        save_button = ctk.CTkButton(
            button_frame,
            text=self.lang.get("save"),
            command=save_translations
        )
        save_button.pack(side="left", padx=5)

        cancel_button = ctk.CTkButton(
            button_frame,
            text=self.lang.get("cancel"),
            command=editor_window.destroy
        )
        cancel_button.pack(side="left", padx=5)

    def log_message(self, message):
        self.log_text.insert("end", message + "\n")
        self.log_text.see("end")
        self.window.update_idletasks()

    def check_ytdlp(self):
        """Check if yt-dlp is available"""
        try:
            result = subprocess.run(
                ["yt-dlp", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def start_download(self):
        # Get URLs from textbox
        urls_text = self.url_entry.get("1.0", "end").strip()

        if not urls_text:
            messagebox.showerror(self.lang.get("error_title"), self.lang.get("error_no_url"))
            return

        # Split by newlines and filter out empty lines and placeholder
        urls = [line.strip() for line in urls_text.split('\n')
                if line.strip() and line.strip().startswith("http")
                and "youtube.com/watch?v=..." not in line]

        if not urls:
            messagebox.showerror(self.lang.get("error_title"), self.lang.get("error_no_url"))
            return

        # Check if yt-dlp is installed
        if not self.check_ytdlp():
            messagebox.showerror(
                self.lang.get("error_title"),
                self.lang.get("error_ytdlp_not_found")
            )
            return

        # If multiple URLs, open batch configuration window
        if len(urls) > 1:
            self.open_batch_config_window(urls)
        else:
            # Single URL - use current settings
            self.download_button.configure(state="disabled")
            thread = threading.Thread(target=self.download_single_with_types, args=(urls[0],))
            thread.daemon = True
            thread.start()

    def open_video_settings_dialog(self, video_info):
        """Open dialog to configure individual video settings"""
        dialog = ctk.CTkToplevel(self.window)
        dialog.title(f"Settings: {video_info['title'][:30]}...")
        dialog.geometry("400x650")
        dialog.grab_set()

        # Create scrollable frame
        scroll_frame = ctk.CTkScrollableFrame(dialog)
        scroll_frame.pack(pady=10, padx=10, fill="both", expand=True)

        # Get max available quality and bitrate from analysis
        max_height = video_info.get("max_height", 0)
        max_audio_bitrate = video_info.get("max_audio_bitrate", 0)

        # Check which download types are enabled
        show_video = video_info.get("download_video").get()
        show_audio = video_info.get("download_audio").get()
        show_subtitle = video_info.get("download_subtitle").get()

        # Variables to store settings
        quality_var = None
        codec_var = None
        container_var = None
        audio_format_var = None
        audio_quality_var = None
        subtitle_format_var = None
        subtitle_language_var = None

        # Show video options only if video download is checked
        if show_video:
            # Filter quality options based on available max height
            quality_map = [
                (self.lang.get("quality_best"), 999999),
                (self.lang.get("quality_8k"), 4320),
                (self.lang.get("quality_4k"), 2160),
                (self.lang.get("quality_2k"), 1440),
                (self.lang.get("quality_1080p"), 1080),
                (self.lang.get("quality_720p"), 720),
                (self.lang.get("quality_640p"), 640),
                (self.lang.get("quality_480p"), 480),
                (self.lang.get("quality_360p"), 360),
                (self.lang.get("quality_240p"), 240),
                (self.lang.get("quality_144p"), 144)
            ]

            available_qualities = []
            for label, height in quality_map:
                if max_height > 0:
                    if label == self.lang.get("quality_best") or height <= max_height:
                        available_qualities.append(label)
                else:
                    available_qualities.append(label)

            ctk.CTkLabel(scroll_frame, text="Video Quality:", font=ctk.CTkFont(size=12, weight="bold")).pack(pady=(10, 5), padx=20, anchor="w")
            quality_var = ctk.StringVar(value=video_info["video_quality"])
            quality_menu = ctk.CTkComboBox(scroll_frame, values=available_qualities, variable=quality_var)
            quality_menu.pack(pady=5, padx=20, fill="x")

            ctk.CTkLabel(scroll_frame, text="Video Codec:", font=ctk.CTkFont(size=12, weight="bold")).pack(pady=(10, 5), padx=20, anchor="w")
            codec_var = ctk.StringVar(value=video_info["video_codec"])
            codec_menu = ctk.CTkComboBox(scroll_frame, values=[self.lang.get("codec_any"), self.lang.get("codec_av1"), self.lang.get("codec_vp9"), self.lang.get("codec_vp8"), self.lang.get("codec_avc")], variable=codec_var)
            codec_menu.pack(pady=5, padx=20, fill="x")

            ctk.CTkLabel(scroll_frame, text="Container:", font=ctk.CTkFont(size=12, weight="bold")).pack(pady=(10, 5), padx=20, anchor="w")
            container_var = ctk.StringVar(value=video_info["video_container"])
            container_menu = ctk.CTkComboBox(scroll_frame, values=["mp4", "mkv", "webm", "avi", self.lang.get("custom_format")], variable=container_var)
            container_menu.pack(pady=5, padx=20, fill="x")

        # Show audio options if video or audio download is checked
        if show_video or show_audio:
            # Filter audio quality options
            audio_map = [
                (self.lang.get("bitrate_best"), 999999),
                (self.lang.get("bitrate_320"), 320),
                (self.lang.get("bitrate_256"), 256),
                (self.lang.get("bitrate_192"), 192),
                (self.lang.get("bitrate_128"), 128),
                (self.lang.get("bitrate_96"), 96),
                (self.lang.get("bitrate_64"), 64)
            ]

            available_audio_qualities = []
            for label, bitrate in audio_map:
                if max_audio_bitrate > 0:
                    if label == self.lang.get("bitrate_best") or bitrate <= max_audio_bitrate:
                        available_audio_qualities.append(label)
                else:
                    available_audio_qualities.append(label)

            if show_audio:
                ctk.CTkLabel(scroll_frame, text="Audio Format:", font=ctk.CTkFont(size=12, weight="bold")).pack(pady=(10, 5), padx=20, anchor="w")
                audio_format_var = ctk.StringVar(value=video_info["audio_format"])
                audio_format_menu = ctk.CTkComboBox(scroll_frame, values=["mp3", "aac", "opus", "m4a", "wav", "flac", self.lang.get("custom_format")], variable=audio_format_var)
                audio_format_menu.pack(pady=5, padx=20, fill="x")

            ctk.CTkLabel(scroll_frame, text="Audio Quality:", font=ctk.CTkFont(size=12, weight="bold")).pack(pady=(10, 5), padx=20, anchor="w")
            audio_quality_var = ctk.StringVar(value=video_info["audio_quality"])
            audio_quality_menu = ctk.CTkComboBox(scroll_frame, values=available_audio_qualities, variable=audio_quality_var)
            audio_quality_menu.pack(pady=5, padx=20, fill="x")

        # Show subtitle options only if subtitle download is checked
        if show_subtitle:
            ctk.CTkLabel(scroll_frame, text=self.lang.get("subtitle_format") if "subtitle_format" in self.lang.translations else "Subtitle Format:", font=ctk.CTkFont(size=12, weight="bold")).pack(pady=(10, 5), padx=20, anchor="w")
            subtitle_format_var = ctk.StringVar(value=video_info.get("subtitle_format", "srt"))
            subtitle_format_menu = ctk.CTkComboBox(scroll_frame, values=["srt", "vtt", "ass", "sbv"], variable=subtitle_format_var)
            subtitle_format_menu.pack(pady=5, padx=20, fill="x")

            ctk.CTkLabel(scroll_frame, text="Subtitle Language:", font=ctk.CTkFont(size=12, weight="bold")).pack(pady=(10, 5), padx=20, anchor="w")
            subtitle_language_var = ctk.StringVar(value=video_info.get("subtitle_language", "en"))
            # Use dropdown if available subtitle languages are provided
            available_langs = video_info.get("available_subtitle_langs", ["en"])
            subtitle_language_menu = ctk.CTkComboBox(scroll_frame, values=available_langs, variable=subtitle_language_var)
            subtitle_language_menu.pack(pady=5, padx=20, fill="x")

        # Save button
        def save_settings():
            if quality_var:
                video_info["video_quality"] = quality_var.get()
            if codec_var:
                video_info["video_codec"] = codec_var.get()
            if container_var:
                video_info["video_container"] = container_var.get()
            if audio_format_var:
                video_info["audio_format"] = audio_format_var.get()
            if audio_quality_var:
                video_info["audio_quality"] = audio_quality_var.get()
            if subtitle_format_var:
                video_info["subtitle_format"] = subtitle_format_var.get()
            if subtitle_language_var:
                video_info["subtitle_language"] = subtitle_language_var.get()
            dialog.destroy()

        button_frame = ctk.CTkFrame(dialog)
        button_frame.pack(pady=10, padx=20, fill="x", side="bottom")

        save_btn = ctk.CTkButton(button_frame, text="Save", command=save_settings)
        save_btn.pack(side="left", padx=5)

        cancel_btn = ctk.CTkButton(button_frame, text="Cancel", command=dialog.destroy)
        cancel_btn.pack(side="left", padx=5)

    def open_batch_config_window(self, urls):
        """Open window to configure download options for each URL"""
        config_window = ctk.CTkToplevel(self.window)
        config_window.title(self.lang.get("batch_config_title") if hasattr(self.lang, 'translations') and "batch_config_title" in self.lang.translations else "Batch Download Configuration")
        config_window.geometry("1000x600")

        # Disable download button while config window is open
        self.download_button.configure(state="disabled")

        # Re-enable download button when config window is closed
        def on_config_window_close():
            self.download_button.configure(state="normal")
            config_window.destroy()

        config_window.protocol("WM_DELETE_WINDOW", on_config_window_close)

        # Show loading message
        loading_label = ctk.CTkLabel(config_window, text="Analyzing videos...\nPlease wait...", font=ctk.CTkFont(size=16))
        loading_label.pack(expand=True)

        # Analyze URLs in separate thread to prevent UI freeze
        video_info_list = []

        def analyze_videos_thread():
            """Analyze all videos in background thread"""
            self.log_message(f"Analyzing {len(urls)} videos...")

            for idx, url in enumerate(urls, 1):
                self.log_message(f"Analyzing video {idx}/{len(urls)}...")
                try:
                    cmd = ["yt-dlp", "-J", "--no-playlist", url]
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

                    if result.returncode == 0:
                        data = json.loads(result.stdout)
                        title = data.get("title", "Unknown")
                        duration = data.get("duration", 0)
                        duration_str = f"{int(duration//60)}:{int(duration%60):02d}" if duration else "Unknown"
                        thumbnail_url = data.get("thumbnail", "")

                        # Analyze available formats
                        formats = data.get("formats", [])
                        max_height = 0
                        max_audio_br = 0

                        for fmt in formats:
                            if fmt.get("height"):
                                max_height = max(max_height, fmt["height"])
                            if fmt.get("abr"):
                                max_audio_br = max(max_audio_br, fmt["abr"])
                            elif fmt.get("tbr") and not fmt.get("height"):
                                max_audio_br = max(max_audio_br, fmt["tbr"])

                        # Get available subtitles
                        subtitles = data.get("subtitles", {})
                        automatic_captions = data.get("automatic_captions", {})
                        available_subtitle_langs = list(set(list(subtitles.keys()) + list(automatic_captions.keys())))
                        if not available_subtitle_langs:
                            available_subtitle_langs = ["en"]  # Default to English if no subtitles found

                        # Download and cache thumbnail
                        if thumbnail_url:
                            url_hash = abs(hash(url)) % (10 ** 8)
                            self.download_and_cache_thumbnail(thumbnail_url, url_hash)

                        self.log_message(f"✓ {title[:50]} - {duration_str} | {max_height}p, {int(max_audio_br)} kbps")

                        video_info_list.append({
                            "url": url,
                            "title": title,
                            "duration": duration_str,
                            "thumbnail_url": thumbnail_url,
                            "max_height": max_height,
                            "max_audio_bitrate": int(max_audio_br),
                            "available_subtitle_langs": available_subtitle_langs,
                            "download_video": ctk.BooleanVar(value=self.download_video_var.get()),
                            "download_audio": ctk.BooleanVar(value=self.download_audio_var.get()),
                            "download_thumbnail": ctk.BooleanVar(value=self.download_thumbnail_var.get()),
                            "download_subtitle": ctk.BooleanVar(value=False),
                            "subtitle_format": "srt",
                            "subtitle_language": available_subtitle_langs[0] if available_subtitle_langs else "en",
                            "video_quality": self.video_quality_var.get(),
                            "video_codec": self.video_codec_var.get(),
                            "video_container": self.video_container_var.get(),
                            "audio_format": self.audio_format_var.get(),
                            "audio_quality": self.audio_quality_var.get()
                        })
                    else:
                        self.log_message(f"✗ Error analyzing URL")
                        video_info_list.append({
                            "url": url,
                            "title": "Error analyzing",
                            "duration": "Unknown",
                            "thumbnail_url": "",
                            "max_height": 0,
                            "max_audio_bitrate": 0,
                            "available_subtitle_langs": ["en"],
                            "download_video": ctk.BooleanVar(value=True),
                            "download_audio": ctk.BooleanVar(value=False),
                            "download_thumbnail": ctk.BooleanVar(value=False),
                            "download_subtitle": ctk.BooleanVar(value=False),
                            "subtitle_format": "srt",
                            "subtitle_language": "en",
                            "video_quality": self.video_quality_var.get(),
                            "video_codec": self.video_codec_var.get(),
                            "video_container": self.video_container_var.get(),
                            "audio_format": self.audio_format_var.get(),
                            "audio_quality": self.audio_quality_var.get()
                        })
                except Exception as e:
                    self.log_message(f"✗ Error: {str(e)}")
                    video_info_list.append({
                        "url": url,
                        "title": f"Error: {str(e)}",
                        "duration": "Unknown",
                        "thumbnail_url": "",
                        "max_height": 0,
                        "max_audio_bitrate": 0,
                        "available_subtitle_langs": ["en"],
                        "download_video": ctk.BooleanVar(value=True),
                        "download_audio": ctk.BooleanVar(value=False),
                        "download_thumbnail": ctk.BooleanVar(value=False),
                        "download_subtitle": ctk.BooleanVar(value=False),
                        "subtitle_format": "srt",
                        "subtitle_language": "en",
                        "video_quality": self.video_quality_var.get(),
                        "video_codec": self.video_codec_var.get(),
                        "video_container": self.video_container_var.get(),
                        "audio_format": self.audio_format_var.get(),
                        "audio_quality": self.audio_quality_var.get()
                    })

            # Build UI after analysis completes (on main thread)
            self.window.after(0, lambda: build_config_ui(config_window, loading_label, video_info_list, on_config_window_close))

        def build_config_ui(config_window, loading_label, video_info_list, on_config_window_close):
            """Build the configuration UI after analysis"""
            # Remove loading label
            loading_label.pack_forget()

            # Create scrollable frame for video list
            scroll_frame = ctk.CTkScrollableFrame(config_window)
            scroll_frame.pack(pady=10, padx=10, fill="both", expand=True)

            # Header
            header_frame = ctk.CTkFrame(scroll_frame)
            header_frame.pack(fill="x", padx=5, pady=5)

            ctk.CTkLabel(header_frame, text=self.lang.get("batch_preview") if "batch_preview" in self.lang.translations else "미리보기", font=ctk.CTkFont(weight="bold"), width=120).grid(row=0, column=0, padx=5)
            ctk.CTkLabel(header_frame, text=self.lang.get("batch_title") if "batch_title" in self.lang.translations else "제목", font=ctk.CTkFont(weight="bold"), width=180).grid(row=0, column=1, padx=5)
            ctk.CTkLabel(header_frame, text=self.lang.get("batch_duration") if "batch_duration" in self.lang.translations else "길이", font=ctk.CTkFont(weight="bold"), width=60).grid(row=0, column=2, padx=5)
            ctk.CTkLabel(header_frame, text=self.lang.get("video") if "video" in self.lang.translations else "비디오", font=ctk.CTkFont(weight="bold"), width=50).grid(row=0, column=3, padx=5)
            ctk.CTkLabel(header_frame, text=self.lang.get("audio_only") if "audio_only" in self.lang.translations else "오디오", font=ctk.CTkFont(weight="bold"), width=50).grid(row=0, column=4, padx=5)
            ctk.CTkLabel(header_frame, text=self.lang.get("thumbnail_only") if "thumbnail_only" in self.lang.translations else "썸네일", font=ctk.CTkFont(weight="bold"), width=50).grid(row=0, column=5, padx=5)
            ctk.CTkLabel(header_frame, text=self.lang.get("batch_subtitle") if "batch_subtitle" in self.lang.translations else "자막", font=ctk.CTkFont(weight="bold"), width=50).grid(row=0, column=6, padx=5)
            ctk.CTkLabel(header_frame, text=self.lang.get("batch_settings") if "batch_settings" in self.lang.translations else "설정", font=ctk.CTkFont(weight="bold"), width=60).grid(row=0, column=7, padx=5)

            # Helper function to load thumbnail image
            def load_thumbnail(thumbnail_url):
                """Load thumbnail image and return CTkImage from cache"""
                if not thumbnail_url:
                    return None

                # Check cache first
                if thumbnail_url in self.thumbnail_cache:
                    cached_path, cached_image = self.thumbnail_cache[thumbnail_url]
                    if cached_image:
                        return cached_image

                # If not cached or no image, return None (should have been downloaded during analysis)
                return None

            # Video rows
            for info in video_info_list:
                row_frame = ctk.CTkFrame(scroll_frame)
                row_frame.pack(fill="x", padx=5, pady=2)

                # Load and display thumbnail image directly
                thumbnail_image = load_thumbnail(info["thumbnail_url"])
                if thumbnail_image:
                    thumbnail_label = ctk.CTkLabel(row_frame, image=thumbnail_image, text="")
                    thumbnail_label.image = thumbnail_image  # Keep reference
                    thumbnail_label.grid(row=0, column=0, padx=5)
                else:
                    # Placeholder if thumbnail not available
                    placeholder_label = ctk.CTkLabel(row_frame, text="No\nPreview", width=120, height=68, fg_color="gray30")
                    placeholder_label.grid(row=0, column=0, padx=5)

                title_label = ctk.CTkLabel(row_frame, text=info["title"][:35] + "..." if len(info["title"]) > 35 else info["title"], width=180, anchor="w")
                title_label.grid(row=0, column=1, padx=5, sticky="w")

                duration_label = ctk.CTkLabel(row_frame, text=info["duration"], width=60)
                duration_label.grid(row=0, column=2, padx=5)

                video_check = ctk.CTkCheckBox(row_frame, text="", variable=info["download_video"], width=50)
                video_check.grid(row=0, column=3, padx=5)

                audio_check = ctk.CTkCheckBox(row_frame, text="", variable=info["download_audio"], width=50)
                audio_check.grid(row=0, column=4, padx=5)

                thumb_check = ctk.CTkCheckBox(row_frame, text="", variable=info["download_thumbnail"], width=50)
                thumb_check.grid(row=0, column=5, padx=5)

                subtitle_check = ctk.CTkCheckBox(row_frame, text="", variable=info["download_subtitle"], width=50)
                subtitle_check.grid(row=0, column=6, padx=5)

                # Settings button for each video
                def open_video_settings(video_info=info):
                    self.open_video_settings_dialog(video_info)

                settings_btn = ctk.CTkButton(row_frame, text="⚙", width=60, command=open_video_settings)
                settings_btn.grid(row=0, column=7, padx=5)

            # Button frame
            button_frame = ctk.CTkFrame(config_window)
            button_frame.pack(pady=10, padx=10, fill="x")

            def start_batch_download():
                """Start downloading all configured videos"""
                config_window.destroy()
                self.download_button.configure(state="disabled")
                thread = threading.Thread(target=self.download_batch_with_config, args=(video_info_list,))
                thread.daemon = True
                thread.start()

            start_button = ctk.CTkButton(button_frame, text=self.lang.get("download"), command=start_batch_download)
            start_button.pack(side="left", padx=5)

            cancel_button = ctk.CTkButton(button_frame, text=self.lang.get("cancel"), command=on_config_window_close)
            cancel_button.pack(side="left", padx=5)

        # Start analysis thread
        thread = threading.Thread(target=analyze_videos_thread)
        thread.daemon = True
        thread.start()

    def download_batch_with_config(self, video_info_list):
        """Download multiple videos with individual configurations"""
        total = len(video_info_list)
        for i, info in enumerate(video_info_list, 1):
            self.log_message(f"\n{'='*50}")
            self.log_message(f"Downloading {i}/{total}: {info['title']}")
            self.log_message(f"{'='*50}\n")

            # Download each selected type with individual settings
            if info["download_video"].get():
                self.log_message("Downloading video...")
                self.download_video(
                    info["url"],
                    download_type="video",
                    video_quality=info["video_quality"],
                    video_codec=info["video_codec"],
                    video_container=info["video_container"],
                    audio_format=info["audio_format"],
                    audio_quality=info["audio_quality"]
                )

            if info["download_audio"].get():
                self.log_message("Downloading audio...")
                self.download_video(
                    info["url"],
                    download_type="audio",
                    audio_format=info["audio_format"],
                    audio_quality=info["audio_quality"]
                )

            if info["download_thumbnail"].get():
                self.log_message("Downloading thumbnail...")
                self.download_video(info["url"], download_type="thumbnail")

            if info["download_subtitle"].get():
                self.log_message(f"Downloading subtitle ({info['subtitle_format']}, {info['subtitle_language']})...")
                self.download_video(
                    info["url"],
                    download_type="subtitle",
                    subtitle_format=info["subtitle_format"],
                    subtitle_language=info["subtitle_language"]
                )

        self.download_button.configure(state="normal")
        self.log_message("\n" + "="*50)
        self.log_message("All downloads completed!")
        self.log_message("="*50 + "\n")

        # Show completion notification
        messagebox.showinfo(
            self.lang.get("success_title") if "success_title" in self.lang.translations else "완료",
            f"모든 다운로드가 완료되었습니다!\n총 {total}개의 동영상"
        )

    def download_single_with_types(self, url):
        """Download single URL with selected types"""
        try:
            # Download each selected type
            if self.download_video_var.get():
                self.log_message("Downloading video...")
                self.download_video(url, download_type="video")

            if self.download_audio_var.get():
                self.log_message("Downloading audio...")
                self.download_video(url, download_type="audio")

            if self.download_thumbnail_var.get():
                self.log_message("Downloading thumbnail...")
                self.download_video(url, download_type="thumbnail")

            if self.download_subtitle_var.get():
                self.log_message(f"Downloading subtitle ({self.subtitle_format_var.get()}, {self.subtitle_language_var.get()})...")
                self.download_video(
                    url,
                    download_type="subtitle",
                    subtitle_format=self.subtitle_format_var.get(),
                    subtitle_language=self.subtitle_language_var.get()
                )

        finally:
            self.download_button.configure(state="normal")

            # Show completion notification
            messagebox.showinfo(
                self.lang.get("success_title") if "success_title" in self.lang.translations else "완료",
                "다운로드가 완료되었습니다!"
            )

    def download_multiple_videos(self, urls):
        """Download multiple videos sequentially"""
        total = len(urls)
        for i, url in enumerate(urls, 1):
            self.log_message(f"\n{'='*50}")
            self.log_message(f"Downloading {i}/{total}: {url}")
            self.log_message(f"{'='*50}\n")
            self.download_video(url)

        # Re-enable download button after all downloads
        self.download_button.configure(state="normal")

        # Show completion notification
        messagebox.showinfo(
            self.lang.get("success_title") if "success_title" in self.lang.translations else "완료",
            f"모든 다운로드가 완료되었습니다!\n총 {total}개의 동영상"
        )

    def get_height_from_quality(self, quality_text):
        """Extract height from quality text"""
        if self.lang.get("quality_best") in quality_text or "best" in quality_text:
            return None
        if "8K" in quality_text or "4320" in quality_text:
            return "4320"
        elif "4K" in quality_text or "2160" in quality_text:
            return "2160"
        elif "2K" in quality_text or "1440" in quality_text:
            return "1440"
        elif "1080" in quality_text:
            return "1080"
        elif "720" in quality_text:
            return "720"
        elif "640" in quality_text:
            return "640"
        elif "480" in quality_text:
            return "480"
        elif "360" in quality_text:
            return "360"
        elif "240" in quality_text:
            return "240"
        elif "144" in quality_text:
            return "144"
        return None

    def get_codec_filter(self, codec_text):
        """Get codec filter string"""
        if self.lang.get("codec_av1") in codec_text or "AV1" in codec_text:
            return "[vcodec^=av01]"
        elif self.lang.get("codec_vp9") in codec_text or "VP9" in codec_text:
            return "[vcodec^=vp9]"
        elif self.lang.get("codec_vp8") in codec_text or "VP8" in codec_text:
            return "[vcodec^=vp8]"
        elif self.lang.get("codec_avc") in codec_text or "AVC" in codec_text or "H.264" in codec_text:
            return "[vcodec^=avc]"
        return ""

    def get_bitrate_from_text(self, bitrate_text):
        """Extract bitrate number from text"""
        if self.lang.get("bitrate_best") in bitrate_text or "best" in bitrate_text:
            return None
        # Extract number
        match = re.search(r'(\d+)', bitrate_text)
        if match:
            return match.group(1)
        return None

    def build_format_string(self):
        """Build yt-dlp format string based on user selections"""
        # Video format
        video_selector = "bestvideo"

        # Get quality
        quality = self.video_quality_var.get()
        height = self.get_height_from_quality(quality)

        if height:
            video_selector += f"[height<={height}]"

        # Get codec
        codec = self.video_codec_var.get()
        codec_filter = self.get_codec_filter(codec)
        if codec_filter:
            video_selector += codec_filter

        # Get audio bitrate
        audio_quality = self.video_audio_quality_var.get()
        audio_br = self.get_bitrate_from_text(audio_quality)

        if audio_br:
            format_string = f"{video_selector}+bestaudio[abr<={audio_br}]/best"
        else:
            format_string = f"{video_selector}+bestaudio/best"

        return format_string

    def download_video(self, url, download_type=None, video_quality=None, video_codec=None,
                      video_container=None, audio_format=None, audio_quality=None, subtitle_format=None, subtitle_language=None):
        try:
            self.log_message(f"Starting download: {url}")
            self.progress_label.configure(text=self.lang.get("downloading"))
            self.progress_bar.set(0)

            # Build yt-dlp command
            output_template = os.path.join(self.download_path, "%(title)s.%(ext)s")

            cmd = ["yt-dlp", url, "-o", output_template]

            # Add cookie options if enabled
            if self.use_cookies_var.get():
                browser = self.browser_var.get()
                profile = self.profile_var.get()
                if browser and browser != self.lang.get("no_browsers_found"):
                    browser_profile = f"{browser}:{profile}" if profile and profile != "Default" else browser
                    cmd.extend(["--cookies-from-browser", browser_profile])
                    self.log_message(f"Using cookies from: {browser_profile}")

            # Determine download type
            if download_type is None:
                # Use checkbox settings if no type specified
                if self.download_thumbnail_var.get():
                    download_type = "thumbnail"
                elif self.download_audio_var.get():
                    download_type = "audio"
                elif self.download_video_var.get():
                    download_type = "video"
                else:
                    download_type = "video"  # Default

            # Use provided settings or fall back to global settings
            _audio_format = audio_format if audio_format is not None else self.audio_format_var.get()
            _audio_quality = audio_quality if audio_quality is not None else self.audio_quality_var.get()
            _video_quality = video_quality if video_quality is not None else self.video_quality_var.get()
            _video_codec = video_codec if video_codec is not None else self.video_codec_var.get()
            _video_container = video_container if video_container is not None else self.video_container_var.get()
            _subtitle_format = subtitle_format if subtitle_format is not None else "srt"
            _subtitle_language = subtitle_language if subtitle_language is not None else "en"

            # Add format options
            if download_type == "subtitle":
                # Subtitle download
                cmd.extend(["--write-subs", "--write-auto-subs", "--skip-download"])
                cmd.extend(["--sub-format", _subtitle_format])
                cmd.extend(["--convert-subs", _subtitle_format])
                cmd.extend(["--sub-langs", _subtitle_language])
                self.log_message(f"Format: Subtitle ({_subtitle_format}, language: {_subtitle_language})")

            elif download_type == "thumbnail":
                # Thumbnail only download
                cmd.extend(["--write-thumbnail", "--skip-download"])
                self.log_message(f"Format: Thumbnail only")

            elif download_type == "audio":
                # Audio download
                if _audio_format == self.lang.get("custom_format"):
                    _audio_format = self.custom_audio_entry.get().strip() or "mp3"

                cmd.extend(["-x", "--audio-format", _audio_format])

                bitrate = self.get_bitrate_from_text(_audio_quality)
                if bitrate:
                    cmd.extend(["--audio-quality", bitrate + "K"])

                self.log_message(f"Format: Audio only")
                self.log_message(f"Audio Format: {_audio_format.upper()}")
                self.log_message(f"Audio Quality: {_audio_quality}")

            else:
                # Video download - build format string with individual settings
                video_selector = "bestvideo"

                # Get quality
                height = self.get_height_from_quality(_video_quality)
                if height:
                    video_selector += f"[height<={height}]"

                # Get codec
                codec_filter = self.get_codec_filter(_video_codec)
                if codec_filter:
                    video_selector += codec_filter

                # Get audio bitrate
                audio_br = self.get_bitrate_from_text(_audio_quality)
                if audio_br:
                    format_string = f"{video_selector}+bestaudio[abr<={audio_br}]/best"
                else:
                    format_string = f"{video_selector}+bestaudio/best"

                cmd.extend(["-f", format_string])

                # Set container format
                container = _video_container
                if container == self.lang.get("custom_format"):
                    container = self.custom_container_entry.get().strip() or "mp4"

                cmd.extend(["--merge-output-format", container])
                # Add remux to ensure format conversion if needed
                cmd.extend(["--remux-video", container])

                # Log settings
                self.log_message(f"Format: Video")
                self.log_message(f"Quality: {_video_quality}")
                self.log_message(f"Video Codec: {_video_codec}")
                self.log_message(f"Audio Bitrate: {_audio_quality}")
                self.log_message(f"Container: {container.upper()}")

            # Add embed options (for video and audio only, not for thumbnail-only mode)
            if download_type != "thumbnail":
                if self.embed_thumbnail_var.get():
                    cmd.extend(["--embed-thumbnail"])
                    self.log_message("Embedding thumbnail")

                if self.embed_metadata_var.get():
                    cmd.extend(["--embed-metadata"])
                    self.log_message("Embedding metadata")

            # Add progress and other options
            cmd.extend(["--newline", "--no-playlist"])

            self.log_message(f"Download location: {self.download_path}")
            self.log_message("Processing...")
            self.log_message(f"Command: {' '.join(cmd)}")

            # Execute command
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )

            # Read output
            for line in process.stdout:
                line = line.strip()
                if line:
                    # Parse progress
                    if "%" in line and "ETA" in line:
                        try:
                            percent_str = line.split("%")[0].split()[-1]
                            percent = float(percent_str) / 100
                            self.progress_bar.set(percent)
                        except:
                            pass
                    self.log_message(line)

            process.wait()

            if process.returncode == 0:
                self.progress_bar.set(1.0)
                self.progress_label.configure(text=self.lang.get("download_completed"))
                self.log_message("Download completed successfully!")
                return True
            else:
                self.progress_label.configure(text=self.lang.get("download_failed"))
                self.log_message("Download failed!")
                return False

        except Exception as e:
            self.log_message(f"Error: {str(e)}")
            self.progress_label.configure(text=self.lang.get("error_occurred"))
            return False

    def run(self):
        self.window.mainloop()


def main():
    app = YouTubeDownloaderGUI()
    app.run()


if __name__ == "__main__":
    main()
