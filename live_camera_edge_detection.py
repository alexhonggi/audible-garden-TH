#!/usr/bin/env python3
"""
Live camera edge detection with change detection and rerun visualization.

Captures from camera, establishes baseline from first 5 seconds, 
then detects changes and logs results to rerun viewer.
"""

from __future__ import annotations

import argparse
import time
from datetime import datetime

import cv2
import numpy as np
import rerun as rr  # pip install rerun-sdk
import rerun.blueprint as rrb


class EdgeChangeDetector:
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
        print(f"\n=== {baseline_msg} ===\n")
        
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


def run_canny(num_frames: int | None, baseline_duration: float, threshold: float, device: int) -> None:
    # Create a new video capture
    cap = cv2.VideoCapture(device)
    
    if not cap.isOpened():
        print("Error: Could not open camera")
        return

    detector = EdgeChangeDetector(baseline_duration, threshold)
    frame_nr = 0
    start_time = time.time()

    while cap.isOpened():
        if num_frames and frame_nr >= num_frames:
            break

        # Read the frame
        ret, img = cap.read()
        if not ret:
            if frame_nr == 0:
                print("Failed to capture any frame. No camera connected?")
            else:
                print("Can't receive frame (stream end?). Exiting…")
            break

        frame_nr += 1
        elapsed_time = time.time() - start_time

        # Get the current frame time. On some platforms it always returns zero.
        frame_time_ms = cap.get(cv2.CAP_PROP_POS_MSEC)
        if frame_time_ms != 0:
            rr.set_time("frame_time", duration=1e-3 * frame_time_ms)

        rr.set_time("frame_nr", sequence=frame_nr)

        # Log the original image
        rr.log("image/rgb", rr.Image(img, color_model="BGR"))

        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        rr.log("image/gray", rr.Image(gray))

        # Run the canny edge detector
        canny = cv2.Canny(gray, 50, 200)
        rr.log("image/canny", rr.Image(canny))

        # Change detection logic
        if elapsed_time < detector.baseline_duration:
            detector.add_baseline_frame(canny)
        elif not detector.baseline_established:
            detector.establish_baseline()
        else:
            # Change detection phase
            change_detected, metrics = detector.detect_change(canny)
            
            # Create verbose log message
            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            log_message = (f"{'1' if change_detected else '0'} | {timestamp} | Frame {frame_nr} | "
                          f"Edge: {metrics['edge_diff']:.1f}/{metrics['edge_threshold']:.1f} "
                          f"({'EXCEED' if metrics['edge_exceeded'] else 'OK'}) | "
                          f"Spatial: {metrics['spatial_diff']:.1f}/{metrics['spatial_threshold']:.1f} "
                          f"({'EXCEED' if metrics['spatial_exceeded'] else 'OK'})")
            
            # Print to console
            print(log_message)
            
            # Log detection state as scalar for plotting
            rr.log("detection/change_detected", rr.Scalars(1.0 if change_detected else 0.0))
            rr.log("detection/edge_diff", rr.Scalars(metrics['edge_diff']))
            rr.log("detection/spatial_diff", rr.Scalars(metrics['spatial_diff']))

        time.sleep(0.1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Live camera change detection with rerun visualization.")
    parser.add_argument("--device", type=int, default=0, help="Camera device (default: 0)")
    parser.add_argument("--num-frames", type=int, default=None, help="Number of frames to process")
    parser.add_argument("--baseline-duration", type=float, default=5.0, help="Baseline duration in seconds")
    parser.add_argument("--threshold", type=float, default=0.1, help="Change sensitivity (0.1=sensitive, 0.3=less)")

    rr.script_add_args(parser)
    args = parser.parse_args()

    rr.script_setup(
        args,
        "rerun_example_live_camera_edge_detection",
        default_blueprint=rrb.Vertical(
            rrb.Horizontal(
                rrb.Spatial2DView(origin="/image/rgb", name="Video"),
                rrb.Spatial2DView(origin="/image/gray", name="Video (Grayscale)"),
            ),
            rrb.Spatial2DView(origin="/image/canny", name="Canny Edge Detector"),
            rrb.TimeSeriesView(origin="/detection", name="Detection Metrics"),
            row_shares=[1, 2, 1],
        ),
    )

    print("Starting live camera change detection with rerun visualization...")
    run_canny(args.num_frames, args.baseline_duration, args.threshold, args.device)

    rr.script_teardown(args)


if __name__ == "__main__":
    main()
