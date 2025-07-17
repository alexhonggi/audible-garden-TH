import sys
import os
import json # config.json 파일을 위해 추가
import time # 전송 간격 제어를 위해 추가
import argparse # CLI 모드를 위해 추가
import cv2 as cv
import numpy as np
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSlider, QComboBox, QGroupBox, QFileDialog, QCheckBox
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import QThread, pyqtSignal, Qt, QTimer, QEvent

# --- 경로 문제 해결 ---
# 스크립트가 어디서 실행되든 'revised' 폴더를 기준으로 모듈을 찾도록 경로 추가
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)
# --------------------

# fixed_turntable.py의 유틸리티 및 클래스들을 가져옵니다.
# (향후 이 클래스들은 GUI와 더 긴밀하게 통합될 수 있습니다)
from utils.camera_utils import open_camera, close_camera, get_camera_name
from utils.rotation_utils import RotationDetector
from fixed_turntable import (
    TurntableScoreRecorder, 
    calculate_timing_parameters, 
    draw_overlay_info, 
    detect_center_spindle, 
    extract_radial_scanline
)
# generate_midi_from_roi를 새로 임포트하고, 오래된 것들은 제거
from utils.audio_utils_simple import generate_midi_from_roi
from utils.osc_utils import init_client, send_midi

class CameraThread(QThread):
    """
    OpenCV 카메라 처리를 위한 별도의 스레드
    GUI의 응답성을 유지하기 위해 카메라 관련 작업은 백그라운드에서 실행합니다.
    """
    # 프레임을 GUI로 전달하기 위한 시그널
    frame_signal = pyqtSignal(np.ndarray)
    # 초기화 완료/실패 시그널
    camera_ready_signal = pyqtSignal(float, tuple) # fps, resolution
    camera_error_signal = pyqtSignal(str)
    # finished_recording = pyqtSignal() # <-- 자동 종료를 위한 새 시그널 (주석 처리)

    def __init__(self, camera_index=0, resolution=(1280, 720)):
        super().__init__()
        self.camera_index = camera_index
        self.resolution = resolution
        self.running = True
        self.camera = None
        self.fps = 6.0
        self.actual_res = (0, 0)

    def run(self):
        """스레드 실행 함수"""
        try:
            cam_name = get_camera_name(self.camera_index)
            print(f"📷 카메라 {self.camera_index} ({cam_name}) 열기 시도...")
            self.camera = open_camera(
                self.camera_index, self.resolution[0], self.resolution[1])
            if self.camera:
                self.actual_res = self.camera.get_frame_size()
                self.fps = self.camera.fps
                self.camera_ready_signal.emit(self.fps, self.actual_res)
                print(f"✅ 카메라 준비 완료. 실제 해상도: {self.actual_res}, FPS: {self.fps}")
            else:
                raise RuntimeError("카메라를 열 수 없습니다.")

        except Exception as e:
            error_msg = f"❌ 카메라 스레드 초기화 실패: {e}"
            print(error_msg)
            self.camera_error_signal.emit(error_msg)
            self.running = False
            return

        while self.running and self.camera and self.camera.is_open():
            ret, frame = self.camera.read_frame()
            if ret and frame is not None:
                # 90도 회전
                frame = cv.rotate(frame, cv.ROTATE_90_CLOCKWISE)
                self.frame_signal.emit(frame)
            else:
                # 프레임 읽기 실패 시 잠시 대기
                QThread.msleep(10)

    def stop(self):
        """스레드 종료 함수"""
        self.running = False
        if self.camera:
            close_camera(self.camera_index)
            self.camera = None
        self.quit()
        self.wait()


class TurntableGUI(QMainWindow):
    """
    메인 GUI 애플리케이션 클래스
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Audible Garden - Turntable GUI (Config-Managed)")
        self.setGeometry(100, 100, 1200, 800)

        # --- 설정 파일 로드 ---
        try:
            with open('config.json', 'r') as f:
                self.config = json.load(f)
            print("✅ config.json 로드 완료.")
        except FileNotFoundError:
            print("❌ CRITICAL: config.json 파일을 찾을 수 없습니다. 기본값으로 실행됩니다.")
            self.config = {} # 기본값으로 비어있는 config 사용
        except json.JSONDecodeError:
            print("❌ CRITICAL: config.json 파일의 형식이 잘못되었습니다.")
            self.config = {}

        # 중앙 위젯 설정
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # 메인 레이아웃
        self.main_layout = QHBoxLayout(self.central_widget)

        # 카메라 화면 표시부
        self.video_label = QLabel("카메라를 초기화하고 있습니다...")
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setMinimumSize(800, 600)
        self.video_label.setStyleSheet("border: 1px solid black; background-color: #333;")
        self.video_label.setMouseTracking(True) # 마우스 움직임 감지
        
        # 컨트롤 패널
        self.controls_layout = QVBoxLayout()
        self.controls_widget = QWidget()
        self.controls_widget.setLayout(self.controls_layout)
        self.controls_widget.setFixedWidth(350)

        # 컨트롤 위젯 추가
        self._create_control_widgets()

        # 레이아웃에 위젯 추가
        self.main_layout.addWidget(self.video_label)
        self.main_layout.addWidget(self.controls_widget)

        # 카메라 스레드 시작
        self.camera_thread = CameraThread()
        self.camera_thread.frame_signal.connect(self.update_frame)
        self.camera_thread.camera_ready_signal.connect(self.on_camera_ready)
        self.camera_thread.camera_error_signal.connect(self.on_camera_error)
        # self.camera_thread.finished_recording.connect(self.close) # <-- 시그널과 종료 함수 연결 (주석 처리)
        self.camera_thread.start()
        
        # 로직 처리 타이머 (GUI 이벤트 루프와 분리)
        self.logic_timer = QTimer(self)
        self.logic_timer.timeout.connect(self.process_logic)
        
        # 이벤트 필터 설치
        self.video_label.installEventFilter(self)
        
        # 상태 변수
        self.is_running = False
        self.is_playback_mode = False # 재생 모드 상태 추가
        self.current_frame = None
        self.manual_roi = None # 수동으로 설정된 ROI
        self.is_setting_roi = False # ROI 설정 모드 상태
        self.roi_start_point = None
        self.roi_end_point = None # 드래그 중인 ROI 끝점
        
        # 로직 관련 객체들
        self.osc_client = None
        self.score_recorder = None
        self.rpm_detector = None
        self.timing_info = {}
        self.roi_coords = None
        self.frame_count = 0
        self.transmission_count = 0
        self.current_fps = 0.0
        self.last_fps_time = 0
        self.zodiac_info = None # 오버레이에 그릴 정보
        self.detected_rpm_value = None # 오버레이에 그릴 정보
        
    def _create_control_widgets(self):
        """컨트롤 패널에 들어갈 위젯들을 생성하고 배치합니다."""
        
        # 1. 실행 컨트롤 그룹
        run_group = QGroupBox("실행 제어")
        run_layout = QHBoxLayout()
        self.start_button = QPushButton("시작")
        self.stop_button = QPushButton("정지")
        self.stop_button.setEnabled(False)
        run_layout.addWidget(self.start_button)
        run_layout.addWidget(self.stop_button)
        run_group.setLayout(run_layout)
        self.controls_layout.addWidget(run_group)

        # 2. RPM 설정 그룹
        rpm_group = QGroupBox("RPM 설정")
        rpm_layout = QVBoxLayout()
        self.rpm_slider = QSlider(Qt.Horizontal)
        self.rpm_slider.setRange(10, 100) # 1.0 ~ 10.0 RPM
        self.rpm_slider.setValue(25) # 기본 2.5 RPM
        self.rpm_label = QLabel(f"고정 RPM: {self.rpm_slider.value() / 10.0:.1f}")
        self.detect_rpm_checkbox = QCheckBox("실시간 RPM 감지 활성화")
        rpm_layout.addWidget(self.rpm_label)
        rpm_layout.addWidget(self.rpm_slider)
        rpm_layout.addWidget(self.detect_rpm_checkbox)
        rpm_group.setLayout(rpm_layout)
        self.controls_layout.addWidget(rpm_group)

        # 3. 모드 설정 그룹
        mode_group = QGroupBox("모드 설정")
        mode_layout = QVBoxLayout()
        # ROI 모드
        self.roi_mode_label = QLabel("ROI 모드")
        self.roi_mode_combo = QComboBox()
        self.roi_mode_combo.addItems(["Circular", "Rectangular"])
        
        # 수동 ROI 설정 버튼
        self.manual_roi_button = QPushButton("마우스로 ROI 설정 시작")
        self.manual_roi_button.setCheckable(True)
        
        # 스케일 모드 - config.json에서 관리하므로 UI는 비활성화
        self.scale_label = QLabel("음계(Scale) - (config.json에서 관리)")
        self.scale_combo = QComboBox()
        
        # config 파일에 정의된 스케일들로 콤보박스 채우기
        if self.config:
            scale_names = self.config.get('scales', {}).get('definitions', {}).keys()
            self.scale_combo.addItems(scale_names)
            default_scale = self.config.get('scales', {}).get('default_scale')
            if default_scale:
                self.scale_combo.setCurrentText(default_scale)
        
        self.scale_combo.setEnabled(False) # 사용자가 직접 변경하지 못하도록 비활성화

        mode_layout.addWidget(self.roi_mode_label)
        mode_layout.addWidget(self.roi_mode_combo)
        mode_layout.addWidget(self.manual_roi_button)
        mode_layout.addWidget(self.scale_label)
        mode_layout.addWidget(self.scale_combo)
        mode_group.setLayout(mode_layout)
        self.controls_layout.addWidget(mode_group)

        # 4. 악보 컨트롤 그룹
        score_group = QGroupBox("악보 제어")
        score_layout = QVBoxLayout()
        self.record_checkbox = QCheckBox("첫 바퀴 악보 녹음")
        self.record_checkbox.setChecked(True)
        self.load_button = QPushButton("저장된 악보 불러오기")
        self.playback_button = QPushButton("불러온 악보 재생")
        self.playback_button.setEnabled(False)
        score_layout.addWidget(self.record_checkbox)
        score_layout.addWidget(self.load_button)
        score_layout.addWidget(self.playback_button)
        score_group.setLayout(score_layout)
        self.controls_layout.addWidget(score_group)

        # 빈 공간 채우기
        self.controls_layout.addStretch(1)

        # 시그널 연결
        self.rpm_slider.valueChanged.connect(lambda val: self.rpm_label.setText(f"고정 RPM: {val / 10.0:.1f}"))
        self.start_button.clicked.connect(self.start_logic)
        self.stop_button.clicked.connect(self.stop_logic)
        self.load_button.clicked.connect(self.load_score_session)
        self.playback_button.clicked.connect(self.toggle_playback_mode)
        self.manual_roi_button.toggled.connect(self.toggle_roi_setting)

    def on_camera_ready(self, fps, resolution):
        """카메라가 성공적으로 초기화되었을 때 호출됩니다."""
        self.video_label.setText("카메라 준비 완료. 로직을 시작하세요.")
        print(f"GUI: 카메라 준비 완료 신호 받음 (FPS: {fps}, 해상도: {resolution})")
    
    def on_camera_error(self, error_message):
        """카메라 초기화 실패 시 호출됩니다."""
        self.video_label.setText(f"카메라 오류:\n{error_message}")
        self.start_button.setEnabled(False) # 카메라 없으면 시작 불가
        self.manual_roi_button.setEnabled(False)

    def toggle_roi_setting(self, checked):
        """'마우스로 ROI 설정' 버튼 토글 시 호출되는 함수."""
        self.is_setting_roi = checked
        if checked:
            self.manual_roi_button.setText("ROI 설정 중... (클릭하여 완료)")
            print("ℹ️ 마우스로 ROI를 설정하세요. 원형 모드는 중심 클릭, 사각형은 드래그하세요.")
        else:
            self.manual_roi_button.setText("마우스로 ROI 설정 시작")
            if self.roi_start_point:
                print(f"✅ 수동 ROI 설정 완료: {self.manual_roi}")
            self.roi_start_point = None
            self.roi_end_point = None # ROI 설정 완료 후 끝점 초기화

    def load_score_session(self):
        """'저장된 악보 불러오기' 버튼에 연결된 함수."""
        if self.is_running:
            print("⚠️ 로직이 실행 중일 때는 악보를 불러올 수 없습니다. 먼저 '정지'를 눌러주세요.")
            return
            
        session_path = QFileDialog.getExistingDirectory(
            self,
            "악보 세션 폴더 선택",
            "data/", # 기본 경로
            QFileDialog.ShowDirsOnly
        )
        
        if session_path:
            print(f"📂 세션 폴더 선택: {session_path}")
            # 기존 score_recorder가 있다면 새로 생성
            self.score_recorder = TurntableScoreRecorder(2.5, 30) # 임시 값으로 초기화
            if self.score_recorder.load_score_from_session(session_path):
                print(f"✅ 악보 '{os.path.basename(session_path)}' 로드 완료.")
                self.playback_button.setEnabled(True)
                self.is_playback_mode = True # 로드 성공 시 바로 재생 모드로
                self.playback_button.setText("재생 중 (클릭하여 실시간 모드로)")
            else:
                print(f"❌ 악보 로드 실패: {session_path}")
                self.playback_button.setEnabled(False)
    
    def toggle_playback_mode(self):
        """'재생' 버튼 클릭 시 재생 모드를 토글합니다."""
        if not self.score_recorder or not self.score_recorder.score_data['rotations']:
            print("⚠️ 재생할 악보 데이터가 없습니다.")
            return
            
        self.is_playback_mode = not self.is_playback_mode
        if self.is_playback_mode:
            print("▶️ 재생 모드 활성화.")
            self.playback_button.setText("재생 중 (클릭하여 실시간 모드로)")
        else:
            print("⏹️ 실시간 처리 모드 활성화.")
            self.playback_button.setText("불러온 악보 재생")

    def start_logic(self):
        """'시작' 버튼에 연결된 함수. 로직 처리를 시작합니다."""
        if self.is_running:
            return
            
        print("🚀 로직 처리 시작...")
        self.is_running = True
        
        # --- 초기화 ---
        # OSC 클라이언트
        self.osc_client = init_client(port=5555)
        
        # 현재 컨트롤 값들 가져오기
        current_rpm = self.rpm_slider.value() / 10.0
        use_detect_rpm = self.detect_rpm_checkbox.isChecked()
        current_scale = self.scale_combo.currentText()
        current_roi_mode = self.roi_mode_combo.currentText()
        do_record = self.record_checkbox.isChecked()

        # 타이밍 정보
        self.timing_info = calculate_timing_parameters(current_rpm, self.camera_thread.fps)
        
        # RPM 감지기
        if use_detect_rpm:
            # RotationDetector 클래스를 fixed_turntable에서 가져오도록 수정
            self.rpm_detector = RotationDetector(self.camera_thread.fps)
            if self.current_frame is not None:
                self.rpm_detector.set_reference_frame(self.current_frame)

        # 악보 녹음기
        self.score_recorder = TurntableScoreRecorder(current_rpm, self.camera_thread.fps)
        if do_record and not self.is_playback_mode: # 재생 모드가 아닐 때만 녹음
            self.score_recorder.start_recording(0, current_scale, current_roi_mode)

        # ROI 설정 (수동 ROI가 있으면 사용, 없으면 자동 감지)
        if self.manual_roi:
            self.roi_coords = self.manual_roi
            print(f"ℹ️ 수동 설정된 ROI를 사용합니다: {self.roi_coords}")
        elif self.current_frame is not None:
             if current_roi_mode == "Circular":
                 center_x, center_y, spindle_radius = detect_center_spindle(self.current_frame)
                 max_radius = np.sqrt(self.current_frame.shape[0]**2 + self.current_frame.shape[1]**2)
                 scan_radius = max_radius - spindle_radius - 20
                 self.roi_coords = (center_x, center_y, int(scan_radius))
             else: # Rectangular
                 x = self.current_frame.shape[1] // 2
                 y = 50
                 w = 1
                 h = min(88 * 10, self.current_frame.shape[0] - y - 50)
                 self.roi_coords = (x, y, w, h)

        # 상태 변수 리셋
        self.frame_count = 0
        self.transmission_count = 0
        self.last_fps_time = time.time()

        # 로직 타이머 시작
        # 카메라 FPS보다 약간 더 자주 (예: 2배) 실행하여 정밀도 향상
        timer_interval = 1000 / (self.camera_thread.fps * 2)
        self.logic_timer.start(int(timer_interval))

        # UI 업데이트
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)

    def stop_logic(self):
        """'정지' 버튼에 연결된 함수. 로직 처리를 중단합니다."""
        if not self.is_running:
            return
            
        print("🛑 로직 처리 중지...")
        self.is_running = False
        self.logic_timer.stop()
        
        # UI 업데이트
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)

    def update_frame(self, frame):
        """카메라 스레드로부터 새 프레임을 받아 화면에 표시 (모든 드로잉 담당)"""
        self.current_frame = frame.copy() # 나중 처리를 위해 프레임 저장
        overlay_frame = self.current_frame.copy()

        # 1. 로직 실행 중일 때 정보 오버레이 그리기
        if self.is_running and self.roi_coords:
            overlay_frame = draw_overlay_info(
                overlay_frame, self.roi_coords, self.zodiac_info, self.timing_info, self.frame_count,
                self.roi_mode_combo.currentText(), self.transmission_count, self.current_fps, self.score_recorder,
                detected_rpm=self.detected_rpm_value)

        # 2. 수동 ROI 설정 모드일 때 시각적 피드백 그리기
        if self.is_setting_roi and self.roi_start_point:
            overlay = overlay_frame.copy()
            current_mode = self.roi_mode_combo.currentText()
            
            if self.roi_end_point: # 드래그 중일 때
                if current_mode == "Circular":
                    radius = int(np.sqrt((self.roi_end_point[0] - self.roi_start_point[0])**2 + (self.roi_end_point[1] - self.roi_start_point[1])**2))
                    cv.circle(overlay, self.roi_start_point, radius, (255, 255, 0), 2)
                    cv.putText(overlay, f"R: {radius}", (self.roi_end_point[0]+10, self.roi_end_point[1]), cv.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
                else: # Rectangular
                    cv.rectangle(overlay, self.roi_start_point, self.roi_end_point, (0, 255, 255), 2)
            
            # 시작점 표시
            cv.circle(overlay, self.roi_start_point, 5, (0, 255, 0), -1)
            # 투명도 조절하여 원본과 합치기
            overlay_frame = cv.addWeighted(overlay, 0.6, overlay_frame, 0.4, 0)
            
        # 3. PyQt에서 표시할 수 있도록 QImage로 변환
        h, w, ch = overlay_frame.shape
        bytes_per_line = ch * w
        qt_image = QImage(overlay_frame.data, w, h, bytes_per_line, QImage.Format_BGR888)
        pixmap = QPixmap.fromImage(qt_image)
        
        # 4. 라벨 크기에 맞게 이미지 스케일 조정
        self.video_label.setPixmap(pixmap.scaled(
            self.video_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def closeEvent(self, event):
        """창이 닫힐 때 카메라 스레드 정리"""
        self.camera_thread.stop()
        event.accept()

    def eventFilter(self, source, event):
        """마우스 이벤트를 감지하여 ROI를 설정합니다."""
        if source is self.video_label and self.is_setting_roi and self.current_frame is not None:
            # 1. 좌표 변환 로직
            label_size = self.video_label.size()
            frame_size = self.current_frame.shape
            
            scale_w = label_size.width() / frame_size[1]
            scale_h = label_size.height() / frame_size[0]
            scale = min(scale_w, scale_h)
            
            scaled_w = int(frame_size[1] * scale)
            scaled_h = int(frame_size[0] * scale)
            
            offset_x = (label_size.width() - scaled_w) / 2
            offset_y = (label_size.height() - scaled_h) / 2

            def map_coords(pos):
                x = (pos.x() - offset_x) / scale
                y = (pos.y() - offset_y) / scale
                return int(x), int(y)

            # 2. 이벤트 핸들링
            if event.type() == QEvent.MouseButtonPress:
                self.roi_start_point = map_coords(event.pos())
                self.roi_end_point = None # 릴리즈 전까지는 끝점 초기화
                return True
            
            elif event.type() == QEvent.MouseMove:
                if self.roi_start_point:
                    self.roi_end_point = map_coords(event.pos())
                    return True

            elif event.type() == QEvent.MouseButtonRelease:
                if not self.roi_start_point: return True # 드래그 시작점이 없으면 무시
                
                end_point = map_coords(event.pos())
                current_mode = self.roi_mode_combo.currentText()
                
                if current_mode == "Circular":
                    # 중심점에서 릴리즈 지점까지의 거리를 반지름으로 설정
                    cx, cy = self.roi_start_point
                    radius = int(np.sqrt((end_point[0] - cx)**2 + (end_point[1] - cy)**2))
                    self.manual_roi = (cx, cy, radius)
                else: # Rectangular
                    # 시작점과 끝점으로 사각형 정의
                    x1, y1 = self.roi_start_point
                    x2, y2 = end_point
                    self.manual_roi = (min(x1, x2), min(y1, y2), abs(x2-x1), abs(y2-y1))
                
                self.manual_roi_button.setChecked(False) # 설정 완료 후 버튼 상태 해제
                return True

        return super().eventFilter(source, event)


    def process_logic(self):
        """
        메인 로직 처리 (데이터 계산 전담, 드로잉 X)
        """
        if not self.is_running or self.current_frame is None:
            return

        # --- 1. RPM 감지 및 타이밍 업데이트 ---
        if self.rpm_detector:
            self.detected_rpm_value = self.rpm_detector.calculate_rpm(self.current_frame)
            if self.detected_rpm_value is not None and self.detected_rpm_value > 0.5:
                current_rpm = self.detected_rpm_value
                self.timing_info = calculate_timing_parameters(current_rpm, self.camera_thread.fps)
                if self.score_recorder:
                    self.score_recorder.update_rpm(current_rpm, self.camera_thread.fps)

        # --- 2. ROI 처리 ---
        raw_roi_for_record = None
        current_roi_mode = self.roi_mode_combo.currentText()
        
        # 임시 zodiac_mode, zodiac_range. 나중에 GUI 옵션으로 추가 가능
        zodiac_mode = True
        zodiac_range = 88
        
        current_angle = (self.frame_count * self.timing_info['degrees_per_frame']) % 360
        roi_gray = np.array([])
        self.zodiac_info = None

        if self.roi_coords:
            if current_roi_mode == "Circular":
                center_x, center_y, radius = self.roi_coords
                scanline_values = extract_radial_scanline(self.current_frame, center_x, center_y, current_angle, radius)
                raw_roi_for_record = scanline_values
                if scanline_values is not None:
                    roi_gray = scanline_values.reshape(-1, 1)
                
                if zodiac_mode:
                    zodiac_section = int(current_angle / 30.0) % 12
                    self.zodiac_info = {'section': zodiac_section + 1, 'range': zodiac_range, 'angle': current_angle}
            
            elif current_roi_mode == "Rectangular":
                x, y, w, h = self.roi_coords
                roi = self.current_frame[y:y+h, x:x+w] # 기본 roi
                
                if zodiac_mode:
                    total_h = h
                    zodiac_y = y + int((current_angle / 360.0) * total_h)
                    zodiac_section = int(current_angle / 30.0) % 12
                    scan_y_start = max(y, zodiac_y - zodiac_range // 2)
                    scan_y_end = min(y + h, zodiac_y + zodiac_range // 2)
                    roi = self.current_frame[scan_y_start:scan_y_end, x:x+w]
                    self.zodiac_info = {'section': zodiac_section + 1, 'range': (scan_y_start, scan_y_end), 'angle': current_angle}

                raw_roi_for_record = roi
                if roi.size > 0:
                    roi_gray = cv.cvtColor(roi, cv.COLOR_BGR2GRAY)
        
        # --- 3. MIDI 데이터 생성 및 OSC 전송 ---
        midi_notes, velocities, durations = [], [], []
        
        if self.is_playback_mode:
            # 🎵 재생 모드
            if self.score_recorder and self.score_recorder.is_loaded:
                # (단, 전송은 간격에 맞춰서)
                current_notes_in_score = self.score_recorder.get_playback_notes(self.frame_count)
                if current_notes_in_score and current_notes_in_score[0]:
                        midi_notes, velocities, durations = current_notes_in_score

        # 🎼 실시간 처리 모드 (roi_gray가 유효할 때만 실행)
        elif roi_gray.size > 0:
            midi_notes, velocities, durations = generate_midi_from_roi(roi_gray, self.config)

        if self.osc_client and len(midi_notes) > 0:
            # duration 단위를 초(float)에서 ms(int)로 변환하여 전송
            durations_ms = [int(d * 1000) for d in durations]
            send_midi(self.osc_client, len(midi_notes), midi_notes, velocities, durations_ms)
            
            self.transmission_count += 1
            
            # 실시간 처리 모드에서만 녹음
            if not self.is_playback_mode and self.score_recorder and self.score_recorder.is_recording:
                self.score_recorder.add_notes(self.frame_count, midi_notes, velocities, durations, raw_roi_for_record, self.zodiac_info['section'] if self.zodiac_info else None)

        # --- 4. 악보 녹음 완료 확인 ---
        if not self.is_playback_mode and self.score_recorder and self.score_recorder.is_recording:
            if self.score_recorder.check_rotation_complete(self.frame_count):
                # 녹음이 완료되면 True를 반환합니다.
                # 이제 앱을 종료하는 대신, 메시지를 출력하고 계속 실행합니다.
                print("✅ 첫 바퀴 녹음 및 저장이 완료되었습니다. 실시간 OSC 전송을 계속합니다.")
                # 방금 녹화한 악보를 재생할 수 있도록 '재생' 버튼을 활성화합니다.
                self.playback_button.setEnabled(True)

        # --- 5. 프레임 카운트 증가 ---
        self.frame_count += 1
        
        # FPS 계산 (생략)


def run_cli(args):
    """CLI 모드 실행을 위한 메인 함수"""
    print("🚀 CLI 모드 실행을 시작합니다.")

    # 1. 설정 파일 로드
    try:
        with open(args.config, 'r') as f:
            config = json.load(f)
        print(f"✅ 설정 파일 '{args.config}' 로드 완료.")
    except Exception as e:
        print(f"❌ CRITICAL: 설정 파일 로드 실패: {e}. 실행을 중단합니다.")
        return

    # 2. 카메라 초기화
    cam_conf = config.get('camera', {})
    camera_index = cam_conf.get('index', 0)
    resolution = tuple(cam_conf.get('resolution', [1280, 720]))
    
    print(f"📷 카메라 {camera_index} ({get_camera_name(camera_index)}) 열기 시도...")
    camera = open_camera(camera_index, resolution[0], resolution[1])
    if not camera:
        print("❌ 카메라를 열 수 없습니다. 실행을 중단합니다.")
        return
    
    actual_res = camera.get_frame_size()
    fps = camera.fps
    print(f"✅ 카메라 준비 완료. 실제 해상도: {actual_res}, FPS: {fps}")

    # 3. 로직 컴포넌트 초기화
    osc_client = init_client(port=5555)
    timing_info = calculate_timing_parameters(args.rpm, fps)
    
    score_recorder = TurntableScoreRecorder(args.rpm, fps)
    if args.record:
        default_scale = config.get('scales', {}).get('default_scale', 'C_PENTATONIC')
        score_recorder.start_recording(0, default_scale, args.roi_mode)
        print(f"ℹ️ 악보 녹음 시작 (모드: {args.roi_mode}, 스케일: {default_scale})")

    # 4. 메인 루프 실행
    start_time = time.time()
    frame_count = 0
    transmission_count = 0
    roi_coords = None
    
    print(f"⏳ 지정된 시간 {args.duration}초 동안 또는 녹음 완료 시까지 실행됩니다...")

    while True:
        # 종료 조건 확인
        elapsed_time = time.time() - start_time
        if elapsed_time > args.duration:
            print("⌛ 지정된 실행 시간이 초과되어 프로그램을 종료합니다.")
            break

        ret, frame = camera.read_frame()
        if not ret or frame is None:
            print("⚠️ 카메라 프레임 수신 실패. 루프를 중단합니다.")
            break
        
        frame = cv.rotate(frame, cv.ROTATE_90_CLOCKWISE)

        # 첫 프레임에서 ROI 자동 감지
        if roi_coords is None:
            print("🔎 ROI 자동 감지를 시도합니다...")
            if args.roi_mode == "Circular":
                center_x, center_y, spindle_radius = detect_center_spindle(frame)
                if center_x is not None:
                    max_radius = np.sqrt(frame.shape[0]**2 + frame.shape[1]**2)
                    scan_radius = max_radius - spindle_radius - 20
                    roi_coords = (center_x, center_y, int(scan_radius))
                else:
                    print("❌ 원형 모드에서 중심점을 찾지 못했습니다. 실행을 중단합니다.")
                    break
            else: # Rectangular
                x = frame.shape[1] // 2
                y = 50
                w = 1 # 스캔라인이므로 폭은 1
                h = min(88 * 10, frame.shape[0] - y - 50)
                roi_coords = (x, y, w, h)
            print(f"✅ ROI 자동 감지 완료: {roi_coords}")
        
        # --- `process_logic`의 핵심 로직을 CLI 환경에 맞게 적용 ---
        raw_roi_for_record = None
        current_angle = (frame_count * timing_info['degrees_per_frame']) % 360
        roi_gray = np.array([])
        zodiac_info = None

        if args.roi_mode == "Circular":
            center_x, center_y, radius = roi_coords
            scanline_values = extract_radial_scanline(frame, center_x, center_y, current_angle, radius)
            raw_roi_for_record = scanline_values
            if scanline_values is not None:
                roi_gray = scanline_values.reshape(-1, 1)
            zodiac_section = int(current_angle / 30.0) % 12
            zodiac_info = {'section': zodiac_section + 1}

        elif args.roi_mode == "Rectangular":
            x, y, w, h = roi_coords
            roi = frame[y:y+h, x:x+w]
            raw_roi_for_record = roi
            if roi.size > 0:
                roi_gray = cv.cvtColor(roi, cv.COLOR_BGR2GRAY)
        
        if roi_gray.size > 0:
            midi_notes, velocities, durations = generate_midi_from_roi(roi_gray, config)
            if osc_client and len(midi_notes) > 0:
                durations_ms = [int(d * 1000) for d in durations]
                send_midi(osc_client, len(midi_notes), midi_notes, velocities, durations_ms)
                transmission_count += 1
                if score_recorder.is_recording:
                    score_recorder.add_notes(frame_count, midi_notes, velocities, durations, raw_roi_for_record, zodiac_info['section'] if zodiac_info else None)
        
        # 녹음 완료 확인
        if args.record and score_recorder.is_recording:
            if score_recorder.check_rotation_complete(frame_count):
                print("\n✅ 첫 바퀴 녹음 및 저장이 완료되었습니다.")
                if args.exit_on_record_complete:
                    print("🚪 녹음 완료 후 자동 종료 옵션이 활성화되어 실행을 마칩니다.")
                    break
                else:
                    # 녹음은 완료되었으므로 레코딩 플래그를 비활성화
                    score_recorder.is_recording = False 
        
        frame_count += 1
        print(f"\rElapsed: {int(elapsed_time)}s | Angle: {current_angle:.1f}° | Notes Sent: {transmission_count}", end="")

    # 5. 종료 처리
    print("\n🛑 로직 처리 중지 및 리소스 정리...")
    close_camera(camera_index)
    print("✨ 작업 완료.")


def main_gui():
    app = QApplication(sys.argv)
    gui = TurntableGUI()
    gui.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Audible Garden Turntable. 기본 실행 시 GUI 모드로, --cli 옵션 사용 시 CLI 모드로 작동합니다.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    
    # CLI 모드 인자
    parser.add_argument('--cli', action='store_true', help='GUI 없이 커맨드라인 모드로 프로그램을 실행합니다.')
    parser.add_argument('--duration', type=int, default=60, help='[CLI] 실행할 총 시간(초)을 지정합니다.')
    parser.add_argument('--config', type=str, default='config.json', help='[CLI] 사용할 설정 파일의 경로를 지정합니다.')
    parser.add_argument('--rpm', type=float, default=2.5, help='[CLI] 사용할 RPM(분당 회전 수)을 지정합니다.')
    parser.add_argument('--roi-mode', type=str, choices=['Circular', 'Rectangular'], default='Circular', help='[CLI] 사용할 ROI(관심 영역) 모드를 지정합니다.')
    parser.add_argument('--record', action='store_true', help='[CLI] 첫 바퀴를 녹음하여 악보 파일로 저장합니다.')
    parser.add_argument('--exit-on-record-complete', action='store_true', help='[CLI] 악보 녹음이 완료되면 프로그램을 자동으로 종료합니다.')

    args = parser.parse_args()

    # 인자에 따라 GUI 또는 CLI 모드 실행
    if args.cli:
        run_cli(args)
    else:
        # GUI 관련 인자가 들어왔을 경우 무시하고 GUI 실행
        if len(sys.argv) > 1:
            print("ℹ️ GUI 모드로 실행합니다. CLI 관련 인자는 무시됩니다.")
        main_gui()
