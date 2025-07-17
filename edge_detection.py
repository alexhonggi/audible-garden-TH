#!/usr/bin/env python3
"""
Live camera edge detection with change detection.

Captures from camera, establishes baseline from first 5 seconds, 
then detects discrepancies and prints "1" when changes occur.
"""

from __future__ import annotations

import argparse
import time
from datetime import datetime

import cv2
import numpy as np


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
        print(f"\n=== BASELINE: {len(self.edge_counts)} frames, {self.baseline_stats['mean_edge_count']:.0f} avg edges ===\n")
        
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


def run_change_detection(num_frames: int | None, baseline_duration: float, threshold: float, device: int) -> None:
    cap = cv2.VideoCapture(device)
    
    if not cap.isOpened():
        print("Error: Could not open camera")
        return

    detector = EdgeChangeDetector(baseline_duration, threshold)
    frame_nr = 0
    start_time = time.time()

    try:
        while cap.isOpened():
            if num_frames and frame_nr >= num_frames:
                break

            ret, img = cap.read()
            if not ret:
                print("Failed to capture frame. Exiting…" if frame_nr == 0 else "Stream ended.")
                break

            frame_nr += 1
            elapsed_time = time.time() - start_time

            # Apply Canny edge detection
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            canny = cv2.Canny(gray, 50, 200)
            
            # Baseline collection phase
            if elapsed_time < detector.baseline_duration:
                detector.add_baseline_frame(canny)
            elif not detector.baseline_established:
                detector.establish_baseline()
            else:
                # Change detection phase
                change_detected, metrics = detector.detect_change(canny)
                
                # Print detection result and similarity metrics
                timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]  # HH:MM:SS.mmm format
                print(f"{'1' if change_detected else '0'} | {timestamp} | Frame {frame_nr} | "
                      f"Edge: {metrics['edge_diff']:.1f}/{metrics['edge_threshold']:.1f} "
                      f"({'EXCEED' if metrics['edge_exceeded'] else 'OK'}) | "
                      f"Spatial: {metrics['spatial_diff']:.1f}/{metrics['spatial_threshold']:.1f} "
                      f"({'EXCEED' if metrics['spatial_exceeded'] else 'OK'})")

            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        cap.release()


def main() -> None:
    parser = argparse.ArgumentParser(description="Camera change detection - prints '1' when changes detected.")
    parser.add_argument("--device", type=int, default=0, help="Camera device (default: 0)")
    parser.add_argument("--num-frames", type=int, default=None, help="Number of frames to process")
    parser.add_argument("--baseline-duration", type=float, default=5.0, help="Baseline duration in seconds")
    parser.add_argument("--threshold", type=float, default=0.1, help="Change sensitivity (0.1=sensitive, 0.3=less)")

    args = parser.parse_args()

    print("Starting change detection...")
    run_change_detection(args.num_frames, args.baseline_duration, args.threshold, args.device)


if __name__ == "__main__":
    main() 