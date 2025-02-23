# Macro Recorder for Linux v1.0

A powerful and user-friendly macro recorder for Ubuntu Linux that captures and replays mouse movements and clicks. The application features a graphical user interface (GUI) built with `tkinter`, allowing you to record, save, load, and play macros with customizable loop counts and themes.

## Features

- **Record Mouse Movements and Clicks**: Capture your mouse actions in real-time for precise automation.
- **Accurate Playback Timing**: Replays your actions with the exact timing as recorded for seamless automation.
- **Adjustable Loop Count**: Set the number of times to repeat the macro or loop infinitely until stopped.
- **Save and Load Macros**: Save your recorded macros to a file for future use and load them anytime.
- **Theme Switching**: Choose between a light or dark theme to suit your preference.
- **Color-Coded Controls**: Intuitive colored buttons for easy recognition:
  - **Record Button**: Red color indicates recording functionality.
  - **Play Button**: Green color indicates playback functionality.
  - **Update Button**: Blue color for checking and applying updates.
- **Update Checker**: Built-in functionality to check for updates from this GitHub repository.
- **Keyboard Shortcuts**:
  - **F6**: Start/Stop Recording
  - **F5**: Play/Pause Playback
- **Always on Top**: The application window stays above other windows for easy access.
- **User-Friendly Interface**: Clean and compact design with minimal empty space for efficient use.

## Prerequisites

Ensure you have the following installed on your Ubuntu system:

- **Python 3**
  - Install using:
    ```bash
    sudo apt-get install python3
    ```
- **Tkinter**: Python interface to the Tk GUI toolkit for the GUI.
  - Install using:
    ```bash
    sudo apt-get install python3-tk
    ```
- **Pip**: Python package installer for managing Python packages.
  - Install using:
    ```bash
    sudo apt-get install python3-pip
    ```
- **Required Python Packages**:
  - **pynput**: Library for controlling and monitoring input devices.
    ```bash
    pip3 install pynput
    ```
  - **requests**: Library for making HTTP requests to check for updates.
    ```bash
    pip3 install requests
    ```

## Installation

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/V4mpw0L/MacroRecorder.git
