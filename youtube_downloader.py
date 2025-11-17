import customtkinter as ctk
from tkinter import filedialog, messagebox
import os
import sys
import threading
import subprocess
import json
from pathlib import Path

# Set appearance
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class YouTubeDownloaderGUI:
    def __init__(self):
        self.window = ctk.CTk()
        self.window.title("YouTube Downloader Pro (yt-dlp)")
        self.window.geometry("900x900")

        # Default download path
        self.download_path = str(Path.home() / "Downloads")

        # Initialize UI
        self.create_widgets()

        # Center window
        self.center_window()

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

        self.url_entry = ctk.CTkEntry(
            url_frame,
            placeholder_text="https://www.youtube.com/watch?v=...",
            height=40,
            font=ctk.CTkFont(size=12)
        )
        self.url_entry.pack(padx=10, pady=(0, 10), fill="x")

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
        quality_menu = ctk.CTkComboBox(
            self.video_options_frame,
            values=["best", "8K (4320p)", "4K (2160p)", "2K (1440p)", "1080p", "720p", "640p", "480p", "360p", "240p", "144p"],
            variable=self.video_quality_var,
            width=180
        )
        quality_menu.grid(row=1, column=1, columnspan=2, padx=10, pady=10, sticky="w")

        # Video Codec
        codec_label = ctk.CTkLabel(self.video_options_frame, text="Video Codec:", font=ctk.CTkFont(size=13))
        codec_label.grid(row=2, column=0, padx=10, pady=10, sticky="w")

        self.video_codec_var = ctk.StringVar(value="any")
        codec_menu = ctk.CTkComboBox(
            self.video_options_frame,
            values=["any", "AV1", "VP9", "VP8", "AVC (H.264)"],
            variable=self.video_codec_var,
            width=180
        )
        codec_menu.grid(row=2, column=1, columnspan=2, padx=10, pady=10, sticky="w")

        # Video Container
        container_label = ctk.CTkLabel(self.video_options_frame, text="Container:", font=ctk.CTkFont(size=13))
        container_label.grid(row=3, column=0, padx=10, pady=10, sticky="w")

        self.video_container_var = ctk.StringVar(value="mp4")
        container_menu = ctk.CTkComboBox(
            self.video_options_frame,
            values=["mp4", "mkv", "webm", "avi"],
            variable=self.video_container_var,
            width=180
        )
        container_menu.grid(row=3, column=1, columnspan=2, padx=10, pady=(10, 15), sticky="w")

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

        self.audio_quality_var = ctk.StringVar(value="192")
        audio_quality_menu = ctk.CTkComboBox(
            self.audio_options_frame,
            values=["best", "320 kbps", "256 kbps", "192 kbps", "128 kbps", "96 kbps", "64 kbps"],
            variable=self.audio_quality_var,
            width=180
        )
        audio_quality_menu.grid(row=1, column=1, columnspan=2, padx=10, pady=10, sticky="w")

        # Audio Format
        audio_format_label = ctk.CTkLabel(self.audio_options_frame, text="Audio Format:", font=ctk.CTkFont(size=13))
        audio_format_label.grid(row=2, column=0, padx=10, pady=10, sticky="w")

        self.audio_format_var = ctk.StringVar(value="mp3")
        audio_format_menu = ctk.CTkComboBox(
            self.audio_options_frame,
            values=["mp3", "aac", "opus", "m4a", "wav", "flac"],
            variable=self.audio_format_var,
            width=180
        )
        audio_format_menu.grid(row=2, column=1, columnspan=2, padx=10, pady=(10, 15), sticky="w")

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
