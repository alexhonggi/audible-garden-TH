"""
Camera utilities for secure and robust camera handling on macOS.
Uses modern AVFoundation APIs to avoid deprecated calls and warnings.
Supports Continuity Cameras with proper device type handling.
"""

import os
import time
import threading
import subprocess
import platform
from typing import Optional, List, Tuple, Callable, Dict
import cv2
import numpy as np

# Set environment variables to suppress OpenCV warnings and use modern APIs
os.environ["OPENCV_VIDEOIO_MSMF_ENABLE_HW_TRANSFORMS"] = "0"
os.environ["OPENCV_VIDEOIO_PRIORITY_MSMF"] = "0"

# For macOS, set environment to use modern AVFoundation APIs
if platform.system() == "Darwin":
    os.environ["OPENCV_VIDEOIO_PRIORITY_AVFOUNDATION"] = "1"
    # Ensure we use the modern device types
    os.environ["OPENCV_VIDEOIO_AVFOUNDATION_USE_CONTINUITY_CAMERA"] = "1"


def get_camera_device_names() -> Dict[int, str]:
    """
    Get camera device names using system-specific methods.
    On macOS, uses modern AVFoundation APIs to avoid deprecation warnings.
    
    Returns:
        Dictionary mapping device IDs to device names
    """
    device_names = {}
    
    if platform.system() == "Darwin":  # macOS
        try:
            # Use system_profiler to get camera information (text format is more reliable)
            result = subprocess.run(
                ["system_profiler", "SPCameraDataType"],
                capture_output=True, text=True, timeout=10
            )
            
            if result.returncode == 0:
                # Parse the text output to extract camera names
                lines = result.stdout.split('\n')
                camera_index = 0
                
                for line in lines:
                    line = line.strip()
                    # Look for camera names (they appear as "Camera Name:" in the output)
                    if line and line.endswith(':') and not line.startswith('Camera:') and not line.startswith('SPCameraDataType:'):
                        # Extract the camera name (everything before the colon)
                        camera_name = line[:-1].strip()  # Remove the trailing colon
                        if camera_name and len(camera_name) > 2:
                            device_names[camera_index] = camera_name
                            camera_index += 1
                            if camera_index >= 4:  # Limit to first 4 cameras
                                break
                    
        except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError):
            pass
            
        # Fallback: try using modern AVFoundation backend info
        if not device_names:
            for device_id in range(4):  # Check more devices
                try:
                    # Use AVFoundation backend with modern device type support
                    cap = cv2.VideoCapture(device_id, cv2.CAP_AVFOUNDATION)
                    if cap.isOpened():
                        # Try to get backend-specific info
                        backend_name = cap.getBackendName()
                        device_names[device_id] = f"Camera {device_id} ({backend_name})"
                        cap.release()
                except:
                    pass
                    
    elif platform.system() == "Windows":
        # On Windows, try to get device names from DirectShow
        for device_id in range(4):
            try:
                cap = cv2.VideoCapture(device_id, cv2.CAP_DSHOW)
                if cap.isOpened():
                    device_names[device_id] = f"Camera {device_id} (DirectShow)"
                    cap.release()
            except:
                pass
                
    else:  # Linux and other systems
        # Try to get device names from /dev/video* devices
        try:
            for device_id in range(4):
                try:
                    cap = cv2.VideoCapture(device_id)
                    if cap.isOpened():
                        device_names[device_id] = f"Camera {device_id} (V4L2)"
                        cap.release()
                except:
                    pass
        except:
            pass
    
    return device_names


class SecureCameraManager:
    """
    A secure camera manager that handles camera access safely on macOS.
    Uses modern AVFoundation APIs to avoid deprecated calls and warnings.
    """
    
    def __init__(self):
        self._cameras = {}
        self._lock = threading.Lock()
        self._max_local_devices = 2  # Only allow local webcams (0, 1)
        self._device_names = get_camera_device_names()
        
    def get_available_cameras(self) -> List[int]:
        """
        Get list of available local camera devices.
        Only returns local webcams (devices 0-1) for security.
        """
        available = []
        
        for device_id in range(self._max_local_devices):
            if self._test_camera_device(device_id):
                available.append(device_id)
                device_name = self._device_names.get(device_id, f"Camera {device_id}")
                print(f"Found camera device {device_id}: {device_name}")
            else:
                print(f"Camera device {device_id} not available")
                
        return available
    
    def _test_camera_device(self, device_id: int) -> bool:
        """
        Test if a camera device is available and working.
        Uses modern AVFoundation APIs to avoid deprecation warnings.
        Returns True if the device can be opened and read from.
        """
        if device_id >= self._max_local_devices:
            return False
            
        try:
            # Create a temporary capture object with modern AVFoundation backend
            cap = cv2.VideoCapture(device_id, cv2.CAP_AVFOUNDATION)
            
            if not cap.isOpened():
                # Fallback to default backend
                cap = cv2.VideoCapture(device_id)
                
            if not cap.isOpened():
                return False
                
            # Try to read a frame to verify it's working
            ret, frame = cap.read()
            cap.release()
            
            return ret and frame is not None
            
        except Exception as e:
            # Silently handle errors to avoid spam
            return False
    
    def open_camera(self, device_id: int, 
                   width: int = 640, 
                   height: int = 480,
                   fps: int = 30) -> Optional['SecureCamera']:
        """
        Open a camera device securely using modern AVFoundation APIs.
        
        Args:
            device_id: Camera device ID (0 or 1 for local webcams)
            width: Desired frame width
            height: Desired frame height
            fps: Desired frame rate
            
        Returns:
            SecureCamera object if successful, None otherwise
        """
        if device_id >= self._max_local_devices:
            raise ValueError(f"Device {device_id} is not allowed for security reasons")
            
        if not self._test_camera_device(device_id):
            raise RuntimeError(f"Camera device {device_id} is not available")
            
        camera = SecureCamera(device_id, width, height, fps)
        
        with self._lock:
            self._cameras[device_id] = camera
            
        return camera
    
    def close_camera(self, device_id: int):
        """Close a camera device."""
        with self._lock:
            if device_id in self._cameras:
                self._cameras[device_id].close()
                del self._cameras[device_id]
    
    def close_all_cameras(self):
        """Close all open cameras."""
        with self._lock:
            for camera in self._cameras.values():
                camera.close()
            self._cameras.clear()
    
    def get_camera_name(self, device_id: int) -> str:
        """
        Get the name of a camera device.
        
        Args:
            device_id: Camera device ID
            
        Returns:
            Camera device name or fallback string
        """
        return self._device_names.get(device_id, f"Camera {device_id}")
    
    def get_all_camera_names(self) -> Dict[int, str]:
        """
        Get all available camera device names.
        
        Returns:
            Dictionary mapping device IDs to device names
        """
        return self._device_names.copy()


class SecureCamera:
    """
    A secure camera wrapper that handles frame capture safely.
    Uses modern AVFoundation APIs to avoid deprecation warnings.
    """
    
    def __init__(self, device_id: int, width: int = 640, height: int = 480, fps: int = 30):
        self.device_id = device_id
        self.width = width
        self.height = height
        self.fps = fps
        self._cap = None
        self._lock = threading.Lock()
        self._is_open = False
        
        self._open_camera()
    
    def _open_camera(self):
        """Open the camera with proper configuration using modern APIs."""
        try:
            # Use AVFoundation backend with modern device type support
            self._cap = cv2.VideoCapture(self.device_id, cv2.CAP_AVFOUNDATION)
            
            if not self._cap.isOpened():
                # Fallback to default backend
                self._cap = cv2.VideoCapture(self.device_id)
                
            if not self._cap.isOpened():
                raise RuntimeError(f"Failed to open camera device {self.device_id}")
            
            # Configure camera properties
            self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            self._cap.set(cv2.CAP_PROP_FPS, self.fps)
            self._cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Minimize latency
            
            # Test frame capture
            ret, test_frame = self._cap.read()
            if not ret or test_frame is None:
                raise RuntimeError(f"Camera device {self.device_id} is not responding")
                
            self._is_open = True
            
        except Exception as e:
            if self._cap:
                self._cap.release()
                self._cap = None
            raise RuntimeError(f"Failed to initialize camera {self.device_id}: {str(e)}")
    
    def read_frame(self) -> Tuple[bool, Optional[np.ndarray]]:
        """
        Read a frame from the camera.
        
        Returns:
            Tuple of (success, frame) where frame is None if unsuccessful
        """
        if not self._is_open or self._cap is None:
            return False, None
            
        # Use timeout to prevent deadlocks
        if not self._lock.acquire(timeout=1.0):  # 1 second timeout
            return False, None
            
        try:
            ret, frame = self._cap.read()
            if not ret or frame is None:
                return False, None
            return True, frame
        except Exception as e:
            print(f"Error reading frame from camera {self.device_id}: {e}")
            return False, None
        finally:
            self._lock.release()
    
    def get_frame_size(self) -> Tuple[int, int]:
        """Get the current frame size."""
        if not self._is_open or self._cap is None:
            return (0, 0)
            
        width = int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        return (width, height)
    
    def is_open(self) -> bool:
        """Check if the camera is open and working."""
        return self._is_open and self._cap is not None
    
    def close(self):
        """Close the camera and release resources."""
        # Use timeout to prevent deadlocks
        if not self._lock.acquire(timeout=1.0):  # 1 second timeout
            print(f"Warning: Could not acquire lock to close camera {self.device_id}")
            return
            
        try:
            if self._cap:
                try:
                    self._cap.release()
                except Exception as e:
                    print(f"Error releasing camera {self.device_id}: {e}")
                self._cap = None
            self._is_open = False
        finally:
            self._lock.release()


class CameraThread(threading.Thread):
    """
    A thread for continuous camera capture.
    Uses modern AVFoundation APIs to avoid deprecation warnings.
    """
    
    def __init__(self, camera: SecureCamera, callback: Callable[[np.ndarray], None], 
                 frame_rate: int = 30):
        super().__init__()
        self.camera = camera
        self.callback = callback
        self.frame_rate = frame_rate
        self.running = False
        self.daemon = True  # Thread will be terminated when main program exits
    
    def start_capture(self):
        """Start the camera capture thread."""
        self.running = True
        self.start()
    
    def stop_capture(self):
        """Stop the camera capture thread."""
        self.running = False
    
    def run(self):
        """Main thread loop for camera capture."""
        frame_interval = 1.0 / self.frame_rate
        
        while self.running:
            start_time = time.time()
            
            try:
                ret, frame = self.camera.read_frame()
                if ret and frame is not None:
                    self.callback(frame)
            except Exception as e:
                print(f"Error in camera thread: {e}")
            
            # Maintain frame rate
            elapsed = time.time() - start_time
            if elapsed < frame_interval:
                time.sleep(frame_interval - elapsed)


# Global camera manager instance
_camera_manager = SecureCameraManager()

def get_camera_manager() -> SecureCameraManager:
    """Get the global camera manager instance."""
    return _camera_manager

def get_available_cameras() -> List[int]:
    """Get list of available local camera devices."""
    return _camera_manager.get_available_cameras()

def open_camera(device_id: int, width: int = 640, height: int = 480, fps: int = 30) -> Optional[SecureCamera]:
    """Open a camera device securely using modern AVFoundation APIs."""
    return _camera_manager.open_camera(device_id, width, height, fps)

def close_camera(device_id: int):
    """Close a camera device."""
    _camera_manager.close_camera(device_id)

def close_all_cameras():
    """Close all open cameras."""
    _camera_manager.close_all_cameras()

def get_camera_name(device_id: int) -> str:
    """Get the name of a camera device."""
    return _camera_manager.get_camera_name(device_id)

def get_all_camera_names() -> Dict[int, str]:
    """Get all available camera device names."""
    return _camera_manager.get_all_camera_names() 