# Macro Recorder for Linux v2.3

A powerful and user-friendly macro recorder for Ubuntu Linux that captures and replays mouse movements and clicks. The application features a graphical user interface (GUI) built with tkinter, allowing you to record, save, load, and play macros with customizable loop counts and themes.

## Features

* **Multi-Input Recording:**
  - Mouse movements and clicks
  - Keyboard input (including special keys)
  - Combined mouse+keyboard actions
* **Smart Playback Control:**
  - Adjustable playback speed (0.1x-10x)
  - Configurable loop counts (1-∞)
  - Real-time playback control
* **Advanced Hotkey Management:**
  - Fully customizable hotkeys
  - Input validation for key selection
  - Dynamic button label updates
* **Cross-Platform Support:**
  - Windows 10/11
  - Ubuntu/Debian Linux
  - Other Linux distributions
* **Enhanced UI Features:**
  - Light/Dark theme support
  - Color-coded status indicators
  - Compact responsive design (220x250px)
* **Security & Maintenance:**
  - Config file encryption
  - Auto-update system
  - Detailed error logging
* **Advanced Functionality:**
  - Precise event timing (ms accuracy)
  - Concurrent operation prevention
  - Configurable through JSON settings
  - Portable script format (.pkl)

## Prerequisites

Ensure you have the following installed on your Ubuntu system:

*   **Python 3:**
    ```bash
    sudo apt-get install python3
    ```
*   **Tkinter:** Python interface to the Tk GUI toolkit for the GUI.
    ```bash
    sudo apt-get install python3-tk
    ```
*   **Pip:** Python package installer for managing Python packages.
    ```bash
    sudo apt-get install python3-pip
    ```
*   **Required Python Packages:**
    *   **pynput:** Library for controlling and monitoring input devices.
        ```bash
        pip3 install pynput
        ```
    *   **requests:** Library for making HTTP requests to check for updates.
        ```bash
        pip3 install requests
        ```

## Installation

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/V4mpw0L/MacroRecorder.git
    ```
2.  **Navigate to the Project Directory:**
    ```bash
    cd MacroRecorder
    ```
    **Note:** If you encounter any issues, ensure that you have pip installed and updated:
    ```bash
    sudo apt-get install python3-pip
    pip3 install --upgrade pip
    ```

## Usage

**Running the Application:**

```bash
python3 macrorecorder.py
```

**Recording Macros:**

1. Click the Record (F6) button or press F6 to start recording.
2. Perform your mouse actions.
3. Click Stop Recording (F6) or press F6 again to stop recording.

**Playing Macros:**

1. Set the Loop Count or check Loop Infinite for continuous playback.
2. Click the Play/Pause (F5) button or press F5 to start playback.
3. Click Pause Playback (F5) or press F5 again to pause playback.

**Saving and Loading Macros:**

*   **Save Script:** Go to File > Save Script to save your macro.
*   **Load Script:** Go to File > Load Script to load a saved macro.

**Switching Themes:**

Go to Theme in the menu bar and select Light Theme or Dark Theme according to your preference.

**Checking for Updates:**

Click the Check for Updates button to see if a new version is available. If an update is available, follow the prompts to update the application.

## Screenshots

*![Image](https://github.com/user-attachments/assets/82308794-daab-467a-9676-a0064154e36f)*

## Troubleshooting

*   **Permission Errors:** If you encounter permission errors when running or updating the application, you may need to run it with elevated permissions:

    ```bash
    sudo python3 macrorecorder.py
    ```

    **Caution:** Running scripts with `sudo` can be a security risk; ensure you trust the source.

*   **Missing Packages:** If prompted about missing packages like `tkinter` `requests` or `pynput`, install them using:

    ```bash
    pip3 install requests pynput tkinter
    ```

*   **Display Issues:** If the GUI elements do not display correctly, ensure that Tkinter is properly installed:

    ```bash
    sudo apt-get install python3-tk
    ```

## Contributing

Contributions are welcome! Please open an issue or submit a pull request with your improvements.

## License

This project is licensed under the MIT License.

## Disclaimer

Use this tool responsibly and ensure compliance with all applicable laws and software terms of service. The author is not liable for any misuse of this application.
