# Audible Garden Turntable Control

A Python-based turntable control system that converts visual input from a camera into MIDI/OSC messages for musical performance. The system features both rectangular and circular ROI modes with real-time visual feedback and interactive controls.

## Features

- **Real-time camera processing** with interactive ROI selection
- **Dual ROI Modes**: Rectangular (traditional) and Circular (radial scanline)
- **Zodiac mode**: 12-section processing for time-based musical composition
- **OSC/MIDI output** for integration with DAWs and music software
- **Interactive visual feedback** with overlay information
- **Configurable parameters**: notes, velocities, durations, processing intervals
- **Execution timeout** and monitoring capabilities
- **Automatic spindle detection** for circular mode

## Prerequisites

- macOS (tested on macOS 24.5.0)
- Conda or Miniconda installed
- Camera device (built-in or external)

## Installation

### 1. Create Conda Environment

Create a new conda environment named 'garden' with Python 3.12:

```bash
conda create -n garden python=3.12.11 -y 
conda activate garden
```

### 2. Install Dependencies

Install the required packages from `requirements.txt`:

```bash
pip install -r requirements.txt
```

### 3. Apply AudioLazy Patch

The project includes a patch for the AudioLazy library to ensure compatibility:

```bash
chmod +x patch_audiolazy.sh
./patch_audiolazy.sh
```

## Usage

### Starting the Application

1. Activate the conda environment:
   ```bash
   conda activate garden
   ```

2. Run the main application:
   ```bash
   python fixed_turntable.py
   ```

### Command Line Options

```bash
python fixed_turntable.py [OPTIONS]

Options:
  -r, --manual_roi      Manual ROI selection (y/n) [default: y]
  -s, --scale           Musical scale (piano/CMajor/CPentatonic/CLydian/CWhole) [default: CPentatonic]
  --rpm                 Turntable rotation speed in RPM [default: 2.5]
  --resolution          Camera resolution (e.g., 1920x1080) [default: 1920x1080]
  --camera              Camera index [default: 0]
  --skip                Frame skip rate (1=every frame) [default: 1]
  --vel_min             Minimum velocity [default: 32]
  --vel_max             Maximum velocity [default: 127]
  --dur_min             Minimum note duration [default: 0.8]
  --dur_max             Maximum note duration [default: 1.8]
  --show_full           Show full camera view (y/n) [default: y]
  --roi_mode            ROI mode (rectangular/circular) [default: rectangular]
  --record_score        Record the first rotation (y/n) [default: y]
  --detect_rpm          Use real-time RPM detection (y/n) [default: n]
```

### Example Commands

```bash
# Start in circular mode with real-time RPM detection (Recommended)
python fixed_turntable.py --roi_mode circular --detect_rpm y

# Start with a fixed RPM and rectangular ROI
python fixed_turntable.py --roi_mode rectangular --rpm 3.0 --manual_roi n

# 고해상도 설정
python fixed_turntable.py --resolution 1920x1080 --roi_mode circular
```

## Interactive Controls

### Keyboard Shortcuts

| Key | Function |
|-----|----------|
| **ESC** | Exit application |
| **'s'** | Change musical scale (piano → CMajor → CPentatonic → CLydian → CWhole) |
| **'f'** | Toggle full camera view ON/OFF |
| **'r'** | Re-select ROI (automatic detection in circular mode) |
| **'m'** | Switch ROI mode (rectangular ↔ circular) |
| **'p'** | Toggle score playback mode ON/OFF |
| **'d'** | Reset reference frame for RPM detection |

### Real-time Information Display

The application shows real-time information overlays:

- **Frame count** and processing FPS
- **RPM** and current rotation angle (shows detected RPM if enabled)
- **ROI coordinates** and mode
- **Zodiac section** (1/12 to 12/12)
- **Center point** and scanline visualization

## ROI Modes

### Rectangular Mode (Traditional)
- **Selection**: Manual rectangle selection or automatic center line
- **Processing**: Vertical scanline from top to bottom
- **Zodiac**: 12 vertical sections that cycle over time
- **Best for**: Linear patterns and traditional turntable simulation

### Circular Mode (New - Recommended)
- **Detection**: Automatic spindle (center pin) detection
- **Processing**: Radial scanline from center to edge
- **Zodiac**: 12 circular sections (30° each) that rotate with the turntable
- **Best for**: Real turntable simulation and radial pattern reading

## Processing Modes

### Full ROI Mode
- Processes the entire selected region of interest
- Continuous analysis of the full area

### Zodiac Mode (12-Section)
- Divides the ROI into 12 sections
- **Rectangular**: Vertical sections (top to bottom)
- **Circular**: Angular sections (0° to 360°)
- Each section represents a "zodiac hour" (time-based composition)
- Cycles through sections over time for time-based composition

## OSC Output and MIDI Mapping

### OSC Communication
- **Port**: 5555 (configurable)
- **Target**: localhost
- **Protocol**: UDP

### MIDI Data Transmission
- **Note Count**: 37 notes (CPentatonic scale) or 88 notes (full piano)
- **Transmission Interval**: Every `--skip` frames (default: every frame)
- **Velocity Range**: 32-127 (configurable)
- **Duration Range**: 0.8-1.8 seconds (configurable)

### OSC Message Format
```
/note: [array of MIDI note numbers]
/velocity: [array of velocity values]
/duration: [array of note durations]
```

### Console Output Example
```
📡 37개 노트 전송 (평균 vel: 94.8)
📊 처리 FPS: 47.9, 프레임: 300
```

### Transmission Timing
- **Processing**: Every frame (or every `--skip` frames)
- **OSC Send**: Only when MIDI notes are generated
- **Console Log**: Every 30 transmissions (to avoid spam)
- **FPS Display**: Every 300 frames (~10 seconds)

## Visual Feedback

### Display Windows
1. **Webcam Full View**: Complete camera feed with overlay information
2. **ROI Detail** (Rectangular): Selected region zoom
3. **Radial Scanline** (Circular): Radial scanline visualization

### Overlay Elements
- **Blue rectangle/line**: Current ROI boundary
- **Red section**: Active Zodiac section
- **Green dot**: Center point
- **Information box**: Real-time parameters
- **Zodiac indicators**: Section numbers and timing

## Score Recording and Playback

### Automatic Recording
- When `--record_score` is enabled, the first full rotation of the turntable is automatically recorded.
- The recorded data is saved in a session-specific folder inside the `images/` directory.

### Saved Files
For each recording session, the following files are generated in `images/{session_name}/`:
- **`score.json`**: Detailed MIDI data (notes, velocities, durations) for each frame.
- **`score.png`**: A panoramic image created by stitching together the ROIs from the entire rotation, visualizing the "unrolled" turntable surface.
- **`score.npy`**: The raw pixel data (as a NumPy array) used to generate the panoramic image.

### Playback
- Press the **'p'** key to toggle playback of the last recorded score.
- The system will loop the first recorded rotation, sending MIDI notes based on the saved data.

## File Structure

```
audible-garden-TH/
├── fixed_turntable.py        # Main application
├── turntable_gui.py          # (Upcoming) GUI version
├── requirements.txt          # Python dependencies
├── patch_audiolazy.sh        # AudioLazy compatibility patch
├── changes.txt               # Record of recent updates
├── images/                   # Directory for saved scores
│   └── {session_name}/       # Folder for each recording
│       ├── score.json
│       ├── score.png
│       └── score.npy
├── utils/
│   ├── audio_utils_simple.py # Simplified audio processing
│   ├── camera_utils.py      # Camera detection and management
│   ├── osc_utils.py         # OSC communication utilities
│   └── rotation_utils.py    # RPM detection utilities
├── AG-TH Project/            # Ableton Live project files
└── README.md                 # This documentation
```

## Performance Specifications

### Camera Support
- **Resolution**: Up to 1920x1080 (tested)
- **FPS**: 22-55 FPS (camera dependent)
- **Backend**: AVFoundation (macOS)

### Processing Performance
- **Typical FPS**: 45-55 FPS
- **Memory Usage**: ~100-200MB
- **CPU Usage**: Moderate (depends on ROI size)

### MIDI/OSC Performance
- **Note Generation**: 37-88 notes per cycle
- **Transmission Rate**: Every frame (or skip rate)
- **Latency**: <50ms (typical)

## Troubleshooting

### Camera Issues
- Ensure camera permissions are granted
- Try different camera backends (AVFoundation is preferred on macOS)
- Check camera availability with different resolutions

### ROI Detection Issues
- **Circular Mode**: Ensure turntable center is visible
- **Rectangular Mode**: Try manual selection if automatic fails
- **Zodiac Mode**: Check if sections are cycling properly

### OSC Connection
- Verify the target application is listening on port 5555
- Check firewall settings
- Use OSC monitoring tools to verify message transmission

### Performance Issues
- Increase `--skip` value for better performance
- Reduce camera resolution
- Use smaller ROI in rectangular mode
- Monitor system resources during execution

### Conda Environment Issues
```bash
# 환경 재생성
conda deactivate
conda env remove -n garden
conda create -n garden python=3.12.11 -y
conda activate garden
pip install -r requirements.txt
```

## Dependencies

Key dependencies include:
- **OpenCV**: Computer vision and camera handling
- **python-osc**: OSC communication
- **numpy**: Numerical processing
- **PyQt5**: GUI framework (for GUI version)
- **audiolazy**: Audio processing (patched)

## Advanced Configuration

### Custom Scales
The system supports various musical scales:
- **piano**: Full 88-note piano range
- **CMajor**: C major scale
- **CPentatonic**: C pentatonic scale (37 notes)
- **CLydian**: C Lydian mode
- **CWhole**: Whole tone scale

### Timing Configuration
- **RPM**: Controls rotation speed and Zodiac timing
- **Frame Skip**: Reduces processing load
- **Zodiac Sections**: Always 12 sections (30° each in circular mode)

## License

This project is part of the Audible Garden series for experimental audio-visual performance.

## Contributing

For issues or contributions, please refer to the project documentation or contact the development team. 