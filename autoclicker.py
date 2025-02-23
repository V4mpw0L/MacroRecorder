#!/usr/bin/env python3

import tkinter as tk
from tkinter import filedialog, messagebox
import pynput.mouse as mouse
import pynput.keyboard as keyboard
from time import time, sleep
import threading
import pickle
import sys
import subprocess
import os
import requests 

class MacroRecorder:
    def __init__(self, root):
        self.current_version = "1.0"  # Update this version as needed

        self.root = root
        self.root.title(f"Macro Recorder v{self.current_version}")  # Display version in title bar
        self.root.geometry("300x200")
        self.root.resizable(False, False)
        self.root.attributes('-topmost', True)

        self.recording = False
        self.playing = False
        self.events = []
        self.loop_infinite = False

        self.create_widgets()

        self.mouse_listener = mouse.Listener(on_click=self.on_click, on_move=self.on_move)
        self.keyboard_listener = keyboard.Listener(on_press=self.on_press)

        self.mouse_listener.start()
        self.keyboard_listener.start()

    def create_widgets(self):
        # Menu Bar
        self.menubar = tk.Menu(self.root)
        self.file_menu = tk.Menu(self.menubar, tearoff=0)
        self.file_menu.add_command(label="Save Script", command=self.save_script)
        self.file_menu.add_command(label="Load Script", command=self.load_script)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Exit", command=self.root.quit)
        self.menubar.add_cascade(label="File", menu=self.file_menu)

        self.help_menu = tk.Menu(self.menubar, tearoff=0)
        self.help_menu.add_command(label="Check for Updates", command=self.check_for_updates)
        self.menubar.add_cascade(label="Help", menu=self.help_menu)

        self.root.config(menu=self.menubar)

        # Main Frame
        main_frame = tk.Frame(self.root)
        main_frame.pack(pady=5)

        # Record Button
        self.record_button = tk.Button(main_frame, text="Record (F6)", command=self.toggle_recording,
                                       bg='red', fg='white', font=('Helvetica', 10, 'bold'), width=15, height=2)
        self.record_button.grid(row=0, column=0, padx=5, pady=5)

        # Play Button
        self.play_button = tk.Button(main_frame, text="Play/Pause (F5)", command=self.toggle_playing,
                                     bg='green', fg='white', font=('Helvetica', 10, 'bold'), width=15, height=2)
        self.play_button.grid(row=0, column=1, padx=5, pady=5)

        # Controls Frame
        controls_frame = tk.Frame(self.root)
        controls_frame.pack(pady=5)

        self.loop_label = tk.Label(controls_frame, text="Loop Count:")
        self.loop_label.grid(row=0, column=0, padx=5)
        self.loop_entry = tk.Entry(controls_frame, width=5)
        self.loop_entry.insert(0, "1")  # Default value
        self.loop_entry.grid(row=0, column=1, padx=5)

        self.loop_infinite_var = tk.BooleanVar()
        self.loop_infinite_check = tk.Checkbutton(controls_frame, text="Loop Infinite",
                                                  variable=self.loop_infinite_var, command=self.toggle_loop_infinite)
        self.loop_infinite_check.grid(row=0, column=2, padx=5)

        # Update Button
        self.update_button = tk.Button(self.root, text="Check for Updates", command=self.check_for_updates,
                                       font=('Helvetica', 9))
        self.update_button.pack(pady=5)

    def toggle_recording(self):
        self.recording = not self.recording
        if self.recording:
            self.events = []
            self.start_time = time()  # Start time of recording
            self.last_time = self.start_time  # Time of the last event
            self.record_button.config(text="Stop Recording (F6)", bg='orange', width=20)
        else:
            self.record_button.config(text="Record (F6)", bg='red', width=15)

    def toggle_playing(self):
        if not self.playing:
            if not self.events:
                messagebox.showwarning("No Events", "No recorded events to play.")
                return
            self.playing = True
            self.play_button.config(text="Pause Playback (F5)", bg='orange', width=20)
            threading.Thread(target=self.play_events).start()
        else:
            self.playing = False
            self.play_button.config(text="Play/Pause (F5)", bg='green', width=15)

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
            delay = current_time - self.last_time  # Time since the last event
            self.last_time = current_time
            self.events.append(("click", x, y, button, pressed, delay))

    def on_move(self, x, y):
        if self.recording:
            current_time = time()
            delay = current_time - self.last_time  # Time since the last event
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
            self.play_button.config(text="Play/Pause (F5)", bg='green', width=15)
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
        self.play_button.config(text="Play/Pause (F5)", bg='green', width=15)

    def check_for_updates(self):
        version_url = "https://raw.githubusercontent.com/V4mpw0L/MacroRecorder/main/version.txt"
        try:
            response = requests.get(version_url, timeout=5)
            if response.status_code == 200:
                online_version = response.text.strip()
                if online_version != self.current_version:
                    update = messagebox.askyesno("Update Available",
                                                 f"A new version ({online_version}) is available.\n"
                                                 f"Would you like to update?")
                    if update:
                        self.perform_update()
                else:
                    messagebox.showinfo("No Update", "You are using the latest version.")
            else:
                messagebox.showerror("Error", "Unable to check for updates.")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while checking for updates:\n{e}")

    def perform_update(self):
        script_url = "https://raw.githubusercontent.com/V4mpw0L/MacroRecorder/main/autoclicker.py"
        try:
            response = requests.get(script_url, timeout=10)
            if response.status_code == 200:
                script_path = os.path.realpath(__file__)
                with open(script_path, 'wb') as f:
                    f.write(response.content)
                messagebox.showinfo("Update Successful", "The application has been updated. Please restart.")
                sys.exit()
            else:
                messagebox.showerror("Error", "Failed to download the update.")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred during the update:\n{e}")

if __name__ == "__main__":
    # Check for required packages
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
