#!/usr/bin/env python3

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pynput.mouse as mouse
import pynput.keyboard as keyboard
import threading
from time import time, sleep
import pickle
import sys
import subprocess
import os
import requests
import hashlib
import re
import random
import webbrowser

__version__ = "1.0"

class MacroRecorder:
    def __init__(self, root):
        self.root = root
        self.root.title("Macro Recorder")
        self.root.geometry("320x340")  # Adjusted window height
        self.root.resizable(False, False)
        self.root.attributes('-topmost', True)

        self.recording = False
        self.playing = False
        self.events = []
        self.loop_infinite = False

        self.style = ttk.Style()
        self.theme = 'light'  # Default theme

        self.create_widgets()
        self.apply_light_theme()  # Apply default theme

        self.mouse_listener = mouse.Listener(on_click=self.on_click, on_move=self.on_move)
        self.keyboard_listener = keyboard.Listener(on_press=self.on_press)

        self.mouse_listener.start()
        self.keyboard_listener.start()

    def create_widgets(self):
        # Menu Bar
        self.menubar = tk.Menu(self.root)
        # File Menu
        self.file_menu = tk.Menu(self.menubar, tearoff=0)
        self.file_menu.add_command(label="Save Script", command=self.save_script)
        self.file_menu.add_command(label="Load Script", command=self.load_script)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Exit", command=self.root.quit)
        self.menubar.add_cascade(label="File", menu=self.file_menu)
        # Theme Menu
        self.theme_menu = tk.Menu(self.menubar, tearoff=0)
        self.theme_menu.add_command(label="Light Theme", command=self.apply_light_theme)
        self.theme_menu.add_command(label="Dark Theme", command=self.apply_dark_theme)
        self.menubar.add_cascade(label="Theme", menu=self.theme_menu)
        # Help Menu
        self.help_menu = tk.Menu(self.menubar, tearoff=0)
        self.help_menu.add_command(label="About", command=self.show_about)
        self.menubar.add_cascade(label="Help", menu=self.help_menu)
        # Configure Menu Bar
        self.root.config(menu=self.menubar)

        # Main Frame
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(pady=10)

        button_width = 20

        # Record Button
        self.record_button = ttk.Button(
            self.main_frame, text="Record (F6)", command=self.toggle_recording,
            width=button_width, style='Record.TButton'
        )
        self.record_button.pack(pady=5)

        # Play Button
        self.play_button = ttk.Button(
            self.main_frame, text="Play/Pause (F5)", command=self.toggle_playing,
            width=button_width, style='Play.TButton'
        )
        self.play_button.pack(pady=5)

        # Controls Frame
        self.controls_frame = ttk.Frame(self.root)
        self.controls_frame.pack(pady=10)

        self.loop_label = ttk.Label(self.controls_frame, text="Loop Count:")
        self.loop_label.grid(row=0, column=0, padx=5, pady=5)
        self.loop_entry = ttk.Entry(self.controls_frame, width=5, justify='center')
        self.loop_entry.insert(0, "1")  # Default value
        self.loop_entry.grid(row=0, column=1, padx=5, pady=5)

        self.loop_infinite_var = tk.BooleanVar()
        self.loop_infinite_check = ttk.Checkbutton(
            self.controls_frame, text="Loop Infinite",
            variable=self.loop_infinite_var, command=self.toggle_loop_infinite
        )
        self.loop_infinite_check.grid(row=1, column=0, columnspan=2, pady=5)

        # Update Button
        self.update_button = ttk.Button(
            self.root, text="Check for Updates", command=self.check_for_updates,
            width=button_width, style='Update.TButton'
        )
        self.update_button.pack(pady=10)

    def apply_light_theme(self):
        self.theme = 'light'
        # Light theme colors
        self.bg_color = '#f0f0f0'        # Light background
        self.fg_color = '#000000'        # Black text
        self.entry_bg = '#ffffff'
        self.entry_fg = '#000000'
        self.menu_bg = '#f0f0f0'
        self.menu_fg = '#000000'
        self.link_color = 'blue'

        # Set button colors
        self.record_button_color = '#ff4d4d'  # Red
        self.play_button_color = '#32cd32'    # Green
        self.update_button_color = '#0078d7'  # Blue

        self.update_styles()

    def apply_dark_theme(self):
        self.theme = 'dark'
        # Dark theme colors
        self.bg_color = '#2e2e2e'        # Dark background
        self.fg_color = '#ffffff'        # White text
        self.entry_bg = '#3e3e3e'
        self.entry_fg = '#ffffff'
        self.menu_bg = '#2e2e2e'
        self.menu_fg = '#ffffff'
        self.link_color = 'cyan'

        # Set button colors
        self.record_button_color = '#ff4d4d'  # Red
        self.play_button_color = '#32cd32'    # Green
        self.update_button_color = '#1a73e8'  # Blue

        self.update_styles()

    def update_styles(self):
        # Update window background
        self.root.configure(background=self.bg_color)
        # Configure styles for ttk widgets
        self.style.configure('TFrame', background=self.bg_color)
        self.style.configure('TLabel', background=self.bg_color, foreground=self.fg_color)
        self.style.configure('TEntry', fieldbackground=self.entry_bg, foreground=self.entry_fg)
        self.style.configure('TCheckbutton', background=self.bg_color, foreground=self.fg_color)
        self.style.map('TCheckbutton', background=[('active', self.bg_color)], foreground=[('active', self.fg_color)])

        # Record Button Style
        self.style.configure('Record.TButton', background=self.record_button_color, foreground='#ffffff')
        self.style.map('Record.TButton', background=[('active', self.record_button_color)], foreground=[('active', '#ffffff')])

        # Play Button Style
        self.style.configure('Play.TButton', background=self.play_button_color, foreground='#ffffff')
        self.style.map('Play.TButton', background=[('active', self.play_button_color)], foreground=[('active', '#ffffff')])

        # Update Button Style
        self.style.configure('Update.TButton', background=self.update_button_color, foreground='#ffffff')
        self.style.map('Update.TButton', background=[('active', self.update_button_color)], foreground=[('active', '#ffffff')])

        # Update menu styles
        self.menubar.configure(background=self.menu_bg, foreground=self.menu_fg)
        self.file_menu.configure(background=self.menu_bg, foreground=self.menu_fg)
        self.theme_menu.configure(background=self.menu_bg, foreground=self.menu_fg)
        self.help_menu.configure(background=self.menu_bg, foreground=self.menu_fg)

        # Update all frames and widgets background
        for frame in [self.main_frame, self.controls_frame]:
            frame.configure(style='TFrame')

        # Update the About window if it's open
        if hasattr(self, 'about_window') and self.about_window.winfo_exists():
            self.about_window.configure(background=self.bg_color)
            for widget in self.about_window.winfo_children():
                if isinstance(widget, ttk.Label):
                    widget.configure(background=self.bg_color, foreground=self.fg_color)
                elif isinstance(widget, ttk.Button):
                    widget.configure(style='TButton')
                elif isinstance(widget, tk.Label):  # For the link
                    widget.configure(background=self.bg_color, foreground=self.link_color)

    def toggle_recording(self):
        self.recording = not self.recording
        if self.recording:
            self.events = []
            self.start_time = time()
            self.last_time = self.start_time
            self.record_button.config(text="Stop Recording (F6)")
        else:
            self.record_button.config(text="Record (F6)")

    def toggle_playing(self):
        if not self.playing:
            if not self.events:
                messagebox.showwarning("No Events", "No recorded events to play.")
                return
            self.playing = True
            self.play_button.config(text="Pause Playback (F5)")
            threading.Thread(target=self.play_events).start()
        else:
            self.playing = False
            self.play_button.config(text="Play/Pause (F5)")

    def toggle_loop_infinite(self):
        self.loop_infinite = self.loop_infinite_var.get()
        if self.loop_infinite:
            self.loop_entry.config(state='disabled')
        else:
            self.loop_entry.config(state='normal')

    def save_script(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".pkl",
                                                 filetypes=[("Macro Script Files", "*.pkl")])
        if file_path:
            with open(file_path, "wb") as f:
                pickle.dump(self.events, f)
            messagebox.showinfo("Success", "Script saved successfully!")

    def load_script(self):
        file_path = filedialog.askopenfilename(filetypes=[("Macro Script Files", "*.pkl")])
        if file_path:
            with open(file_path, "rb") as f:
                self.events = pickle.load(f)
            messagebox.showinfo("Success", "Script loaded successfully!")

    def on_click(self, x, y, button, pressed):
        if self.recording:
            current_time = time()
            delay = current_time - self.last_time
            self.last_time = current_time
            self.events.append(("click", x, y, button, pressed, delay))

    def on_move(self, x, y):
        if self.recording:
            current_time = time()
            delay = current_time - self.last_time
            self.last_time = current_time
            self.events.append(("move", x, y, delay))

    def on_press(self, key):
        try:
            if key == keyboard.Key.f6:
                self.toggle_recording()
            elif key == keyboard.Key.f5:
                self.toggle_playing()
        except AttributeError:
            pass

    def play_events(self):
        if not self.events:
            messagebox.showwarning("No Events", "No recorded events to play.")
            self.playing = False
            self.play_button.config(text="Play/Pause (F5)")
            return

        try:
            if self.loop_infinite:
                loop_count = float('inf')
            else:
                loop_count = int(self.loop_entry.get())
                if loop_count <= 0:
                    raise ValueError
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid positive integer for loop count.")
            self.loop_entry.delete(0, tk.END)
            self.loop_entry.insert(0, "1")
            loop_count = 1

        count = 0
        while self.playing and (self.loop_infinite or count < loop_count):
            for event in self.events:
                if not self.playing:
                    break
                sleep(event[-1])  # Delay before the event
                if event[0] == "click":
                    x, y, button, pressed = event[1], event[2], event[3], event[4]
                    mouse.Controller().position = (x, y)
                    if pressed:
                        mouse.Controller().press(button)
                    else:
                        mouse.Controller().release(button)
                elif event[0] == "move":
                    x, y = event[1], event[2]
                    mouse.Controller().position = (x, y)
            if not self.loop_infinite:
                count += 1

        self.playing = False
        self.play_button.config(text="Play/Pause (F5)")

    def normalize_line_endings(self, content):
        return re.sub(rb'\r\n?', b'\n', content)

    def check_for_updates(self):
        version_url = f"https://raw.githubusercontent.com/V4mpw0L/MacroRecorder/main/version.txt?nocache={random.randint(1,100000)}"
        try:
            response = requests.get(version_url, timeout=5)
            if response.status_code == 200:
                online_version = response.text.strip()
                if online_version != __version__:
                    update = messagebox.askyesno("Update Available",
                                                 f"A new version ({online_version}) is available.\nWould you like to update?")
                    if update:
                        self.perform_update()
                else:
                    messagebox.showinfo("No Update", "You are using the latest version.")
            else:
                messagebox.showerror("Error", "Unable to check for updates.")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while checking for updates:\n{e}")

    def perform_update(self):
        script_url = f"https://raw.githubusercontent.com/V4mpw0L/MacroRecorder/main/autoclicker.py?nocache={random.randint(1,100000)}"
        try:
            response = requests.get(script_url, timeout=10)
            if response.status_code == 200:
                remote_script = response.content
                script_path = os.path.abspath(__file__)
                if os.access(script_path, os.W_OK):
                    with open(script_path, 'wb') as f:
                        f.write(remote_script)
                    messagebox.showinfo("Update Successful", "The application has been updated. Please restart.")
                    sys.exit()
                else:
                    messagebox.showerror("Error", "No write permission to update the script file. Please run the application with appropriate permissions.")
            else:
                messagebox.showerror("Error", "Failed to download the update.")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred during the update:\n{e}")

    def show_about(self):
        # Create a custom About window
        self.about_window = tk.Toplevel(self.root)
        self.about_window.title("About Macro Recorder")
        self.about_window.resizable(False, False)
        self.about_window.geometry("400x200")
        self.about_window.attributes('-topmost', True)

        # Apply theme to the About window
        self.about_window.configure(background=self.bg_color)

        # Center the window relative to the parent window
        x = self.root.winfo_x() + (self.root.winfo_width() - 400) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - 200) // 2
        self.about_window.geometry(f"+{x}+{y}")

        # Labels
        ttk.Label(self.about_window, text=f"Macro Recorder v{__version__}", font=('Helvetica', 12, 'bold'), background=self.bg_color, foreground=self.fg_color).pack(pady=10)
        ttk.Label(self.about_window, text="Created by V4mpw0L", background=self.bg_color, foreground=self.fg_color).pack(pady=5)

        # GitHub Link
        link = tk.Label(self.about_window, text="GitHub Repository", fg=self.link_color, cursor="hand2", background=self.bg_color)
        link.pack(pady=5)
        link.bind("<Button-1>", lambda e: webbrowser.open("https://github.com/V4mpw0L/MacroRecorder"))

        # Close Button
        ttk.Button(self.about_window, text="Close", command=self.about_window.destroy).pack(pady=10)

if __name__ == "__main__":
    try:
        import requests
    except ImportError:
        install = messagebox.askyesno("Missing Package",
                                      "The 'requests' package is missing.\nWould you like to install it now?")
        if install:
            try:
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'requests'])
                messagebox.showinfo("Package Installed", "The 'requests' package has been installed. Please restart the application.")
            except Exception as e:
                messagebox.showerror("Installation Error", f"An error occurred while installing 'requests':\n{e}")
            sys.exit()
        else:
            messagebox.showwarning("Missing Package", "The application cannot run without the 'requests' package.")
            sys.exit()

    root = tk.Tk()
    app = MacroRecorder(root)
    root.mainloop()
