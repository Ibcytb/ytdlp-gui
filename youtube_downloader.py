import customtkinter as ctk
from tkinter import filedialog, messagebox
import os
import sys
import threading
import subprocess
import json
import re
import platform
from pathlib import Path

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

        # Language selector
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

        # Analysis Status Label
        self.analysis_status = ctk.CTkLabel(
            url_frame,
            text="",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        self.analysis_status.pack(padx=10, pady=(0, 10))

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
        format_frame = ctk.CTkFrame(self.main_frame)
        format_frame.pack(pady=10, padx=20, fill="x")

        format_title = ctk.CTkLabel(format_frame, text=self.lang.get("download_type"), font=ctk.CTkFont(size=14, weight="bold"))
        format_title.pack(anchor="w", padx=10, pady=(10, 5))

        format_select_frame = ctk.CTkFrame(format_frame)
        format_select_frame.pack(padx=10, pady=(0, 10), fill="x")

        self.format_var = ctk.StringVar(value="video")
        format_radio1 = ctk.CTkRadioButton(
            format_select_frame,
            text=self.lang.get("video"),
            variable=self.format_var,
            value="video",
            command=self.toggle_options,
            font=ctk.CTkFont(size=13)
        )
        format_radio1.pack(side="left", padx=20, pady=10)

        format_radio2 = ctk.CTkRadioButton(
            format_select_frame,
            text=self.lang.get("audio_only"),
            variable=self.format_var,
            value="audio",
            command=self.toggle_options,
            font=ctk.CTkFont(size=13)
        )
        format_radio2.pack(side="left", padx=20, pady=10)

        format_radio3 = ctk.CTkRadioButton(
            format_select_frame,
            text=self.lang.get("thumbnail_only"),
            variable=self.format_var,
            value="thumbnail",
            command=self.toggle_options,
            font=ctk.CTkFont(size=13)
        )
        format_radio3.pack(side="left", padx=20, pady=10)

        # Embed Options Frame
        embed_frame = ctk.CTkFrame(format_frame)
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

        # Settings Frame
        settings_frame = ctk.CTkFrame(self.main_frame)
        settings_frame.pack(pady=10, padx=20, fill="x")

        settings_title = ctk.CTkLabel(settings_frame, text=self.lang.get("settings"), font=ctk.CTkFont(size=14, weight="bold"))
        settings_title.grid(row=0, column=0, columnspan=2, padx=10, pady=(10, 5), sticky="w")

        # Language selection
        lang_label = ctk.CTkLabel(settings_frame, text=self.lang.get("language"), font=ctk.CTkFont(size=12))
        lang_label.grid(row=1, column=0, padx=10, pady=5, sticky="w")

        self.language_var = ctk.StringVar(value="한국어")
        language_menu = ctk.CTkComboBox(
            settings_frame,
            values=["English", "한국어"],
            variable=self.language_var,
            command=self.change_language,
            width=150
        )
        language_menu.grid(row=1, column=1, padx=10, pady=5, sticky="w")

        # Manual translation editor button
        edit_translation_button = ctk.CTkButton(
            settings_frame,
            text=self.lang.get("edit_translations") if hasattr(self, 'lang') else "Edit Translations",
            command=self.open_translation_editor,
            width=150
        )
        edit_translation_button.grid(row=2, column=0, columnspan=2, padx=10, pady=(5, 10), sticky="w")

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
            widget._parent_canvas.yview_scroll(int(-5 * (event.delta / 120)), "units")
            return "break"

        # Bind for Windows and Linux
        widget.bind("<MouseWheel>", on_mousewheel)
        # Bind for Linux (alternative)
        widget.bind("<Button-4>", lambda e: widget._parent_canvas.yview_scroll(-5, "units"))
        widget.bind("<Button-5>", lambda e: widget._parent_canvas.yview_scroll(5, "units"))

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
        # Get first valid URL
        current_url = ""
        for line in current_text.split('\n'):
            line = line.strip()
            if line and line.startswith("http") and "youtube.com/watch?v=..." not in line:
                current_url = line
                break

        if current_url and current_url != self.last_url:
            self.last_url = current_url
            # Delay analysis slightly to allow full URL to be pasted
            self.window.after(500, lambda: self.auto_analyze_video(current_url))

    def on_url_paste(self, event=None):
        """Detect paste event"""
        # Wait for paste to complete
        self.window.after(100, self.on_url_change)

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
        """Toggle between video, audio, and thumbnail options"""
        if self.format_var.get() == "video":
            self.video_options_frame.pack(pady=10, padx=20, fill="x", after=self.video_options_frame.master.children[list(self.video_options_frame.master.children.keys())[3]])
            self.audio_options_frame.pack_forget()
        elif self.format_var.get() == "audio":
            self.video_options_frame.pack_forget()
            self.audio_options_frame.pack(pady=10, padx=20, fill="x", after=self.audio_options_frame.master.children[list(self.audio_options_frame.master.children.keys())[3]])
        else:  # thumbnail
            self.video_options_frame.pack_forget()
            self.audio_options_frame.pack_forget()

    def analyze_video(self):
        """Analyze video URL to get available formats"""
        # Get first valid URL from textbox
        current_text = self.url_entry.get("1.0", "end").strip()
        url = ""
        for line in current_text.split('\n'):
            line = line.strip()
            if line and line.startswith("http") and "youtube.com/watch?v=..." not in line:
                url = line
                break

        if not url:
            return

        # Check if yt-dlp is installed
        if not self.check_ytdlp():
            messagebox.showerror(
                self.lang.get("error_title"),
                self.lang.get("error_ytdlp_not_found")
            )
            return

        self.auto_analyzing = True
        self.analysis_status.configure(text=self.lang.get("analyzing"))

        # Start analysis in separate thread
        thread = threading.Thread(target=self._analyze_video_thread, args=(url,))
        thread.daemon = True
        thread.start()

    def _analyze_video_thread(self, url):
        """Thread function to analyze video formats"""
        try:
            self.log_message(f"Analyzing: {url}")

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
                self.analysis_status.configure(text=self.lang.get("analysis_failed"), text_color="red")
                self.log_message(f"Analysis error: {result.stderr}")
                return

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

            self.max_height = max_height
            self.max_audio_bitrate = int(max_audio_br)

            # Update UI
            self.update_quality_options()

            video_title = data.get("title", "Unknown")
            self.analysis_status.configure(
                text=self.lang.get("analysis_complete", height=max_height, audio=int(max_audio_br), title=video_title[:50]),
                text_color="green"
            )
            self.log_message(f"Analysis complete - Max video: {max_height}p, Max audio: {int(max_audio_br)} kbps")

        except subprocess.TimeoutExpired:
            self.analysis_status.configure(text=self.lang.get("analysis_timeout"), text_color="red")
            self.log_message("Analysis timeout - URL may be invalid or network is slow")
        except json.JSONDecodeError:
            self.analysis_status.configure(text=self.lang.get("analysis_failed"), text_color="red")
            self.log_message("Failed to parse video information")
        except Exception as e:
            self.analysis_status.configure(text=self.lang.get("analysis_error"), text_color="red")
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

        # Disable download button
        self.download_button.configure(state="disabled")

        # Start download in separate thread
        thread = threading.Thread(target=self.download_multiple_videos, args=(urls,))
        thread.daemon = True
        thread.start()

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
        if self.format_var.get() == "audio":
            return None  # Audio format is handled separately

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

    def download_video(self, url):
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

            # Add format options
            if self.format_var.get() == "thumbnail":
                # Thumbnail only download
                cmd.extend(["--write-thumbnail", "--skip-download"])
                self.log_message(f"Format: Thumbnail only")

            elif self.format_var.get() == "audio":
                # Audio download
                audio_format = self.audio_format_var.get()
                if audio_format == self.lang.get("custom_format"):
                    audio_format = self.custom_audio_entry.get().strip() or "mp3"

                audio_quality = self.audio_quality_var.get()

                cmd.extend(["-x", "--audio-format", audio_format])

                bitrate = self.get_bitrate_from_text(audio_quality)
                if bitrate:
                    cmd.extend(["--audio-quality", bitrate + "K"])

                self.log_message(f"Format: Audio only")
                self.log_message(f"Audio Format: {audio_format.upper()}")
                self.log_message(f"Audio Quality: {audio_quality}")

            else:
                # Video download
                format_string = self.build_format_string()
                cmd.extend(["-f", format_string])

                # Set container format
                container = self.video_container_var.get()
                if container == self.lang.get("custom_format"):
                    container = self.custom_container_entry.get().strip() or "mp4"

                cmd.extend(["--merge-output-format", container])
                # Add remux to ensure format conversion if needed
                cmd.extend(["--remux-video", container])

                # Log settings
                self.log_message(f"Format: Video")
                self.log_message(f"Quality: {self.video_quality_var.get()}")
                self.log_message(f"Video Codec: {self.video_codec_var.get()}")
                self.log_message(f"Audio Bitrate: {self.video_audio_quality_var.get()}")
                self.log_message(f"Container: {container.upper()}")

            # Add embed options (for video and audio only, not for thumbnail-only mode)
            if self.format_var.get() != "thumbnail":
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
                messagebox.showinfo(self.lang.get("success_title"), self.lang.get("success_message"))
            else:
                self.progress_label.configure(text=self.lang.get("download_failed"))
                self.log_message("Download failed!")
                messagebox.showerror(self.lang.get("error_title"), "Download failed. Check the log for details.")

        except Exception as e:
            self.log_message(f"Error: {str(e)}")
            self.progress_label.configure(text=self.lang.get("error_occurred"))
            messagebox.showerror(self.lang.get("error_title"), f"An error occurred:\n{str(e)}")

    def run(self):
        self.window.mainloop()


def main():
    app = YouTubeDownloaderGUI()
    app.run()


if __name__ == "__main__":
    main()
