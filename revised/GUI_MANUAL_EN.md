# Audible Garden Turntable GUI User Manual

This document explains how to install and run the Audible Garden Turntable GUI application, and how to use each of its features.

---

## 1. Table of Contents

- [2. Installation and Execution](#2-installation-and-execution)
- [3. Screen Layout](#3-screen-layout)
- [4. Control Panel Details](#4-control-panel-details)
  - [4.1. Execution Control](#41-execution-control)
  - [4.2. RPM Settings](#42-rpm-settings)
  - [4.3. Mode Settings](#43-mode-settings)
  - [4.4. Score Control](#44-score-control)
- [5. Basic Usage Scenarios](#5-basic-usage-scenarios)
  - [Scenario 1: Real-time Performance (with Score Recording)](#scenario-1-real-time-performance-with-score-recording)
  - [Scenario 2: Loading and Playing a Saved Score](#scenario-2-loading-and-playing-a-saved-score)
- [6. Setting ROI with Mouse (Planned)](#6-setting-roi-with-mouse-planned)

---

## 2. Installation and Execution

1.  **Activate Conda Environment**:
    To run the project, open a terminal and activate the `garden` virtual environment with the command below.
    ```bash
    conda activate garden
    ```

2.  **Run the GUI Application**:
    In the terminal, execute the following command to launch the GUI.
    ```bash
    python turntable_gui.py
    ```

---

## 3. Screen Layout

The GUI is divided into two main parts:

-   **① Video Display (Left)**: Shows the live feed from the webcam. When the logic is running, various information such as the ROI (Region of Interest), scanline, current RPM, and FPS will be drawn as an overlay on the video.
-   **② Control Panel (Right)**: Contains all the buttons, sliders, and combo boxes to control the application's behavior.

![GUI Layout](https://i.imgur.com/example.png) <!-- TODO: Add a real screenshot -->

---

## 4. Control Panel Details

### 4.1. Execution Control

-   **Start Button**: Begins the data processing logic using the current settings from the control panel.
-   **Stop Button**: Halts all running logic. It becomes enabled after the 'Start' button is pressed.

### 4.2. RPM Settings

-   **Fixed RPM Slider**: Sets a virtual rotation speed (RPM) from 1.0 to 10.0. Use this when you don't have a physically rotating object.
-   **Enable Real-time RPM Detection Checkbox**: When checked, the program analyzes feature points in the video to detect the actual rotation speed, ignoring the Fixed RPM slider.

### 4.3. Mode Settings

-   **ROI Mode**:
    -   `Circular`: This is the circular mode. It automatically detects the center (spindle) of the turntable in the video and reads pixel data along a radial scanline from the center outwards. This is suitable for circular objects with a clear center, like an LP record.
    -   `Rectangular`: This is the rectangular mode. It reads pixel data from the entire specified rectangular area.
-   **Scale**: Selects the musical scale to which the scanned pixel brightness values will be converted into MIDI notes (e.g., Pentatonic, full Piano, Major scale).

### 4.4. Score Control

-   **Record First Lap Score Checkbox**: Determines whether to save all processed data (MIDI notes, pixel values, etc.) during the first full rotation after pressing 'Start'. This is enabled by default.
    -   The recorded data is saved in a session folder within the `images/` directory. The folder is named using the format `Timestamp_Mode_Scale_RPM` and contains `score.json`, `score.npy`, and `score.png` files.

-   **Load Saved Score Button**: Opens a file explorer, allowing you to select a previously saved session folder from the `images/` directory to load its score data into the program.
    -   **Important**: Loading a score is only possible when the logic is in the **'Stopped' state**.

-   **Playback Loaded Score Button**: This button becomes active after a score is successfully loaded.
    -   **On Click (Playback Mode)**: The button's text changes to "Playing...", and it begins to loop the loaded score data, ignoring the live camera feed.
    -   **On Second Click (Live Mode)**: The button text reverts, and the application switches back to processing the live camera feed. This allows for easy switching between the loaded score and a live performance.

---

## 5. Basic Usage Scenarios

### Scenario 1: Real-time Performance (with Score Recording)

1.  Run the GUI with `python turntable_gui.py`.
2.  Set your desired `RPM`, `ROI Mode`, and `Scale` in the control panel.
3.  Ensure the `Record First Lap Score` checkbox is checked.
4.  Press the **Start** button.
5.  The performance will begin, either based on the virtual RPM or by rotating an object in front of the camera.
6.  The performance from the first lap will be automatically saved in the `images/` folder.
7.  Press the **Stop** button to end the performance.

### Scenario 2: Loading and Playing a Saved Score

1.  After launching the GUI, ensure it is in the **'Stopped'** state.
2.  Click the **Load Saved Score** button and select the desired session folder.
3.  Once the "Score loaded" message appears, the **Playback Loaded Score** button will be enabled.
4.  Click the **Playback Loaded Score** button to start playback.
    -   You do not need to press the 'Start' button in this case.
5.  If you want to switch back to a live performance during playback, click the active playback button again to return to 'Live Mode', and then press the **Start** button.

---

## 6. Setting ROI with Mouse (Planned)

In a future update, a feature will be added to allow users to set the ROI directly on the video display using the mouse.

-   **Circular Mode**: Click the center point -> Drag to set the radius.
-   **Rectangular Mode**: Click the top-left corner -> Drag to the bottom-right corner. 