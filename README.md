# Macro Recorder for Linux v1.0

A powerful and user-friendly macro recorder for Ubuntu Linux that captures and replays mouse movements and clicks. The application features a graphical user interface (GUI) built with tkinter, allowing you to record, save, load, and play macros with customizable loop counts and themes.

## Features

*   **Record Mouse Movements and Clicks:** Capture your mouse actions in real-time for precise automation.
*   **Accurate Playback Timing:** Replays your actions with the exact timing as recorded for seamless automation.
*   **Adjustable Loop Count:** Set the number of times to repeat the macro or loop infinitely until stopped.
*   **Save and Load Macros:** Save your recorded macros to a file for future use and load them anytime.
*   **Theme Switching:** Choose between a light or dark theme to suit your preference.
*   **Color-Coded Controls:** Intuitive colored buttons for easy recognition:
    *   **Record Button:** Red color indicates recording functionality.
    *   **Play Button:** Green color indicates playback functionality.
    *   **Update Button:** Blue color for checking and applying updates.
*   **Update Checker:** Built-in functionality to check for updates from this GitHub repository.
*   **Keyboard Shortcuts:**
    *   **F6:** Start/Stop Recording
    *   **F5:** Play/Pause Playback
*   **Always on Top:** The application window stays above other windows for easy access.
*   **User-Friendly Interface:** Clean and compact design with minimal empty space for efficient use.

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
    git clone [https://github.com/V4mpw0L/MacroRecorder.git](https://github.com/V4mpw0L/MacroRecorder.git)
    ```
2.  **Navigate to the Project Directory:**
    ```bash
    cd MacroRecorder
    ```
3.  **Install Required Python Packages:**
    ```bash
    pip3 install pynput requests
    ```
    **Note:** If you encounter any issues, ensure that you have pip installed and updated:
    ```bash
    sudo apt-get install python3-pip
    pip3 install --upgrade pip
    ```

## Usage

**Running the Application:**

```bash
python3 autoclicker.py
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

*(Include screenshots of the application in both light and dark themes, showcasing the main interface and features here)*

## Troubleshooting

*   **Permission Errors:** If you encounter permission errors when running or updating the application, you may need to run it with elevated permissions:

    ```bash
    sudo python3 autoclicker.py
    ```

    **Caution:** Running scripts with `sudo` can be a security risk; ensure you trust the source.

*   **Missing Packages:** If prompted about missing packages like `requests` or `pynput`, install them using:

    ```bash
    pip3 install requests pynput
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
