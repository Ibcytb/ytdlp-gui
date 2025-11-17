import customtkinter as ctk
from tkinter import filedialog, messagebox
import os
import sys
import threading
import subprocess
import json
import re
from pathlib import Path

# Set appearance
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class YouTubeDownloaderGUI:
    def __init__(self):
        self.window = ctk.CTk()
        self.window.title("YouTube Downloader Pro (yt-dlp)")

        # Default download path
        self.download_path = str(Path.home() / "Downloads")

        # Available formats data
        self.available_formats = None
        self.max_height = None
        self.max_audio_bitrate = None

        # Set responsive window size
        self.set_responsive_size()

        # Initialize UI
        self.create_widgets()

        # Center window
        self.center_window()

    def set_responsive_size(self):
        """Set window size based on screen resolution and DPI scaling"""
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()

        # Calculate appropriate window size (60% of screen height, maintain aspect ratio)
        window_height = min(int(screen_height * 0.75), 1000)
        window_width = min(int(window_height * 0.9), 900)

        # Ensure minimum size
        window_width = max(window_width, 700)
        window_height = max(window_height, 700)

        self.window.geometry(f"{window_width}x{window_height}")
        self.window.minsize(700, 700)

    def center_window(self):
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f'{width}x{height}+{x}+{y}')

    def create_widgets(self):
        # Create scrollable frame
        self.main_frame = ctk.CTkScrollableFrame(self.window)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Title
        title_label = ctk.CTkLabel(
            self.main_frame,
            text="YouTube Downloader Pro",
            font=ctk.CTkFont(size=28, weight="bold")
        )
        title_label.pack(pady=20)

        # URL Frame
        url_frame = ctk.CTkFrame(self.main_frame)
        url_frame.pack(pady=10, padx=20, fill="x")

        url_label = ctk.CTkLabel(url_frame, text="Video URL:", font=ctk.CTkFont(size=14, weight="bold"))
        url_label.pack(anchor="w", padx=10, pady=(10, 5))

        url_input_frame = ctk.CTkFrame(url_frame)
        url_input_frame.pack(padx=10, pady=(0, 10), fill="x")

        self.url_entry = ctk.CTkEntry(
            url_input_frame,
            placeholder_text="https://www.youtube.com/watch?v=...",
            height=40,
            font=ctk.CTkFont(size=12)
        )
        self.url_entry.pack(side="left", padx=(0, 5), fill="x", expand=True)

        self.analyze_button = ctk.CTkButton(
            url_input_frame,
            text="Analyze",
            command=self.analyze_video,
            width=100,
            height=40,
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.analyze_button.pack(side="right")

        # Analysis Status Label
        self.analysis_status = ctk.CTkLabel(
            url_frame,
            text="",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        self.analysis_status.pack(padx=10, pady=(0, 10))

        # Format Selection Frame
        format_frame = ctk.CTkFrame(self.main_frame)
        format_frame.pack(pady=10, padx=20, fill="x")

        format_title = ctk.CTkLabel(format_frame, text="Download Type:", font=ctk.CTkFont(size=14, weight="bold"))
        format_title.pack(anchor="w", padx=10, pady=(10, 5))

        format_select_frame = ctk.CTkFrame(format_frame)
        format_select_frame.pack(padx=10, pady=(0, 10), fill="x")

        self.format_var = ctk.StringVar(value="video")
        format_radio1 = ctk.CTkRadioButton(
            format_select_frame,
            text="Video",
            variable=self.format_var,
            value="video",
            command=self.toggle_options,
            font=ctk.CTkFont(size=13)
        )
        format_radio1.pack(side="left", padx=20, pady=10)

        format_radio2 = ctk.CTkRadioButton(
            format_select_frame,
            text="Audio Only",
            variable=self.format_var,
            value="audio",
            command=self.toggle_options,
            font=ctk.CTkFont(size=13)
        )
        format_radio2.pack(side="left", padx=20, pady=10)

        # Video Options Frame
        self.video_options_frame = ctk.CTkFrame(self.main_frame)
        self.video_options_frame.pack(pady=10, padx=20, fill="x")

        video_title = ctk.CTkLabel(
            self.video_options_frame,
            text="Video Options:",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        video_title.grid(row=0, column=0, columnspan=3, padx=10, pady=(10, 15), sticky="w")

        # Video Quality
        quality_label = ctk.CTkLabel(self.video_options_frame, text="Quality:", font=ctk.CTkFont(size=13))
        quality_label.grid(row=1, column=0, padx=10, pady=10, sticky="w")

        self.video_quality_var = ctk.StringVar(value="best")
        self.quality_menu = ctk.CTkComboBox(
            self.video_options_frame,
            values=["best", "8K (4320p)", "4K (2160p)", "2K (1440p)", "1080p", "720p", "640p", "480p", "360p", "240p", "144p"],
            variable=self.video_quality_var,
            width=200
        )
        self.quality_menu.grid(row=1, column=1, columnspan=2, padx=10, pady=10, sticky="w")

        # Video Codec
        codec_label = ctk.CTkLabel(self.video_options_frame, text="Video Codec:", font=ctk.CTkFont(size=13))
        codec_label.grid(row=2, column=0, padx=10, pady=10, sticky="w")

        self.video_codec_var = ctk.StringVar(value="any")
        self.codec_menu = ctk.CTkComboBox(
            self.video_options_frame,
            values=["any", "AV1", "VP9", "VP8", "AVC (H.264)"],
            variable=self.video_codec_var,
            width=200
        )
        self.codec_menu.grid(row=2, column=1, columnspan=2, padx=10, pady=10, sticky="w")

        # Video Container
        container_label = ctk.CTkLabel(self.video_options_frame, text="Container:", font=ctk.CTkFont(size=13))
        container_label.grid(row=3, column=0, padx=10, pady=10, sticky="w")

        self.video_container_var = ctk.StringVar(value="mp4")
        self.container_menu = ctk.CTkComboBox(
            self.video_options_frame,
            values=["mp4", "mkv", "webm", "avi"],
            variable=self.video_container_var,
            width=200
        )
        self.container_menu.grid(row=3, column=1, columnspan=2, padx=10, pady=(10, 15), sticky="w")

        # Audio Options Frame
        self.audio_options_frame = ctk.CTkFrame(self.main_frame)

        audio_title = ctk.CTkLabel(
            self.audio_options_frame,
            text="Audio Options:",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        audio_title.grid(row=0, column=0, columnspan=3, padx=10, pady=(10, 15), sticky="w")

        # Audio Quality (Bitrate)
        audio_quality_label = ctk.CTkLabel(self.audio_options_frame, text="Audio Quality:", font=ctk.CTkFont(size=13))
        audio_quality_label.grid(row=1, column=0, padx=10, pady=10, sticky="w")

        self.audio_quality_var = ctk.StringVar(value="192 kbps")
        self.audio_quality_menu = ctk.CTkComboBox(
            self.audio_options_frame,
            values=["best", "320 kbps", "256 kbps", "192 kbps", "128 kbps", "96 kbps", "64 kbps"],
            variable=self.audio_quality_var,
            width=200
        )
        self.audio_quality_menu.grid(row=1, column=1, columnspan=2, padx=10, pady=10, sticky="w")

        # Audio Format
        audio_format_label = ctk.CTkLabel(self.audio_options_frame, text="Audio Format:", font=ctk.CTkFont(size=13))
        audio_format_label.grid(row=2, column=0, padx=10, pady=10, sticky="w")

        self.audio_format_var = ctk.StringVar(value="mp3")
        self.audio_format_menu = ctk.CTkComboBox(
            self.audio_options_frame,
            values=["mp3", "aac", "opus", "m4a", "wav", "flac"],
            variable=self.audio_format_var,
            width=200
        )
        self.audio_format_menu.grid(row=2, column=1, columnspan=2, padx=10, pady=(10, 15), sticky="w")

        # Download Path Frame
        path_frame = ctk.CTkFrame(self.main_frame)
        path_frame.pack(pady=10, padx=20, fill="x")

        path_label = ctk.CTkLabel(path_frame, text="Download Location:", font=ctk.CTkFont(size=14, weight="bold"))
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
            text="Browse",
            command=self.browse_folder,
            width=100
        )
        browse_button.pack(side="right")

        # Progress Frame (in main window, not scrollable)
        self.progress_frame = ctk.CTkFrame(self.window)
        self.progress_frame.pack(pady=10, padx=20, fill="x", side="bottom")

        self.progress_label = ctk.CTkLabel(
            self.progress_frame,
            text="Ready to download",
            font=ctk.CTkFont(size=12)
        )
        self.progress_label.pack(padx=10, pady=(10, 5))

        self.progress_bar = ctk.CTkProgressBar(self.progress_frame)
        self.progress_bar.pack(padx=10, pady=(0, 10), fill="x")
        self.progress_bar.set(0)

        # Download Button (in main window, not scrollable)
        self.download_button = ctk.CTkButton(
            self.window,
            text="Download",
            command=self.start_download,
            height=45,
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.download_button.pack(pady=10, padx=20, fill="x", side="bottom")

        # Log Frame (back in scrollable frame)
        log_frame = ctk.CTkFrame(self.main_frame)
        log_frame.pack(pady=10, padx=20, fill="both", expand=True)

        log_label = ctk.CTkLabel(log_frame, text="Log:", font=ctk.CTkFont(size=14, weight="bold"))
        log_label.pack(anchor="w", padx=10, pady=(10, 5))

        self.log_text = ctk.CTkTextbox(log_frame, height=200, font=ctk.CTkFont(size=11))
        self.log_text.pack(padx=10, pady=(0, 10), fill="both", expand=True)

        # Initialize options visibility
        self.toggle_options()

    def toggle_options(self):
        """Toggle between video and audio options"""
        if self.format_var.get() == "video":
            self.video_options_frame.pack(pady=10, padx=20, fill="x", after=self.video_options_frame.master.children[list(self.video_options_frame.master.children.keys())[2]])
            self.audio_options_frame.pack_forget()
        else:
            self.video_options_frame.pack_forget()
            self.audio_options_frame.pack(pady=10, padx=20, fill="x", after=self.audio_options_frame.master.children[list(self.audio_options_frame.master.children.keys())[2]])

    def analyze_video(self):
        """Analyze video URL to get available formats"""
        url = self.url_entry.get().strip()

        if not url:
            messagebox.showerror("Error", "Please enter a video URL")
            return

        if not url.startswith("http"):
            messagebox.showerror("Error", "Please enter a valid URL")
            return

        # Check if yt-dlp is installed
        if not self.check_ytdlp():
            messagebox.showerror(
                "Error",
                "yt-dlp is not installed or not found in PATH.\n\n"
                "Please install it using:\npip install yt-dlp"
            )
            return

        # Disable analyze button
        self.analyze_button.configure(state="disabled")
        self.analysis_status.configure(text="Analyzing video...")

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

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                self.analysis_status.configure(text="Analysis failed", text_color="red")
                self.log_message(f"Analysis error: {result.stderr}")
                messagebox.showerror("Error", "Failed to analyze video. Check the URL and try again.")
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
                text=f"✓ Max Quality: {max_height}p | Max Audio: {int(max_audio_br)} kbps | Title: {video_title[:50]}...",
                text_color="green"
            )
            self.log_message(f"Analysis complete - Max video: {max_height}p, Max audio: {int(max_audio_br)} kbps")

        except subprocess.TimeoutExpired:
            self.analysis_status.configure(text="Analysis timeout", text_color="red")
            self.log_message("Analysis timeout - URL may be invalid or network is slow")
            messagebox.showerror("Error", "Analysis timeout. Please try again.")
        except json.JSONDecodeError:
            self.analysis_status.configure(text="Analysis failed", text_color="red")
            self.log_message("Failed to parse video information")
            messagebox.showerror("Error", "Failed to parse video information.")
        except Exception as e:
            self.analysis_status.configure(text="Analysis error", text_color="red")
            self.log_message(f"Analysis error: {str(e)}")
            messagebox.showerror("Error", f"Analysis error: {str(e)}")
        finally:
            self.analyze_button.configure(state="normal")

    def update_quality_options(self):
        """Update quality options based on analysis results"""
        if self.max_height is None:
            return

        # Video quality options
        quality_options = [
            ("best", 999999),
            ("8K (4320p)", 4320),
            ("4K (2160p)", 2160),
            ("2K (1440p)", 1440),
            ("1080p", 1080),
            ("720p", 720),
            ("640p", 640),
            ("480p", 480),
            ("360p", 360),
            ("240p", 240),
            ("144p", 144)
        ]

        updated_options = []
        for label, height in quality_options:
            if label == "best" or height <= self.max_height:
                updated_options.append(label)
            else:
                updated_options.append(f"{label} (사용 불가)")

        self.quality_menu.configure(values=updated_options)

        # Audio quality options
        audio_options = [
            ("best", 999999),
            ("320 kbps", 320),
            ("256 kbps", 256),
            ("192 kbps", 192),
            ("128 kbps", 128),
            ("96 kbps", 96),
            ("64 kbps", 64)
        ]

        updated_audio = []
        for label, bitrate in audio_options:
            if label == "best" or bitrate <= self.max_audio_bitrate:
                updated_audio.append(label)
            else:
                updated_audio.append(f"{label} (사용 불가)")

        self.audio_quality_menu.configure(values=updated_audio)

    def browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.download_path = folder
            self.path_entry.delete(0, "end")
            self.path_entry.insert(0, folder)

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
        url = self.url_entry.get().strip()

        if not url:
            messagebox.showerror("Error", "Please enter a video URL")
            return

        if not url.startswith("http"):
            messagebox.showerror("Error", "Please enter a valid URL")
            return

        # Check if yt-dlp is installed
        if not self.check_ytdlp():
            messagebox.showerror(
                "Error",
                "yt-dlp is not installed or not found in PATH.\n\n"
                "Please install it using:\npip install yt-dlp"
            )
            return

        # Check for unavailable options
        selected_quality = self.video_quality_var.get()
        selected_audio = self.audio_quality_var.get()

        if "(사용 불가)" in selected_quality:
            messagebox.showerror("Error", "Selected video quality is not available. Please choose a different quality or click 'Analyze' first.")
            return

        if "(사용 불가)" in selected_audio:
            messagebox.showerror("Error", "Selected audio quality is not available. Please choose a different quality or click 'Analyze' first.")
            return

        # Disable download button
        self.download_button.configure(state="disabled")

        # Start download in separate thread
        thread = threading.Thread(target=self.download_video, args=(url,))
        thread.daemon = True
        thread.start()

    def build_format_string(self):
        """Build yt-dlp format string based on user selections"""
        if self.format_var.get() == "audio":
            return None  # Audio format is handled separately

        # Video format
        format_parts = []

        # Get quality
        quality = self.video_quality_var.get()
        if "8K" in quality or "4320p" in quality:
            height = "4320"
        elif "4K" in quality or "2160p" in quality:
            height = "2160"
        elif "2K" in quality or "1440p" in quality:
            height = "1440"
        elif "1080p" in quality:
            height = "1080"
        elif "720p" in quality:
            height = "720"
        elif "640p" in quality:
            height = "640"
        elif "480p" in quality:
            height = "480"
        elif "360p" in quality:
            height = "360"
        elif "240p" in quality:
            height = "240"
        elif "144p" in quality:
            height = "144"
        else:
            height = None

        # Build video format selector
        video_selector = "bestvideo"

        if height:
            video_selector += f"[height<={height}]"

        # Get codec
        codec = self.video_codec_var.get()
        if codec != "any":
            if codec == "AV1":
                video_selector += "[vcodec^=av01]"
            elif codec == "VP9":
                video_selector += "[vcodec^=vp9]"
            elif codec == "VP8":
                video_selector += "[vcodec^=vp8]"
            elif codec == "AVC (H.264)":
                video_selector += "[vcodec^=avc]"

        # Combine video and audio
        format_string = f"{video_selector}+bestaudio/best"

        return format_string

    def download_video(self, url):
        try:
            self.log_message(f"Starting download: {url}")
            self.progress_label.configure(text="Downloading...")
            self.progress_bar.set(0)

            # Build yt-dlp command
            output_template = os.path.join(self.download_path, "%(title)s.%(ext)s")

            cmd = ["yt-dlp", url, "-o", output_template]

            # Add format options
            if self.format_var.get() == "audio":
                # Audio download
                audio_format = self.audio_format_var.get()
                audio_quality = self.audio_quality_var.get()

                cmd.extend(["-x", "--audio-format", audio_format])

                if audio_quality != "best":
                    # Extract bitrate number
                    bitrate = audio_quality.split()[0]
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
                cmd.extend(["--merge-output-format", container])

                # Log settings
                self.log_message(f"Format: Video")
                self.log_message(f"Quality: {self.video_quality_var.get()}")
                self.log_message(f"Video Codec: {self.video_codec_var.get()}")
                self.log_message(f"Container: {container.upper()}")

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
                self.progress_label.configure(text="Download completed!")
                self.log_message("Download completed successfully!")
                messagebox.showinfo("Success", "Download completed successfully!")
            else:
                self.progress_label.configure(text="Download failed")
                self.log_message("Download failed!")
                messagebox.showerror("Error", "Download failed. Check the log for details.")

        except Exception as e:
            self.log_message(f"Error: {str(e)}")
            self.progress_label.configure(text="Error occurred")
            messagebox.showerror("Error", f"An error occurred:\n{str(e)}")

        finally:
            # Re-enable download button
            self.download_button.configure(state="normal")

    def run(self):
        self.window.mainloop()


def main():
    app = YouTubeDownloaderGUI()
    app.run()


if __name__ == "__main__":
    main()
