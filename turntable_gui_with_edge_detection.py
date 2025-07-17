#!/usr/bin/env python3
"""
Enhanced Turntable GUI with Edge Detection Logging

Based on turntable_gui.py but adds edge detection functionality with a dedicated log window
showing real-time edge detection trends on the right side of the webcam feed.
"""

import sys
import time
from datetime import datetime
import cv2
import numpy as np
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTextEdit, QComboBox, QMessageBox,
    QSpinBox, QDoubleSpinBox, QGroupBox, QGridLayout, QCheckBox,
    QSplitter
)
from PyQt5.QtCore import QThread, pyqtSignal, Qt, QTimer, QRect, QPoint
from PyQt5.QtGui import QImage, QPixmap, QPainter, QPen, QColor, QFont
from pythonosc import udp_client

from utils.camera_utils import get_camera_name, get_all_camera_names


class EdgeChangeDetector:
    """Edge detection and change detection class from live_camera_edge_detection.py"""
    def __init__(self, baseline_duration: float = 5.0, threshold: float = 0.15):
        self.baseline_duration = baseline_duration
        self.threshold = threshold
        self.edge_counts = []
        self.baseline_mean_frame = None
        self.baseline_stats = None
        self.baseline_established = False
        
    def add_baseline_frame(self, canny_frame):
        """Add a frame to the baseline collection."""
        edge_count = np.count_nonzero(canny_frame)
        self.edge_counts.append(edge_count)
        
        # Accumulate mean frame efficiently
        if self.baseline_mean_frame is None:
            self.baseline_mean_frame = canny_frame.astype(float)
        else:
            self.baseline_mean_frame += canny_frame.astype(float)
        
    def establish_baseline(self):
        """Create baseline statistics from collected frames."""
        self.baseline_mean_frame /= len(self.edge_counts)
        
        self.baseline_stats = {
            'mean_edge_count': np.mean(self.edge_counts),
            'std_edge_count': np.std(self.edge_counts)
        }
        
        self.baseline_established = True
        baseline_msg = f"BASELINE: {len(self.edge_counts)} frames, {self.baseline_stats['mean_edge_count']:.0f} avg edges"
        return baseline_msg
        
    def detect_change(self, canny_frame):
        """Check if current frame differs significantly from baseline."""
        current_edge_count = np.count_nonzero(canny_frame)
        
        # Statistical comparison
        edge_diff = abs(current_edge_count - self.baseline_stats['mean_edge_count'])
        edge_threshold = max(self.baseline_stats['std_edge_count'] * 3, 
                           self.baseline_stats['mean_edge_count'] * self.threshold)
        
        # Spatial comparison  
        spatial_diff = np.mean(np.abs(canny_frame.astype(float) - self.baseline_mean_frame))
        spatial_threshold = 255.0 * self.threshold
        
        # Determine if change detected
        edge_exceeded = edge_diff > edge_threshold
        spatial_exceeded = spatial_diff > spatial_threshold
        change_detected = edge_exceeded or spatial_exceeded
        
        # Return detection result and metrics
        metrics = {
            'edge_diff': edge_diff,
            'edge_threshold': edge_threshold,
            'edge_exceeded': edge_exceeded,
            'spatial_diff': spatial_diff,
            'spatial_threshold': spatial_threshold,
            'spatial_exceeded': spatial_exceeded
        }
        
        return change_detected, metrics


class ROISelector(QLabel):
    """Interactive ROI selector widget"""
    roi_selected = pyqtSignal(tuple)  # (x, y, w, h)
    log_message = pyqtSignal(str)  # For logging messages
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.selecting = False
        self.start_point = QPoint()
        self.end_point = QPoint()
        self.current_roi = None
        self.setStyleSheet("border: 2px solid #333;")
        
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.selecting = True
            self.start_point = event.pos()
            self.end_point = self.start_point
            self.update()
            
    def mouseMoveEvent(self, event):
        if self.selecting:
            self.end_point = event.pos()
            self.update()
            
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.selecting:
            self.selecting = False
            self.end_point = event.pos()
            
            # Calculate ROI rectangle
            x1, y1 = min(self.start_point.x(), self.end_point.x()), min(self.start_point.y(), self.end_point.y())
            x2, y2 = max(self.start_point.x(), self.end_point.x()), max(self.start_point.y(), self.end_point.y())
            
            # Ensure minimum size
            if x2 - x1 < 10 or y2 - y1 < 10:
                self.log_message.emit("ROI too small, please select a larger area")
                self.update()
                return
                
            self.current_roi = (x1, y1, x2 - x1, y2 - y1)
            self.roi_selected.emit(self.current_roi)
            self.update()
            
    def paintEvent(self, event):
        super().paintEvent(event)
        
        if self.pixmap():
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            
            # Draw existing ROI if any
            if self.current_roi and not self.selecting:
                x, y, w, h = self.current_roi
                painter.setPen(QPen(QColor(0, 255, 0), 2))
                painter.drawRect(x, y, w, h)
                
            # Draw selection rectangle
            if self.selecting:
                x1, y1 = min(self.start_point.x(), self.end_point.x()), min(self.start_point.y(), self.end_point.y())
                x2, y2 = max(self.start_point.x(), self.end_point.x()), max(self.start_point.y(), self.end_point.y())
                
                painter.setPen(QPen(QColor(255, 0, 0), 2, Qt.DashLine))
                painter.drawRect(x1, y1, x2 - x1, y2 - y1)
                
    def clear_roi(self):
        """Clear the current ROI"""
        self.current_roi = None
        self.update()
        
    def set_roi(self, roi):
        """Set ROI programmatically"""
        if roi:
            self.current_roi = roi
            self.update()


class EnhancedCameraThread(QThread):
    """Enhanced camera thread with edge detection and zodiac processing"""
    frame_ready = pyqtSignal(QImage)
    midi_sent = pyqtSignal(str)
    error = pyqtSignal(str)
    execution_timeout = pyqtSignal()
    
    # New signals for edge detection
    edge_detection_log = pyqtSignal(str)
    baseline_established = pyqtSignal(str)

    def __init__(self, camera_id=0, roi=None, osc_port=5555, max_execution_time=300):
        super().__init__()
        self.camera_id = camera_id
        self.roi = roi            # (x, y, w, h)
        self.roi_confirmed = False  # Track if ROI is confirmed for MIDI processing
        self.osc_port = osc_port
        self.max_execution_time = max_execution_time
        self.running = False
        self.cap = None
        self.osc_client = None
        self.start_time = None

        # MIDI/OSC parameters
        self.notes = [60, 62, 64, 67, 69]
        self.min_velocity = 32
        self.max_velocity = 127
        self.note_duration = 1.0
        self.processing_interval = 30

        # Zodiac processing parameters
        self.zodiac_mode = True                  # enable 12-section mode
        self.zodiac_range = 88                   # pixel height per zodiac "hour"
        self.time_per_zodiac_sec = 30            # seconds per zodiac segment
        self.fps = 30                            # assumed frames per second
        self.hour_frame = int(self.fps * self.time_per_zodiac_sec)

        # Frame counter
        self.frame_count = 0
        
        # Edge detection
        self.edge_detector = EdgeChangeDetector(baseline_duration=5.0, threshold=0.15)

    def run(self):
        try:
            # Use modern AVFoundation backend with proper device type support
            self.cap = cv2.VideoCapture(self.camera_id, cv2.CAP_AVFOUNDATION)
            if not self.cap.isOpened():
                # Fallback to default backend
                self.cap = cv2.VideoCapture(self.camera_id)
                
            if not self.cap.isOpened():
                name = get_camera_name(self.camera_id)
                self.error.emit(f"Cannot open camera {self.camera_id} ({name})")
                return

            # Configure camera properties for optimal performance
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Minimize latency
            self.cap.set(cv2.CAP_PROP_FPS, self.fps)

            self.osc_client = udp_client.SimpleUDPClient("127.0.0.1", self.osc_port)
            self.midi_sent.emit(f"OSC client connected to localhost:{self.osc_port}")

            self.running = True
            self.start_time = time.time()
            self.frame_count = 0

            while self.running:
                # Check execution timeout
                if 0 < self.max_execution_time < (time.time() - self.start_time):
                    self.execution_timeout.emit()
                    break

                ret, frame = self.cap.read()
                if not ret:
                    break

                # Emit frame for display
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = rgb.shape
                img = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888).copy()
                self.frame_ready.emit(img)

                # Edge detection processing
                self.process_edge_detection(frame)

                # Process ROI at set interval (only if confirmed)
                if self.roi and self.roi_confirmed and self.frame_count % self.processing_interval == 0:
                    self.process_roi(frame)

                self.frame_count += 1
                time.sleep(1/self.fps)

        except Exception as e:
            name = get_camera_name(self.camera_id)
            self.error.emit(f"Error in camera thread ({name}): {e}")
        finally:
            if self.cap:
                self.cap.release()
                
    def process_edge_detection(self, frame):
        """Process frame for edge detection and change detection"""
        elapsed_time = time.time() - self.start_time
        
        # Convert to grayscale and apply Canny edge detection
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        canny = cv2.Canny(gray, 50, 200)
        
        # Baseline collection phase
        if elapsed_time < self.edge_detector.baseline_duration:
            self.edge_detector.add_baseline_frame(canny)
        elif not self.edge_detector.baseline_established:
            baseline_msg = self.edge_detector.establish_baseline()
            self.baseline_established.emit(f"\n=== {baseline_msg} ===\n")
        else:
            # Change detection phase
            change_detected, metrics = self.edge_detector.detect_change(canny)
            
            # Create verbose log message in the same format as the edge detection scripts
            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            log_message = (f"{'1' if change_detected else '0'} | {timestamp} | Frame {self.frame_count} | "
                          f"Edge: {metrics['edge_diff']:.1f}/{metrics['edge_threshold']:.1f} "
                          f"({'EXCEED' if metrics['edge_exceeded'] else 'OK'}) | "
                          f"Spatial: {metrics['spatial_diff']:.1f}/{metrics['spatial_threshold']:.1f} "
                          f"({'EXCEED' if metrics['spatial_exceeded'] else 'OK'})")
            
            # Emit edge detection log
            self.edge_detection_log.emit(log_message)

    def process_roi(self, frame):
        """Process either full ROI or 12-section zodiac slice into MIDI data"""
        if not self.roi:
            return
        x, y, w, h = self.roi

        # Determine vertical slice based on zodiac mode
        if self.zodiac_mode:
            # compute current zodiac "hour"
            hour_idx = (self.frame_count // self.hour_frame) % 12
            y0 = y + hour_idx * self.zodiac_range
            h0 = self.zodiac_range
        else:
            y0, h0 = y, h

        # Crop ROI slice
        roi = frame[y0:y0+h0, x:x+w]
        if roi.size == 0:
            self.error.emit(f"Invalid ROI slice at y={y0}, h={h0}")
            return

        # 1) Convert to grayscale
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

        # 2) Band-wise mean → magnitude array
        num_notes = len(self.notes)
        band_h = h0 // num_notes
        magnitudes = []
        for i in range(num_notes):
            start = i * band_h
            end = (i+1) * band_h if i < num_notes-1 else h0
            band = gray[start:end, :]
            magnitudes.append(float(np.mean(band)))
        magnitudes = np.array(magnitudes)

        # 3) Linear scale magnitudes → velocities
        min_mag, max_mag = magnitudes.min(), magnitudes.max()
        if max_mag > min_mag:
            norm = (magnitudes - min_mag) / (max_mag - min_mag)
        else:
            norm = np.zeros_like(magnitudes)
        velocities = (self.min_velocity + norm * (self.max_velocity - self.min_velocity)).astype(int)

        # 4) Build constant duration array
        durations = np.full(num_notes, self.note_duration)

        # 5) Send OSC/MIDI messages
        self.osc_client.send_message('/note', self.notes)
        self.osc_client.send_message('/velocity', velocities.tolist())
        self.osc_client.send_message('/duration', durations.tolist())

        # Emit log with organized format including port number
        details = [f"{note}:{vel}" for note, vel in zip(self.notes, velocities)]
        mode_info = f"zodiac[{hour_idx+1}/12]" if self.zodiac_mode else "full"
        self.midi_sent.emit(f"OSC [{self.osc_port}] - {mode_info} | Notes: {', '.join(details)} | Duration: {self.note_duration}s")

    def update_parameters(self, notes=None, min_velocity=None, max_velocity=None,
                          note_duration=None, processing_interval=None, zodiac_mode=None):
        if notes is not None:
            self.notes = notes
        if min_velocity is not None:
            self.min_velocity = min_velocity
        if max_velocity is not None:
            self.max_velocity = max_velocity
        if note_duration is not None:
            self.note_duration = note_duration
        if processing_interval is not None:
            self.processing_interval = processing_interval
        if zodiac_mode is not None:
            self.zodiac_mode = zodiac_mode
    
    def set_roi_confirmed(self, confirmed):
        """Set ROI confirmation status for MIDI processing"""
        self.roi_confirmed = confirmed

    def stop(self):
        self.running = False
        self.wait(1000)


class EnhancedTurntableApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Enhanced Turntable Control with Edge Detection")
        self.setGeometry(100, 100, 1600, 900)  # Even wider for better log readability
        self.camera_thread = None
        self.selected_roi = None
        self.roi_confirmed = False  # Track ROI confirmation state
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_time)
        self.init_ui()

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main = QVBoxLayout(central)

        # Camera controls
        cam_layout = QHBoxLayout()
        cam_layout.addWidget(QLabel("Camera:"))
        self.cam_box = QComboBox()
        self.cam_box.currentIndexChanged.connect(self.on_camera_selection_changed)
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.refresh_cameras)
        self.test_btn = QPushButton("Test Camera")
        self.test_btn.clicked.connect(self.test_camera)
        self.start_btn = QPushButton("Start")
        self.start_btn.clicked.connect(self.start_camera)
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.clicked.connect(self.stop_camera)
        self.stop_btn.setEnabled(False)
        cam_layout.addWidget(self.cam_box)
        cam_layout.addWidget(self.refresh_btn)
        cam_layout.addWidget(self.test_btn)
        cam_layout.addWidget(self.start_btn)
        cam_layout.addWidget(self.stop_btn)
        main.addLayout(cam_layout)

        # Camera information display
        cam_info_layout = QHBoxLayout()
        cam_info_layout.addWidget(QLabel("Camera Info:"))
        self.cam_info_label = QLabel("No camera selected")
        self.cam_info_label.setStyleSheet("color: gray; font-style: italic;")
        cam_info_layout.addWidget(self.cam_info_label)
        cam_info_layout.addStretch()
        main.addLayout(cam_info_layout)

        # Status display
        status_layout = QHBoxLayout()
        status_layout.addWidget(QLabel("Status:"))
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: green; font-weight: bold;")
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        main.addLayout(status_layout)

        # Main content area with splitter for video and edge detection log
        content_splitter = QSplitter(Qt.Horizontal)
        
        # Left side: Video display and ROI controls
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        # Video display
        self.video_label = ROISelector("Click and drag to select ROI")
        self.video_label.setFixedSize(640, 480)
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.roi_selected.connect(self.on_roi_selected)
        self.video_label.log_message.connect(self.log_message)
        left_layout.addWidget(self.video_label)

        # ROI selection
        roi_layout = QHBoxLayout()
        self.roi_btn = QPushButton("Select ROI")
        self.roi_btn.setEnabled(False)
        self.roi_btn.clicked.connect(self.select_roi)
        self.confirm_roi_btn = QPushButton("Confirm ROI")
        self.confirm_roi_btn.setEnabled(False)
        self.confirm_roi_btn.clicked.connect(self.confirm_roi)
        self.clear_roi_btn = QPushButton("Clear ROI")
        self.clear_roi_btn.setEnabled(False)
        self.clear_roi_btn.clicked.connect(self.clear_roi)
        self.roi_label = QLabel("ROI: None")
        roi_layout.addWidget(self.roi_btn)
        roi_layout.addWidget(self.confirm_roi_btn)
        roi_layout.addWidget(self.clear_roi_btn)
        roi_layout.addWidget(self.roi_label)
        roi_layout.addStretch()
        left_layout.addLayout(roi_layout)
        
        # Right side: Edge Detection Log
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.addWidget(QLabel("Edge Detection Trends"))
        
        self.edge_log = QTextEdit()
        self.edge_log.setReadOnly(True)
        self.edge_log.setFixedWidth(600)  # Increased width for better single-line readability
        self.edge_log.setFont(QFont("Monaco", 9))  # Native macOS monospace font for better performance
        self.edge_log.setStyleSheet("background-color: #1e1e1e; color: #e0e0e0; border: 1px solid #333;")
        right_layout.addWidget(self.edge_log)
        
        # Add widgets to splitter
        content_splitter.addWidget(left_widget)
        content_splitter.addWidget(right_widget)
        content_splitter.setSizes([640, 600])  # Adjusted sizes for wider log panel
        main.addWidget(content_splitter)

        # MIDI parameters group
        midi_group = QGroupBox("MIDI Parameters")
        grid = QGridLayout()
        grid.addWidget(QLabel("Notes (CSV):"), 0, 0)
        self.notes_edit = QTextEdit("60,62,64,67,69")
        self.notes_edit.setFixedHeight(50)
        grid.addWidget(self.notes_edit, 0, 1)
        grid.addWidget(QLabel("Min Vel:"), 1, 0)
        self.min_vel = QSpinBox(); self.min_vel.setRange(1,127); self.min_vel.setValue(32)
        grid.addWidget(self.min_vel, 1, 1)
        grid.addWidget(QLabel("Max Vel:"), 2, 0)
        self.max_vel = QSpinBox(); self.max_vel.setRange(1,127); self.max_vel.setValue(127)
        grid.addWidget(self.max_vel, 2, 1)
        grid.addWidget(QLabel("Note Dur (s):"), 3, 0)
        self.note_dur = QDoubleSpinBox(); self.note_dur.setRange(0.1,10.0); self.note_dur.setValue(1.0)
        grid.addWidget(self.note_dur, 3, 1)
        grid.addWidget(QLabel("Interval (frames):"), 4, 0)
        self.interval = QSpinBox(); self.interval.setRange(1,300); self.interval.setValue(30)
        grid.addWidget(self.interval, 4, 1)
        grid.addWidget(QLabel("Zodiac Mode:"), 5, 0)
        self.zodiac_mode = QCheckBox("Enable 12-section zodiac processing")
        self.zodiac_mode.setChecked(True)
        grid.addWidget(self.zodiac_mode, 5, 1)
        self.apply_params_btn = QPushButton("Apply Parameters")
        self.apply_params_btn.clicked.connect(self.apply_parameters)
        grid.addWidget(self.apply_params_btn, 6, 0, 1, 2)
        midi_group.setLayout(grid)
        main.addWidget(midi_group)

        # Execution group
        exec_group = QGroupBox("Execution")
        exec_layout = QGridLayout()
        exec_layout.addWidget(QLabel("Max Time (s):"), 0, 0)
        self.max_time = QSpinBox(); self.max_time.setRange(0,3600); self.max_time.setValue(300)
        exec_layout.addWidget(self.max_time, 0, 1)
        exec_layout.addWidget(QLabel("Elapsed:"), 1, 0)
        self.elapsed_lbl = QLabel("0.0s")
        exec_layout.addWidget(self.elapsed_lbl, 1, 1)
        exec_layout.addWidget(QLabel("OSC Port:"), 2, 0)
        self.osc_port = QSpinBox(); self.osc_port.setRange(1024,65535); self.osc_port.setValue(5555)
        exec_layout.addWidget(self.osc_port, 2, 1)
        exec_group.setLayout(exec_layout)
        main.addWidget(exec_group)

        # General log area (for MIDI/OSC messages)
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setFixedHeight(100)
        main.addWidget(self.log)

        # Now that all UI elements are created, refresh cameras
        self.refresh_cameras()

    def update_time(self):
        """Update elapsed execution time display"""
        if self.camera_thread and getattr(self.camera_thread, 'start_time', None):
            elapsed = time.time() - self.camera_thread.start_time
            self.elapsed_lbl.setText(f"{elapsed:.1f}s")

    def start_camera(self):
        """Start the camera thread with current settings"""
        if self.camera_thread and self.camera_thread.isRunning():
            self.log_message("Camera already running")
            return

        try:
            # Get camera ID from combo box
            camera_id = self.cam_box.currentData()
            
            # Create enhanced camera thread with current parameters
            self.camera_thread = EnhancedCameraThread(
                camera_id=camera_id,
                roi=self.selected_roi,
                osc_port=self.osc_port.value(),
                max_execution_time=self.max_time.value()
            )
            
            # Connect signals
            self.camera_thread.frame_ready.connect(self.update_video_display)
            self.camera_thread.midi_sent.connect(self.log_message)
            self.camera_thread.error.connect(self.log_error)
            self.camera_thread.execution_timeout.connect(self.on_execution_timeout)
            
            # Connect new edge detection signals
            self.camera_thread.edge_detection_log.connect(self.log_edge_detection)
            self.camera_thread.baseline_established.connect(self.log_baseline)
            
            # Update parameters from UI
            self.update_camera_parameters()
            
            # Start thread
            self.camera_thread.start()
            
            # Update UI state
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            self.roi_btn.setEnabled(True)
            self.confirm_roi_btn.setEnabled(False)  # Enabled after ROI selection
            self.clear_roi_btn.setEnabled(True)
            self.cam_box.setEnabled(False)
            
            # Start timer for elapsed time
            self.timer.start(100)  # Update every 100ms
            
            self.log_message(f"Started camera {camera_id}")
            self.status_label.setText("Running")
            self.status_label.setStyleSheet("color: green; font-weight: bold;")
            
            # Clear edge detection log
            self.edge_log.clear()
            self.edge_log.append("Edge Detection Started - Collecting baseline...")
            
        except Exception as e:
            self.log_error(f"Failed to start camera: {e}")
            self.status_label.setText("Error")
            self.status_label.setStyleSheet("color: red; font-weight: bold;")

    def stop_camera(self):
        """Stop the camera thread"""
        if self.camera_thread and self.camera_thread.isRunning():
            self.camera_thread.stop()
            self.camera_thread.wait(2000)  # Wait up to 2 seconds
            
            # Update UI state
            self.start_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            self.roi_btn.setEnabled(False)
            self.confirm_roi_btn.setEnabled(False)
            self.clear_roi_btn.setEnabled(False)
            self.cam_box.setEnabled(True)
            
            # Stop timer
            self.timer.stop()
            
            self.log_message("Camera stopped")
            self.status_label.setText("Ready")
            self.status_label.setStyleSheet("color: green; font-weight: bold;")
            
            # Add final message to edge detection log
            self.edge_log.append("\n--- Edge Detection Stopped ---")
        else:
            self.log_message("No camera running")

    def select_roi(self):
        """Enable ROI selection mode"""
        if not self.camera_thread or not self.camera_thread.isRunning():
            self.log_message("Camera must be running to select ROI")
            return
            
        self.log_message("Click and drag on the video to select ROI")
        self.roi_btn.setText("Selecting ROI...")
        self.roi_btn.setEnabled(False)

    def on_roi_selected(self, roi):
        """Handle ROI selection from the video display"""
        x, y, w, h = roi
        self.selected_roi = roi
        self.roi_confirmed = False  # Reset confirmation state
        self.roi_label.setText(f"ROI: ({x},{y},{w},{h}) - Not Confirmed")
        
        # Update camera thread ROI but don't confirm yet
        if self.camera_thread:
            self.camera_thread.roi = self.selected_roi
            self.camera_thread.set_roi_confirmed(False)
            
        # Reset ROI button and enable confirm button
        self.roi_btn.setText("Select ROI")
        self.roi_btn.setEnabled(True)
        self.confirm_roi_btn.setEnabled(True)
        
        self.log_message(f"ROI selected: {self.selected_roi} - Click 'Confirm ROI' to start MIDI processing")

    def confirm_roi(self):
        """Confirm ROI and start MIDI processing"""
        if not self.selected_roi:
            self.log_message("No ROI selected to confirm")
            return
            
        self.roi_confirmed = True
        x, y, w, h = self.selected_roi
        self.roi_label.setText(f"ROI: ({x},{y},{w},{h}) - CONFIRMED")
        
        # Enable MIDI processing in camera thread
        if self.camera_thread:
            self.camera_thread.set_roi_confirmed(True)
            
        # Update button states
        self.confirm_roi_btn.setEnabled(False)
        self.confirm_roi_btn.setText("ROI Confirmed ✓")
        
        self.log_message(f"ROI confirmed: {self.selected_roi} - MIDI processing started")

    def clear_roi(self):
        """Clear the current ROI"""
        self.selected_roi = None
        self.roi_confirmed = False
        self.roi_label.setText("ROI: None")
        self.video_label.clear_roi()
        
        # Update camera thread ROI and confirmation
        if self.camera_thread:
            self.camera_thread.roi = None
            self.camera_thread.set_roi_confirmed(False)
            
        # Reset button states
        self.confirm_roi_btn.setEnabled(False)
        self.confirm_roi_btn.setText("Confirm ROI")
            
        self.log_message("ROI cleared")

    def update_camera_parameters(self):
        """Update camera thread parameters from UI controls"""
        if not self.camera_thread:
            return
            
        # Parse notes from text edit
        try:
            notes_text = self.notes_edit.toPlainText().strip()
            if not notes_text:
                self.log_error("Notes field cannot be empty")
                return
                
            notes = [int(n.strip()) for n in notes_text.split(',') if n.strip()]
            if not notes:
                self.log_error("No valid notes found")
                return
                
            # Validate note range (MIDI notes 0-127)
            invalid_notes = [n for n in notes if n < 0 or n > 127]
            if invalid_notes:
                self.log_error(f"Invalid MIDI notes: {invalid_notes} (must be 0-127)")
                return
                
            self.camera_thread.update_parameters(
                notes=notes,
                min_velocity=self.min_vel.value(),
                max_velocity=self.max_vel.value(),
                note_duration=self.note_dur.value(),
                processing_interval=self.interval.value(),
                zodiac_mode=self.zodiac_mode.isChecked()
            )
        except ValueError as e:
            self.log_error(f"Invalid notes format: {e}")
        except Exception as e:
            self.log_error(f"Error updating parameters: {e}")

    def update_video_display(self, image):
        """Update the video display with new frame"""
        pixmap = QPixmap.fromImage(image)
        scaled_pixmap = pixmap.scaled(
            self.video_label.size(), 
            Qt.KeepAspectRatio, 
            Qt.SmoothTransformation
        )
        self.video_label.setPixmap(scaled_pixmap)
        
        # Update ROI display if there's a current ROI
        if hasattr(self, 'selected_roi') and self.selected_roi:
            self.video_label.set_roi(self.selected_roi)

    def log_edge_detection(self, message):
        """Log edge detection messages to the dedicated edge log window"""
        self.edge_log.append(message)
        # Auto-scroll to bottom
        scrollbar = self.edge_log.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def log_baseline(self, message):
        """Log baseline establishment message"""
        self.edge_log.append(message)
        scrollbar = self.edge_log.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def on_execution_timeout(self):
        """Handle execution timeout"""
        self.log_message("Execution timeout reached - stopping camera")
        self.stop_camera()

    def on_camera_selection_changed(self):
        """Handle camera selection change"""
        camera_id = self.cam_box.currentData()
        if camera_id is not None:
            self.log_message(f"Selected camera: {camera_id}")
            self.update_camera_info(camera_id)

    def update_camera_info(self, camera_id):
        """Update camera information"""
        try:
            name = get_camera_name(camera_id)
            if hasattr(self, 'cam_info_label'):
                self.cam_info_label.setText(f"{camera_id}: {name}")
        except Exception as e:
            self.log_error(f"Failed to update camera info: {e}")

    def log_message(self, message):
        timestamp = time.strftime('%H:%M:%S')
        if hasattr(self, 'log'):
            self.log.append(f"{timestamp}: {message}")

    def log_error(self, message):
        timestamp = time.strftime('%H:%M:%S')
        if hasattr(self, 'log'):
            self.log.append(f"{timestamp}: ERROR - {message}")

    def closeEvent(self, event):
        """Handle application close event"""
        if self.camera_thread and self.camera_thread.isRunning():
            self.log_message("Stopping camera thread...")
            self.camera_thread.stop()
            self.camera_thread.wait(3000)  # Wait up to 3 seconds
        event.accept()

    def refresh_cameras(self):
        """Refresh the camera list"""
        try:
            cams = get_all_camera_names()
            self.cam_box.clear()
            for i in range(2):
                name = cams.get(i, f"Camera {i}")
                self.cam_box.addItem(f"{i}: {name}", i)
            
            # Update camera info for the first camera if available
            if self.cam_box.count() > 0:
                camera_id = self.cam_box.currentData()
                if camera_id is not None:
                    self.update_camera_info(camera_id)
                else:
                    self.cam_info_label.setText("No camera selected")
            else:
                self.cam_info_label.setText("No cameras found")
                
            self.log_message(f"Refreshed camera list - found {self.cam_box.count()} cameras")
            
        except Exception as e:
            self.log_error(f"Failed to refresh cameras: {e}")
            self.cam_info_label.setText("Error refreshing cameras")

    def test_camera(self):
        """Test the selected camera"""
        camera_id = self.cam_box.currentData()
        if camera_id is None:
            self.log_message("No camera selected")
            return
            
        try:
            # Try to open the camera temporarily with modern AVFoundation backend
            cap = cv2.VideoCapture(camera_id, cv2.CAP_AVFOUNDATION)
            if not cap.isOpened():
                # Fallback to default backend
                cap = cv2.VideoCapture(camera_id)
                
            if not cap.isOpened():
                self.log_error(f"Cannot open camera {camera_id}")
                return
                
            # Try to read a frame
            ret, frame = cap.read()
            if not ret:
                self.log_error(f"Cannot read from camera {camera_id}")
                cap.release()
                return
                
            # Get camera properties
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            
            cap.release()
            
            # Display test frame
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb.shape
            img = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888).copy()
            self.update_video_display(img)
            
            # Update camera info with test results
            name = get_camera_name(camera_id)
            info_text = f"{camera_id}: {name} ({width}x{height}, {fps:.1f}fps)"
            self.cam_info_label.setText(info_text)
            self.cam_info_label.setStyleSheet("color: green; font-weight: bold;")
            
            self.log_message(f"Camera {camera_id} test successful - {width}x{height} @ {fps:.1f}fps")
            
        except Exception as e:
            self.log_error(f"Failed to test camera {camera_id}: {e}")
            self.cam_info_label.setStyleSheet("color: red; font-weight: bold;")

    def apply_parameters(self):
        """Apply MIDI parameter changes when user clicks the button"""
        self.update_camera_parameters()
        self.log_message("MIDI parameters applied.")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = EnhancedTurntableApp()
    win.show()
    sys.exit(app.exec_()) 