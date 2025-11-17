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
        self.window.title("YouTube Downloader (yt-dlp)")
        self.window.geometry("800x700")

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
        # Title
        title_label = ctk.CTkLabel(
            self.window,
            text="YouTube Downloader",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(pady=20)

        # URL Frame
        url_frame = ctk.CTkFrame(self.window)
        url_frame.pack(pady=10, padx=20, fill="x")

        url_label = ctk.CTkLabel(url_frame, text="Video URL:", font=ctk.CTkFont(size=14))
        url_label.pack(anchor="w", padx=10, pady=(10, 5))

        self.url_entry = ctk.CTkEntry(
            url_frame,
            placeholder_text="https://www.youtube.com/watch?v=...",
            height=40,
            font=ctk.CTkFont(size=12)
        )
        self.url_entry.pack(padx=10, pady=(0, 10), fill="x")

        # Options Frame
        options_frame = ctk.CTkFrame(self.window)
        options_frame.pack(pady=10, padx=20, fill="x")

        # Format Selection
        format_label = ctk.CTkLabel(options_frame, text="Format:", font=ctk.CTkFont(size=14))
        format_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")

        self.format_var = ctk.StringVar(value="video")
        format_radio1 = ctk.CTkRadioButton(
            options_frame,
            text="Video",
            variable=self.format_var,
            value="video"
        )
        format_radio1.grid(row=0, column=1, padx=5, pady=10)

        format_radio2 = ctk.CTkRadioButton(
            options_frame,
            text="Audio Only",
            variable=self.format_var,
            value="audio"
        )
        format_radio2.grid(row=0, column=2, padx=5, pady=10)

        # Quality Selection
        quality_label = ctk.CTkLabel(options_frame, text="Quality:", font=ctk.CTkFont(size=14))
        quality_label.grid(row=1, column=0, padx=10, pady=10, sticky="w")

        self.quality_var = ctk.StringVar(value="best")
        quality_menu = ctk.CTkComboBox(
            options_frame,
            values=["best", "1080p", "720p", "480p", "360p"],
            variable=self.quality_var,
            width=150
        )
        quality_menu.grid(row=1, column=1, columnspan=2, padx=5, pady=10, sticky="w")

        # Download Path Frame
        path_frame = ctk.CTkFrame(self.window)
        path_frame.pack(pady=10, padx=20, fill="x")

        path_label = ctk.CTkLabel(path_frame, text="Download Location:", font=ctk.CTkFont(size=14))
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

        # Progress Frame
        progress_frame = ctk.CTkFrame(self.window)
        progress_frame.pack(pady=10, padx=20, fill="x")

        self.progress_label = ctk.CTkLabel(
            progress_frame,
            text="Ready to download",
            font=ctk.CTkFont(size=12)
        )
        self.progress_label.pack(padx=10, pady=(10, 5))

        self.progress_bar = ctk.CTkProgressBar(progress_frame)
        self.progress_bar.pack(padx=10, pady=(0, 10), fill="x")
        self.progress_bar.set(0)

        # Download Button
        self.download_button = ctk.CTkButton(
            self.window,
            text="Download",
            command=self.start_download,
            height=45,
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.download_button.pack(pady=10, padx=20, fill="x")

        # Log Frame
        log_frame = ctk.CTkFrame(self.window)
        log_frame.pack(pady=10, padx=20, fill="both", expand=True)

        log_label = ctk.CTkLabel(log_frame, text="Log:", font=ctk.CTkFont(size=14))
        log_label.pack(anchor="w", padx=10, pady=(10, 5))

        self.log_text = ctk.CTkTextbox(log_frame, height=150, font=ctk.CTkFont(size=11))
        self.log_text.pack(padx=10, pady=(0, 10), fill="both", expand=True)

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
                cmd.extend(["-x", "--audio-format", "mp3"])
                self.log_message("Format: Audio only (MP3)")
            else:
                quality = self.quality_var.get()
                if quality == "best":
                    cmd.extend(["-f", "bestvideo+bestaudio/best"])
                else:
                    height = quality.rstrip('p')
                    cmd.extend(["-f", f"bestvideo[height<={height}]+bestaudio/best[height<={height}]"])
                self.log_message(f"Format: Video - Quality: {quality}")

            # Add progress hook
            cmd.extend(["--newline", "--no-playlist"])

            self.log_message(f"Download location: {self.download_path}")
            self.log_message("Processing...")

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
