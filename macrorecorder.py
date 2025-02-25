#!/usr/bin/env python3

# Windows UAC elevation
import os
import sys
if os.name == 'nt':
    import ctypes
    if ctypes.windll.shell32.IsUserAnAdmin() == 0:
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        sys.exit()

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pynput.mouse as mouse
import pynput.keyboard as keyboard
import threading
from time import time, sleep
import pickle
import subprocess
import requests
import random
import webbrowser
import logging
import json
from queue import Queue
import platform
from typing import Optional, Tuple, Any

__version__ = "2.2"

# Configure logging with secure permissions
logging.basicConfig(
    filename='macro_recorder.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filemode='a'
)
if os.path.exists('macro_recorder.log'):
    os.chmod('macro_recorder.log', 0o600)

class KeyListener(threading.Thread):
    def __init__(self, queue: Queue):
        super().__init__(daemon=True)
        self.queue = queue
        self.listener = None

    def run(self) -> None:
        try:
            with keyboard.Listener(on_press=self.on_press) as self.listener:
                self.listener.join()
        except Exception as e:
            logging.error(f"Key listener error: {e}")

    def on_press(self, key: Any) -> bool:
        self.queue.put(key)
        return False

class MacroRecorder:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Macro Recorder")
        self.root.geometry("220x250")
        self.root.resizable(False, False)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.attributes('-topmost', True)
        
        self.is_windows = platform.system() == "Windows"
        self.recording = False
        self.playing = False
        self.events = []
        self.loop_infinite = False
        self.record_hotkey = 'f6'
        self.play_hotkey = 'f5'
        self.last_time = 0.0

        self.style = ttk.Style()
        self.theme = 'light'

        self.create_widgets()
        self.apply_light_theme()
        self.load_config()
        self.update_hotkey_buttons()

        self.mouse_listener = None
        self.keyboard_listener = None
        self.setup_listeners()

    def create_widgets(self) -> None:
        self.menubar = tk.Menu(self.root)
        
        # File Menu
        self.file_menu = tk.Menu(self.menubar, tearoff=0)
        self.file_menu.add_command(label="Save Script", command=self.save_script)
        self.file_menu.add_command(label="Load Script", command=self.load_script)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Exit", command=self.on_close)
        self.menubar.add_cascade(label="File", menu=self.file_menu)
        
        # Settings Menu
        self.settings_menu = tk.Menu(self.menubar, tearoff=0)
        self.settings_menu.add_command(label="Change Hotkeys", command=self.change_hotkeys)
        self.menubar.add_cascade(label="Settings", menu=self.settings_menu)
        
        # Theme Menu
        self.theme_menu = tk.Menu(self.menubar, tearoff=0)
        self.theme_menu.add_command(label="Light Theme", command=self.apply_light_theme)
        self.theme_menu.add_command(label="Dark Theme", command=self.apply_dark_theme)
        self.menubar.add_cascade(label="Theme", menu=self.theme_menu)
        
        # Help Menu
        self.help_menu = tk.Menu(self.menubar, tearoff=0)
        self.help_menu.add_command(label="About", command=self.show_about)
        self.help_menu.add_command(label="Donation", command=self.show_donation)
        self.menubar.add_cascade(label="Help", menu=self.help_menu)
        
        self.root.config(menu=self.menubar)

        # Main Interface
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(pady=5)

        button_width = 15
        self.record_button = ttk.Button(
            self.main_frame, text="Record (F6)", command=self.toggle_recording,
            width=button_width, style='Record.TButton'
        )
        self.record_button.pack(pady=3)

        self.play_button = ttk.Button(
            self.main_frame, text="Play/Pause (F5)", command=self.toggle_playing,
            width=button_width, style='Play.TButton'
        )
        self.play_button.pack(pady=3)

        # Controls Frame
        self.controls_frame = ttk.Frame(self.root)
        self.controls_frame.pack(pady=5)

        self.loop_label = ttk.Label(self.controls_frame, text="Loop Count:")
        self.loop_label.grid(row=0, column=0, padx=3, pady=3, sticky=tk.W)
        self.loop_entry = ttk.Entry(self.controls_frame, width=6, justify='center')
        self.loop_entry.insert(0, "1")
        self.loop_entry.grid(row=0, column=1, padx=3, pady=3, sticky=tk.E)

        self.loop_infinite_var = tk.BooleanVar()
        self.loop_infinite_label = ttk.Label(self.controls_frame, text="Infinite Loop:")
        self.loop_infinite_label.grid(row=1, column=0, padx=3, pady=3, sticky=tk.W)
        self.loop_infinite_check = ttk.Checkbutton(
            self.controls_frame,
            variable=self.loop_infinite_var, command=self.toggle_loop_infinite
        )
        self.loop_infinite_check.grid(row=1, column=1, padx=3, pady=3, sticky=tk.W)

        self.speed_label = ttk.Label(self.controls_frame, text="Speed Multiplier:")
        self.speed_label.grid(row=2, column=0, padx=3, pady=3, sticky=tk.W)
        self.speed_var = tk.StringVar(value="1.0")
        self.speed_entry = ttk.Entry(self.controls_frame, textvariable=self.speed_var, 
                                    width=6, justify='center')
        self.speed_entry.grid(row=2, column=1, padx=3, pady=3, sticky=tk.E)

        self.update_button = ttk.Button(
            self.root, text="Check for Updates", command=self.check_for_updates,
            width=button_width, style='Update.TButton'
        )
        self.update_button.pack(pady=5)

    def load_config(self) -> None:
        config_path = os.path.expanduser("~/.macro_recorder_config.json")
        default_config = {'record_hotkey': 'f6', 'play_hotkey': 'f5'}
        
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.record_hotkey = config.get('record_hotkey', 'f6').lower()
                    self.play_hotkey = config.get('play_hotkey', 'f5').lower()
            else:
                self.record_hotkey = default_config['record_hotkey']
                self.play_hotkey = default_config['play_hotkey']
                self.save_config()
        except (json.JSONDecodeError, PermissionError) as e:
            messagebox.showerror("Config Error", f"Failed to load config: {e}")
            self.record_hotkey = default_config['record_hotkey']
            self.play_hotkey = default_config['play_hotkey']
            logging.error(f"Config load error: {e}")

    def save_config(self) -> None:
        config = {'record_hotkey': self.record_hotkey, 'play_hotkey': self.play_hotkey}
        config_path = os.path.expanduser("~/.macro_recorder_config.json")
        
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
            os.chmod(config_path, 0o600)
        except (IOError, PermissionError) as e:
            messagebox.showerror("Config Error", f"Failed to save config: {e}")
            logging.error(f"Config save error: {e}")

    def validate_hotkey(self, input_str: str) -> Tuple[bool, str]:
        input_str = input_str.strip().lower()
        if not input_str:
            return False, "Hotkey cannot be empty"
        if len(input_str) == 1 and input_str.isalpha():
            return True, ""
        if hasattr(keyboard.Key, input_str):
            return True, ""
        return False, f"Invalid key: {input_str}"

    def change_hotkeys(self) -> None:
        dialog = tk.Toplevel(self.root)
        dialog.title("Change Hotkeys")
        dialog.geometry("300x200")
        dialog.resizable(False, False)
        dialog.attributes('-topmost', True)
        dialog.configure(background=self.bg_color)
        
        frame = ttk.Frame(dialog)
        frame.pack(pady=10, padx=10, fill='both', expand=True)

        ttk.Label(frame, text="Record Hotkey:", background=self.bg_color, 
                 foreground=self.fg_color).grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.record_btn = ttk.Button(frame, text=f"{self.record_hotkey.upper()} (Click to set)",
                                    command=lambda: self.set_hotkey(dialog, 'record'))
        self.record_btn.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(frame, text="Play Hotkey:", background=self.bg_color, 
                 foreground=self.fg_color).grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.play_btn = ttk.Button(frame, text=f"{self.play_hotkey.upper()} (Click to set)",
                                  command=lambda: self.set_hotkey(dialog, 'play'))
        self.play_btn.grid(row=1, column=1, padx=5, pady=5)
        
        self.status_label = ttk.Label(frame, text="", background=self.bg_color, 
                                    foreground=self.fg_color)
        self.status_label.grid(row=2, column=0, columnspan=2, pady=5)
        
        ttk.Button(frame, text="Save", command=lambda: self.save_new_hotkeys(dialog)
                  ).grid(row=3, column=0, columnspan=2, pady=10)

        x = self.root.winfo_x() + (self.root.winfo_width() - 300) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - 200) // 2
        dialog.geometry(f"+{x}+{y}")

    def set_hotkey(self, dialog: tk.Toplevel, hotkey_type: str) -> None:
        self.status_label.config(text=f"Press any key for {hotkey_type}...")
        dialog.update_idletasks()
        
        q = Queue()
        listener = KeyListener(q)
        listener.start()
        listener.join(timeout=30)
        
        try:
            key = q.get_nowait()
            key_str = self.get_key_string(key)
            
            if key_str:
                if hotkey_type == 'record':
                    self.record_hotkey = key_str
                    self.record_btn.config(text=f"{key_str.upper()} (Click to set)")
                else:
                    self.play_hotkey = key_str
                    self.play_btn.config(text=f"{key_str.upper()} (Click to set)")
                self.status_label.config(text="Key set successfully!")
            else:
                self.status_label.config(text="Invalid key, try again")
        except Exception as e:
            self.status_label.config(text=f"Error: {str(e)}")
            logging.error(f"Hotkey setting error: {e}")

    def get_key_string(self, key: Any) -> Optional[str]:
        try:
            if isinstance(key, keyboard.Key):
                return key.name.lower()
            elif isinstance(key, keyboard.KeyCode):
                return key.char.lower() if key.char else f'<{key.vk}>'
            return None
        except AttributeError:
            return None

    def save_new_hotkeys(self, dialog: tk.Toplevel) -> None:
        if self.record_hotkey == self.play_hotkey:
            messagebox.showerror("Error", "Hotkeys must be different")
            return
        
        valid_record, msg_r = self.validate_hotkey(self.record_hotkey)
        valid_play, msg_p = self.validate_hotkey(self.play_hotkey)
        
        if not valid_record:
            messagebox.showerror("Error", f"Invalid Record Hotkey: {msg_r}")
            return
        if not valid_play:
            messagebox.showerror("Error", f"Invalid Play Hotkey: {msg_p}")
            return
        
        self.save_config()
        self.update_hotkey_buttons()
        dialog.destroy()

    def update_hotkey_buttons(self) -> None:
        self.record_button.config(text=f"Recording ({self.record_hotkey.upper()})" if self.recording 
                                 else f"Record ({self.record_hotkey.upper()})")
        self.play_button.config(text=f"Playing ({self.play_hotkey.upper()})" if self.playing 
                               else f"Play/Pause ({self.play_hotkey.upper()})")

    def apply_light_theme(self) -> None:
        self.theme = 'light'
        self.bg_color = '#f0f0f0'
        self.fg_color = '#000000'
        self.entry_bg = '#ffffff'
        self.entry_fg = '#000000'
        self.menu_bg = '#f0f0f0'
        self.menu_fg = '#000000'
        self.link_color = 'blue'
        self.record_button_color = '#ff4d4d'
        self.play_button_color = '#32cd32'
        self.active_button_color = '#ff8000'
        self.update_button_color = '#0078d7'
        self.update_styles()

    def apply_dark_theme(self) -> None:
        self.theme = 'dark'
        self.bg_color = '#2e2e2e'
        self.fg_color = '#ffffff'
        self.entry_bg = '#3e3e3e'
        self.entry_fg = '#ffffff'
        self.menu_bg = '#2e2e2e'
        self.menu_fg = '#ffffff'
        self.link_color = 'cyan'
        self.record_button_color = '#ff4d4d'
        self.play_button_color = '#32cd32'
        self.active_button_color = '#ff8000'
        self.update_button_color = '#1a73e8'
        self.update_styles()

    def update_styles(self) -> None:
        self.menubar.configure(bg=self.menu_bg, fg=self.menu_fg)
        self.file_menu.configure(bg=self.menu_bg, fg=self.menu_fg)
        self.settings_menu.configure(bg=self.menu_bg, fg=self.menu_fg)
        self.theme_menu.configure(bg=self.menu_bg, fg=self.menu_fg)
        self.help_menu.configure(bg=self.menu_bg, fg=self.menu_fg)

        if self.is_windows:
            self.style.theme_use('clam')
            self.style.configure('.', background=self.bg_color, foreground=self.fg_color)
            
            self.style.configure('Record.TButton', background=self.record_button_color, foreground='white')
            self.style.configure('Active.Record.TButton', background=self.active_button_color, foreground='white')
            self.style.configure('Play.TButton', background=self.play_button_color, foreground='white')
            self.style.configure('Active.Play.TButton', background=self.active_button_color, foreground='white')
            self.style.configure('Update.TButton', background=self.update_button_color, foreground='white')
            
            self.style.map('Record.TButton', background=[('active', self.record_button_color)], foreground=[('active', 'white')])
            self.style.map('Active.Record.TButton', background=[('active', self.active_button_color)], foreground=[('active', 'white')])
            self.style.map('Play.TButton', background=[('active', self.play_button_color)], foreground=[('active', 'white')])
            self.style.map('Active.Play.TButton', background=[('active', self.active_button_color)], foreground=[('active', 'white')])
            self.style.map('Update.TButton', background=[('active', self.update_button_color)], foreground=[('active', 'white')])
        else:
            self.style.configure('TFrame', background=self.bg_color)
            self.style.configure('TLabel', background=self.bg_color, foreground=self.fg_color)
            self.style.configure('TEntry', fieldbackground=self.entry_bg, foreground=self.entry_fg)
            self.style.configure('TCheckbutton', background=self.bg_color, foreground=self.fg_color)
            self.style.map('TCheckbutton', background=[('active', self.bg_color)], foreground=[('active', self.fg_color)])
            
            self.style.configure('Record.TButton', background=self.record_button_color, foreground='#ffffff')
            self.style.configure('Active.Record.TButton', background=self.active_button_color, foreground='#ffffff')
            self.style.map('Record.TButton', background=[('active', self.record_button_color), ('disabled', '#cccccc')],
                          foreground=[('active', '#ffffff'), ('disabled', '#666666')])
            self.style.map('Active.Record.TButton', background=[('active', self.active_button_color)],
                          foreground=[('active', '#ffffff')])
            
            self.style.configure('Play.TButton', background=self.play_button_color, foreground='#ffffff')
            self.style.configure('Active.Play.TButton', background=self.active_button_color, foreground='#ffffff')
            self.style.map('Play.TButton', background=[('active', self.play_button_color), ('disabled', '#cccccc')],
                          foreground=[('active', '#ffffff'), ('disabled', '#666666')])
            self.style.map('Active.Play.TButton', background=[('active', self.active_button_color)],
                          foreground=[('active', '#ffffff')])
            
            self.style.configure('Update.TButton', background=self.update_button_color, foreground='#ffffff')
            self.style.map('Update.TButton', background=[('active', self.update_button_color)],
                          foreground=[('active', '#ffffff')])

        self.root.configure(background=self.bg_color)
        
        if hasattr(self, 'about_window') and self.about_window.winfo_exists():
            self.update_about_window_styles()
        if hasattr(self, 'donation_window') and self.donation_window.winfo_exists():
            self.update_donation_window_styles()

    def toggle_recording(self) -> None:
        if self.playing:
            messagebox.showwarning("Warning", "Cannot record during playback")
            return
        self.recording = not self.recording
        if self.recording:
            self.play_button.config(state='disabled')
            self.record_button.config(style='Active.Record.TButton')
            self.events = []
            self.last_time = time()
            if self.is_windows:
                self.setup_listeners()
            logging.info("Recording started")
        else:
            self.play_button.config(state='normal')
            self.record_button.config(style='Record.TButton')
            logging.info(f"Recording stopped. Recorded {len(self.events)} events: {self.events}")
        self.update_hotkey_buttons()

    def toggle_playing(self) -> None:
        if self.recording:
            messagebox.showwarning("Warning", "Cannot play during recording")
            return
        if not self.playing:
            if not self.events:
                messagebox.showwarning("No Events", "No recorded events to play.")
                logging.warning("Attempted playback with no events")
                return
            self.record_button.config(state='disabled')
            self.play_button.config(style='Active.Play.TButton')
            self.playing = True
            logging.info(f"Starting playback with {len(self.events)} events: {self.events}")
            threading.Thread(target=self.play_events, daemon=True).start()
        else:
            self.record_button.config(state='normal')
            self.play_button.config(style='Play.TButton')
            self.playing = False
            logging.info("Playback paused")
        self.update_hotkey_buttons()

    def toggle_loop_infinite(self) -> None:
        self.loop_infinite = self.loop_infinite_var.get()
        self.loop_entry.config(state='disabled' if self.loop_infinite else 'normal')

    def on_press(self, key: Any) -> None:
        try:
            current_key = self.get_key_string(key)
            if not current_key:
                return

            is_hotkey = False
            if current_key == self.record_hotkey:
                self.toggle_recording()
                is_hotkey = True
            elif current_key == self.play_hotkey:
                self.toggle_playing()
                is_hotkey = True

            if self.recording and not is_hotkey:
                current_time = time()
                if self.last_time == 0.0:
                    self.last_time = current_time
                delay = current_time - self.last_time
                self.events.append(("key_press", key, delay))
                self.last_time = current_time
                logging.debug(f"Recorded key press: {key}, delay: {delay}, total events: {len(self.events)}")
        except Exception as e:
            logging.error(f"Key handling error: {e}")

    def on_click(self, x: int, y: int, button: mouse.Button, pressed: bool) -> None:
        if self.recording:
            try:
                current_time = time()
                if self.last_time == 0.0:
                    self.last_time = current_time
                delay = current_time - self.last_time
                self.events.append(("click", x, y, button, pressed, delay))
                self.last_time = current_time
                logging.debug(f"Recorded click: {button} {'press' if pressed else 'release'} at ({x}, {y}), delay: {delay}, total events: {len(self.events)}")
            except Exception as e:
                logging.error(f"Click handling error: {e}")

    def on_move(self, x: int, y: int) -> None:
        if self.recording:
            try:
                current_time = time()
                if self.last_time == 0.0:
                    self.last_time = current_time
                delay = current_time - self.last_time
                self.events.append(("move", x, y, delay))
                self.last_time = current_time
                logging.debug(f"Recorded move to ({x}, {y}), delay: {delay}, total events: {len(self.events)}")
            except Exception as e:
                logging.error(f"Move handling error: {e}")

    def save_script(self) -> None:
        file_path = filedialog.asksaveasfilename(defaultextension=".pkl",
                                                 filetypes=[("Macro Script Files", "*.pkl")])
        if file_path:
            try:
                with open(file_path, "wb") as f:
                    pickle.dump(self.events, f)
                messagebox.showinfo("Success", "Script saved successfully!")
                logging.info(f"Script saved to {file_path} with {len(self.events)} events")
            except (IOError, pickle.PickleError) as e:
                messagebox.showerror("Error", f"Failed to save script:\n{e}")
                logging.error(f"Failed to save script: {e}")

    def load_script(self) -> None:
        file_path = filedialog.askopenfilename(filetypes=[("Macro Script Files", "*.pkl")])
        if file_path:
            try:
                with open(file_path, "rb") as f:
                    self.events = pickle.load(f)
                messagebox.showinfo("Success", "Script loaded successfully!")
                logging.info(f"Script loaded from {file_path} with {len(self.events)} events")
            except (IOError, pickle.UnpicklingError) as e:
                messagebox.showerror("Error", f"Failed to load script:\n{e}")
                logging.error(f"Failed to load script: {e}")

    def play_events(self) -> None:
        if not self.events:
            messagebox.showwarning("No Events", "No recorded events to play.")
            self.playing = False
            self.root.after(0, self.update_hotkey_buttons)
            return

        try:
            speed_factor = float(self.speed_var.get())
            if speed_factor <= 0:
                raise ValueError("Speed factor must be positive")
        except ValueError:
            messagebox.showerror("Invalid Speed", "Please enter a valid positive number for speed multiplier.")
            self.playing = False
            self.root.after(0, self.update_hotkey_buttons)
            return

        try:
            loop_count = float('inf') if self.loop_infinite else int(self.loop_entry.get())
            if loop_count <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid positive integer for loop count.")
            self.loop_entry.delete(0, tk.END)
            self.loop_entry.insert(0, "1")
            loop_count = 1
            self.playing = False
            self.root.after(0, self.update_hotkey_buttons)
            return

        count = 0
        mouse_controller = mouse.Controller()
        keyboard_controller = keyboard.Controller()
        try:
            while self.playing and (self.loop_infinite or count < loop_count):
                for event in self.events:
                    if not self.playing:
                        break
                    adjusted_delay = event[-1] / speed_factor
                    sleep(adjusted_delay)
                    
                    if event[0] == "click":
                        x, y, button, pressed = event[1], event[2], event[3], event[4]
                        mouse_controller.position = (x, y)
                        if pressed:
                            mouse_controller.press(button)
                        else:
                            mouse_controller.release(button)
                    elif event[0] == "move":
                        x, y = event[1], event[2]
                        mouse_controller.position = (x, y)
                    elif event[0] == "key_press":
                        key = event[1]
                        keyboard_controller.press(key)
                        keyboard_controller.release(key)
                if not self.loop_infinite:
                    count += 1
        except Exception as e:
            logging.error(f"Playback error: {e}")
            messagebox.showerror("Playback Error", f"An error occurred: {e}")
        finally:
            self.playing = False
            self.root.after(0, lambda: [
                self.play_button.config(style='Play.TButton'),
                self.record_button.config(state='normal'),
                self.update_hotkey_buttons()
            ])

    def check_for_updates(self) -> None:
        version_url = f"https://raw.githubusercontent.com/V4mpw0L/MacroRecorder/main/version.txt?nocache={random.randint(1,100000)}"
        try:
            response = requests.get(version_url, timeout=5)
            response.raise_for_status()
            online_version = response.text.strip()
            if online_version != __version__:
                update = messagebox.askyesno("Update Available",
                                             f"A new version ({online_version}) is available.\nWould you like to update?")
                if update:
                    self.perform_update()
            else:
                messagebox.showinfo("No Update", "You are using the latest version.")
        except requests.RequestException as e:
            messagebox.showerror("Error", f"Unable to check for updates: {e}")
            logging.error(f"Error checking for updates: {e}")

    def perform_update(self) -> None:
        script_url = f"https://raw.githubusercontent.com/V4mpw0L/MacroRecorder/main/autoclicker.py?nocache={random.randint(1,100000)}"
        try:
            response = requests.get(script_url, timeout=10)
            response.raise_for_status()
            remote_script = response.content
            script_path = os.path.abspath(__file__)
            if os.access(script_path, os.W_OK):
                with open(script_path, 'wb') as f:
                    f.write(remote_script)
                messagebox.showinfo("Update Successful", "The application has been updated. Please restart.")
                logging.info("Application updated successfully")
                sys.exit(0)
            else:
                messagebox.showerror("Error", "No write permission to update the script file.")
                logging.error("No write permission to update script")
        except requests.RequestException as e:
            messagebox.showerror("Error", f"Failed to download update: {e}")
            logging.error(f"Failed to download update: {e}")
        except IOError as e:
            messagebox.showerror("Error", f"Failed to write update: {e}")
            logging.error(f"Error during update write: {e}")

    def show_about(self) -> None:
        self.about_window = tk.Toplevel(self.root)
        self.about_window.title("About")
        self.about_window.resizable(False, False)
        self.about_window.geometry("200x150")
        self.about_window.attributes('-topmost', True)
        self.about_window.configure(background=self.bg_color)

        x = self.root.winfo_x() + (self.root.winfo_width() - 400) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - 200) // 2
        self.about_window.geometry(f"+{x}+{y}")

        ttk.Label(self.about_window, text=f"Macro Recorder v{__version__}", font=('Helvetica', 12, 'bold'), 
                 background=self.bg_color, foreground=self.fg_color).pack(pady=10)
        ttk.Label(self.about_window, text="Created by V4mpw0L", 
                 background=self.bg_color, foreground=self.fg_color).pack(pady=5)

        link = tk.Label(self.about_window, text="GitHub Repository", fg=self.link_color, 
                       cursor="hand2", background=self.bg_color)
        link.pack(pady=5)
        link.bind("<Button-1>", lambda e: webbrowser.open("https://github.com/V4mpw0L/MacroRecorder"))

        ttk.Button(self.about_window, text="Close", command=self.about_window.destroy).pack(pady=10)

    def show_donation(self) -> None:
        self.donation_window = tk.Toplevel(self.root)
        self.donation_window.title("Donation")
        self.donation_window.resizable(False, False)
        self.donation_window.geometry("400x150")
        self.donation_window.attributes('-topmost', True)
        self.donation_window.configure(background=self.bg_color)

        x = self.root.winfo_x() + (self.root.winfo_width() - 400) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - 150) // 2
        self.donation_window.geometry(f"+{x}+{y}")

        ttk.Label(self.donation_window, text="Support the Project", font=('Helvetica', 12, 'bold'),
                 background=self.bg_color, foreground=self.fg_color).pack(pady=10)

        btc_address = "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"
        btc_text = f"₿ Bitcoin: {btc_address}"

        btc_label = tk.Label(self.donation_window, text=btc_text, fg=self.link_color,
                            cursor="hand2", background=self.bg_color)
        btc_label.pack(pady=5)
        btc_label.bind("<Button-1>", lambda e: self.copy_to_clipboard(btc_address))

        ttk.Label(self.donation_window, text="Click to copy address", background=self.bg_color,
                 foreground=self.fg_color).pack(pady=5)

        ttk.Button(self.donation_window, text="Close", command=self.donation_window.destroy).pack(pady=10)

    def copy_to_clipboard(self, text: str) -> None:
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self.root.update()
        messagebox.showinfo("Copied", "Bitcoin address copied to clipboard!")

    def setup_listeners(self) -> None:
        try:
            if self.mouse_listener and self.mouse_listener.running:
                self.mouse_listener.stop()
            if self.keyboard_listener and self.keyboard_listener.running:
                self.keyboard_listener.stop()

            self.mouse_listener = mouse.Listener(
                on_click=self.on_click,
                on_move=self.on_move
            )
            self.keyboard_listener = keyboard.Listener(
                on_press=self.on_press
            )

            self.mouse_listener.start()
            self.keyboard_listener.start()
            logging.info(f"Listeners started. Mouse running: {self.mouse_listener.running}, Keyboard running: {self.keyboard_listener.running}")
            if self.is_windows and not (self.mouse_listener.running and self.keyboard_listener.running):
                logging.warning("Listeners may require admin privileges on Windows.")
                messagebox.showwarning("Permission Issue", "Listeners may not work without admin privileges.\nRun as administrator via Command Prompt.")
        except Exception as e:
            logging.error(f"Failed to start listeners: {e}")
            messagebox.showerror("Listener Error", f"Failed to start listeners: {e}\nTry running with Python 3.12 or as administrator.")
            self.root.destroy()
            sys.exit(1)

    def on_close(self) -> None:
        try:
            if self.mouse_listener and self.mouse_listener.running:
                self.mouse_listener.stop()
            if self.keyboard_listener and self.keyboard_listener.running:
                self.keyboard_listener.stop()
        except Exception as e:
            logging.error(f"Error stopping listeners: {e}")
        finally:
            self.root.destroy()

if __name__ == "__main__":
    try:
        import requests
    except ImportError:
        install = messagebox.askyesno("Missing Package",
                                      "The 'requests' package is missing.\nWould you like to install it now?")
        if install:
            try:
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'requests'])
                messagebox.showinfo("Package Installed", "The 'requests' package has been installed. Please restart.")
                sys.exit(0)
            except subprocess.CalledProcessError as e:
                messagebox.showerror("Installation Error", f"Failed to install 'requests': {e}")
                sys.exit(1)
        else:
            messagebox.showwarning("Missing Package", "The application requires the 'requests' package.")
            sys.exit(1)

    try:
        root = tk.Tk()
        app = MacroRecorder(root)
        root.mainloop()
    except Exception as e:
        messagebox.showerror("Fatal Error", f"Application failed to start:\n{str(e)}")
        logging.critical(f"Application crash: {str(e)}")
        sys.exit(1)
