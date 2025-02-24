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
import random
import webbrowser
import logging
import json
from queue import Queue

__version__ = "2.0"

logging.basicConfig(
    filename='macro_recorder.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class KeyListener(threading.Thread):
    def __init__(self, queue):
        super().__init__(daemon=True)
        self.queue = queue
        self.listener = None

    def run(self):
        try:
            with keyboard.Listener(on_press=self.on_press) as self.listener:
                self.listener.join()
        except Exception as e:
            logging.error(f"Key listener error: {e}")

    def on_press(self, key):
        self.queue.put(key)
        return False  # Stop listener after first key press

class MacroRecorder:
    def __init__(self, root):
        self.root = root
        self.root.title("Macro Recorder")
        self.root.geometry("220x250")
        self.root.resizable(False, False)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.attributes('-topmost', True)

        self.recording = False
        self.playing = False
        self.events = []
        self.loop_infinite = False
        self.record_hotkey = 'f6'
        self.play_hotkey = 'f5'

        self.style = ttk.Style()
        self.theme = 'light'

        self.create_widgets()
        self.apply_light_theme()
        self.load_config()
        self.update_hotkey_buttons()

        self.mouse_listener = mouse.Listener(on_click=self.on_click, on_move=self.on_move)
        self.keyboard_listener = keyboard.Listener(on_press=self.on_press)

        try:
            self.mouse_listener.start()
            self.keyboard_listener.start()
        except Exception as e:
            messagebox.showerror("Initialization Error", f"Failed to start listeners: {e}")
            self.root.destroy()

    def create_widgets(self):
        # Menu Bar
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
        self.menubar.add_cascade(label="Help", menu=self.help_menu)
        
        self.root.config(menu=self.menubar)

        # Main Frame
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(pady=5)

        button_width = 15

        # Record Button
        self.record_button = ttk.Button(
            self.main_frame, text="Record (F6)", command=self.toggle_recording,
            width=button_width, style='Record.TButton'
        )
        self.record_button.pack(pady=3)

        # Play Button
        self.play_button = ttk.Button(
            self.main_frame, text="Play/Pause (F5)", command=self.toggle_playing,
            width=button_width, style='Play.TButton'
        )
        self.play_button.pack(pady=3)

        # Controls Frame
        self.controls_frame = ttk.Frame(self.root)
        self.controls_frame.pack(pady=5)

        self.controls_frame.columnconfigure(0, weight=1)
        self.controls_frame.columnconfigure(1, weight=1)

        # Loop controls
        self.loop_label = ttk.Label(self.controls_frame, text="Loop Count:")
        self.loop_label.grid(row=0, column=0, padx=3, pady=3, sticky=tk.W)
        self.loop_entry = ttk.Entry(self.controls_frame, width=6, justify='center')
        self.loop_entry.insert(0, "1")
        self.loop_entry.grid(row=0, column=1, padx=3, pady=3, sticky=tk.E)

        # Infinite Loop Checkbox
        self.loop_infinite_var = tk.BooleanVar()
        self.loop_infinite_check = ttk.Checkbutton(
            self.controls_frame, text="Infinite Loop",
            variable=self.loop_infinite_var, command=self.toggle_loop_infinite
        )
        self.loop_infinite_check.grid(row=1, column=0, columnspan=2, padx=3, pady=3, sticky=tk.E)

        # Speed controls
        self.speed_label = ttk.Label(self.controls_frame, text="Speed Multiplier:")
        self.speed_label.grid(row=2, column=0, padx=3, pady=3, sticky=tk.W)
        self.speed_var = tk.StringVar()
        self.speed_var.set("1.0")
        self.speed_entry = ttk.Entry(self.controls_frame, textvariable=self.speed_var, 
                           width=6, justify='center')
        self.speed_entry.grid(row=2, column=1, padx=3, pady=3, sticky=tk.E)

        # Update Button
        self.update_button = ttk.Button(
            self.root, text="Check for Updates", command=self.check_for_updates,
            width=button_width, style='Update.TButton'
        )
        self.update_button.pack(pady=5)

    def load_config(self):
        config_path = os.path.expanduser("~/.macro_recorder_config.json")
        default_config = {'record_hotkey': 'f6', 'play_hotkey': 'f5'}
        
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    self.record_hotkey = config.get('record_hotkey', 'f6')
                    self.play_hotkey = config.get('play_hotkey', 'f5')
            else:
                self.record_hotkey = default_config['record_hotkey']
                self.play_hotkey = default_config['play_hotkey']
                self.save_config()
        except Exception as e:
            messagebox.showerror("Config Error", f"Failed to load config: {e}")
            self.record_hotkey = default_config['record_hotkey']
            self.play_hotkey = default_config['play_hotkey']

    def save_config(self):
        config = {'record_hotkey': self.record_hotkey, 'play_hotkey': self.play_hotkey}
        config_path = os.path.expanduser("~/.macro_recorder_config.json")
        
        try:
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            messagebox.showerror("Config Error", f"Failed to save config: {e}")

    def validate_hotkey(self, input_str):
        input_str = input_str.strip()
        if not input_str:
            return False, "Hotkey cannot be empty"
        
        input_lower = input_str.lower()
        if len(input_lower) == 1 and input_lower.isalpha():
            return True, ""
        elif hasattr(keyboard.Key, input_lower):
            return True, ""
        else:
            return False, f"Invalid key: {input_str}"

    def change_hotkeys(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Change Hotkeys")
        dialog.resizable(False, False)
        dialog.attributes('-topmost', True)
        
        # Record Hotkey
        self.record_btn = ttk.Button(dialog, text=f"Record: {self.record_hotkey.upper()}\n(Click to set)",
                                    command=lambda: self.set_hotkey(dialog, 'record'))
        self.record_btn.grid(row=0, column=0, padx=10, pady=5)
        
        # Play Hotkey
        self.play_btn = ttk.Button(dialog, text=f"Play: {self.play_hotkey.upper()}\n(Click to set)",
                                  command=lambda: self.set_hotkey(dialog, 'play'))
        self.play_btn.grid(row=1, column=0, padx=10, pady=5)
        
        # Status Label
        self.status_label = ttk.Label(dialog, text="")
        self.status_label.grid(row=2, column=0, pady=5)
        
        # Save Button
        ttk.Button(dialog, text="Save", command=lambda: self.save_new_hotkeys(dialog)
                  ).grid(row=3, column=0, pady=5)

    def set_hotkey(self, dialog, hotkey_type):
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
                    self.record_btn.config(text=f"Record: {key_str.upper()}\n(Click to set)")
                else:
                    self.play_hotkey = key_str
                    self.play_btn.config(text=f"Play: {key_str.upper()}\n(Click to set)")
                self.status_label.config(text="Key set successfully!")
            else:
                self.status_label.config(text="Invalid key, try again")
        except Exception as e:
            self.status_label.config(text=f"Error: {str(e)}")
            logging.error(f"Hotkey setting error: {e}")

    def get_key_string(self, key):
        try:
            if isinstance(key, keyboard.Key):
                return key.name.lower()
            elif isinstance(key, keyboard.KeyCode):
                if key.char is not None:
                    return key.char.lower()
                return f'<{key.vk}>'
        except AttributeError:
            return None

    def save_new_hotkeys(self, dialog):
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

    def update_hotkey_buttons(self):
        self.record_button.config(text=f"Record ({self.record_hotkey.upper()})")
        self.play_button.config(text=f"Play/Pause ({self.play_hotkey.upper()})")

    def apply_light_theme(self):
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
        self.update_button_color = '#0078d7'
        self.update_styles()

    def apply_dark_theme(self):
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
        self.update_button_color = '#1a73e8'
        self.update_styles()

    def update_styles(self):
        self.root.configure(background=self.bg_color)
        self.style.configure('TFrame', background=self.bg_color)
        self.style.configure('TLabel', background=self.bg_color, foreground=self.fg_color)
        self.style.configure('TEntry', fieldbackground=self.entry_bg, foreground=self.entry_fg)
        self.style.configure('TCheckbutton', background=self.bg_color, foreground=self.fg_color)
        self.style.map('TCheckbutton', 
                      background=[('active', self.bg_color)], 
                      foreground=[('active', self.fg_color)])
        
        self.style.configure('Record.TButton', background=self.record_button_color, foreground='#ffffff')
        self.style.map('Record.TButton', 
                      background=[('active', self.record_button_color), ('disabled', '#cccccc')],
                      foreground=[('active', '#ffffff'), ('disabled', '#666666')])
        
        self.style.configure('Play.TButton', background=self.play_button_color, foreground='#ffffff')
        self.style.map('Play.TButton',
                      background=[('active', self.play_button_color), ('disabled', '#cccccc')],
                      foreground=[('active', '#ffffff'), ('disabled', '#666666')])
        
        self.style.configure('Update.TButton', background=self.update_button_color, foreground='#ffffff')
        self.style.map('Update.TButton', 
                      background=[('active', self.update_button_color)],
                      foreground=[('active', '#ffffff')])

        self.style.configure('Active.Record.TButton', background='#FFA500', foreground='#ffffff')
        self.style.map('Active.Record.TButton',
                      background=[('active', '#FFA500')],
                      foreground=[('active', '#ffffff')])

        self.style.configure('Active.Play.TButton', background='#FFA500', foreground='#ffffff')
        self.style.map('Active.Play.TButton',
                      background=[('active', '#FFA500')],
                      foreground=[('active', '#ffffff')])

        self.menubar.configure(background=self.menu_bg, foreground=self.menu_fg)
        self.file_menu.configure(background=self.menu_bg, foreground=self.menu_fg)
        self.settings_menu.configure(background=self.menu_bg, foreground=self.menu_fg)
        self.theme_menu.configure(background=self.menu_bg, foreground=self.menu_fg)
        self.help_menu.configure(background=self.menu_bg, foreground=self.menu_fg)

        for frame in [self.main_frame, self.controls_frame]:
            frame.configure(style='TFrame')

        if hasattr(self, 'about_window') and self.about_window.winfo_exists():
            self.about_window.configure(background=self.bg_color)
            for widget in self.about_window.winfo_children():
                if isinstance(widget, ttk.Label):
                    widget.configure(background=self.bg_color, foreground=self.fg_color)
                elif isinstance(widget, ttk.Button):
                    widget.configure(style='TButton')
                elif isinstance(widget, tk.Label):
                    widget.configure(background=self.bg_color, foreground=self.link_color)

    def toggle_recording(self):
        if self.playing:
            messagebox.showwarning("Warning", "Cannot record during playback")
            return
        self.recording = not self.recording
        if self.recording:
            self.play_button.config(state='disabled')
            self.record_button.config(style='Active.Record.TButton')
            self.events = []
            self.start_time = time()
            self.last_time = self.start_time
            logging.info("Recording started")
        else:
            self.play_button.config(state='normal')
            self.record_button.config(style='Record.TButton')
            logging.info("Recording stopped")
        self.update_hotkey_buttons()

    def toggle_playing(self):
        if self.recording:
            messagebox.showwarning("Warning", "Cannot play during recording")
            return
        if not self.playing:
            if not self.events:
                messagebox.showwarning("No Events", "No recorded events to play.")
                return
            self.record_button.config(state='disabled')
            self.play_button.config(style='Active.Play.TButton')
            self.playing = True
            threading.Thread(target=self.play_events, daemon=True).start()
            logging.info("Playback started")
        else:
            self.record_button.config(state='normal')
            self.play_button.config(style='Play.TButton')
            self.playing = False
            logging.info("Playback paused")
        self.update_hotkey_buttons()

    def toggle_loop_infinite(self):
        self.loop_infinite = self.loop_infinite_var.get()
        self.loop_entry.config(state='disabled' if self.loop_infinite else 'normal')

    def on_press(self, key):
        try:
            current_key = self.get_key_string(key)
            if not current_key:
                return

            is_hotkey = False
            if current_key == self.record_hotkey.lower():
                self.toggle_recording()
                is_hotkey = True
            elif current_key == self.play_hotkey.lower():
                self.toggle_playing()
                is_hotkey = True

            if self.recording and not is_hotkey:
                current_time = time()
                delay = current_time - self.last_time
                self.last_time = current_time
                self.events.append(("key_press", key, delay))
                logging.debug(f"Recorded key press: {key}")

        except Exception as e:
            logging.error(f"Key handling error: {e}")

    def on_click(self, x, y, button, pressed):
        if self.recording:
            current_time = time()
            delay = current_time - self.last_time
            self.last_time = current_time
            self.events.append(("click", x, y, button, pressed, delay))
            logging.debug(f"Recorded click: {button} {'press' if pressed else 'release'} at ({x}, {y})")

    def on_move(self, x, y):
        if self.recording:
            current_time = time()
            delay = current_time - self.last_time
            self.last_time = current_time
            self.events.append(("move", x, y, delay))
            logging.debug(f"Recorded move to ({x}, {y})")

    def save_script(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".pkl",
                                                 filetypes=[("Macro Script Files", "*.pkl")])
        if file_path:
            try:
                with open(file_path, "wb") as f:
                    pickle.dump(self.events, f)
                messagebox.showinfo("Success", "Script saved successfully!")
                logging.info(f"Script saved to {file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save script:\n{e}")
                logging.error(f"Failed to save script: {e}")

    def load_script(self):
        file_path = filedialog.askopenfilename(filetypes=[("Macro Script Files", "*.pkl")])
        if file_path:
            try:
                with open(file_path, "rb") as f:
                    self.events = pickle.load(f)
                messagebox.showinfo("Success", "Script loaded successfully!")
                logging.info(f"Script loaded from {file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load script:\n{e}")
                logging.error(f"Failed to load script: {e}")

    def play_events(self):
        if not self.events:
            messagebox.showwarning("No Events", "No recorded events to play.")
            self.playing = False
            self.play_button.config(text=f"Play/Pause ({self.play_hotkey.upper()})")
            return

        try:
            speed_factor = float(self.speed_var.get())
            if speed_factor <= 0:
                raise ValueError("Speed factor must be positive")
        except ValueError:
            messagebox.showerror("Invalid Speed", "Please enter a valid positive number for speed multiplier.")
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
            logging.error(f"Error checking for updates: {e}")

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
                    logging.info("Application updated successfully")
                    sys.exit()
                else:
                    messagebox.showerror("Error", "No write permission to update the script file. Please run the application with appropriate permissions.")
                    logging.error("No write permission to update script")
            else:
                messagebox.showerror("Error", "Failed to download the update.")
                logging.error("Failed to download update")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred during the update:\n{e}")
            logging.error(f"Error during update: {e}")

    def show_about(self):
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

    def on_close(self):
        try:
            self.mouse_listener.stop()
            self.keyboard_listener.stop()
        except:
            pass
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
                messagebox.showinfo("Package Installed", "The 'requests' package has been installed. Please restart the application.")
            except Exception as e:
                messagebox.showerror("Installation Error", f"An error occurred while installing 'requests':\n{e}")
            sys.exit()
        else:
            messagebox.showwarning("Missing Package", "The application cannot run without the 'requests' package.")
            sys.exit()

    try:
        root = tk.Tk()
        app = MacroRecorder(root)
        root.mainloop()
    except Exception as e:
        messagebox.showerror("Fatal Error", f"Application failed to start:\n{str(e)}")
        logging.critical(f"Application crash: {str(e)}")
