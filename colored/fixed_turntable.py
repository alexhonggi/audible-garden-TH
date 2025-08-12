#!/usr/bin/env python3
"""
🎯 FIXED TURNTABLE - 주요 문제점 수정 버전
================================================
기존 final_turntable.py의 문제점들을 수정한 개선된 버전

🔧 수정된 문제점들:
1. ✅ 카메라 해상도 설정 (WIDTH 중복, HEIGHT 누락)
2. ✅ 실제 FPS 감지 및 사용  
3. ✅ RPM 기반 시간 계산
4. ✅ OSC 전송 개선
5. ✅ 88픽셀 → MIDI 매핑 유지 (의도된 설계)

Author: Bug Fix & Optimization
Date: 2025-01-08
"""

import cv2 as cv
import numpy as np
import pandas as pd
import time
import argparse
import json
import os
import sys
from datetime import datetime
from pythonosc import udp_client
from utils.osc_utils import init_client, send_midi, get_scale_notes, SCALES
from utils.audio_utils_simple import process_roi_to_midi_data
from utils.rotation_utils import RotationDetector
import copy

# --- 경로 문제 해결 ---
# 스크립트가 어디서 실행되든 'revised' 폴더를 기준으로 모듈을 찾도록 경로 추가
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)
# --------------------

from utils.camera_utils import open_camera
from utils.osc_utils import init_client, send_midi


class TurntableScoreRecorder:
    """
    🎼 턴테이블 악보 녹음 및 재생 시스템
    """
    
    def __init__(self, rpm=2.5, fps=30):
        self.rpm = rpm
        self.fps = fps
        self.rotation_time = 60.0 / rpm  # 한 바퀴 시간 (초)
        self.frames_per_rotation = int(self.rotation_time * fps)  # 한 바퀴 프레임 수
        
        # 📝 악보 데이터
        self.score_data = {
            'metadata': {
                'rpm': rpm,
                'fps': fps,
                'rotation_time': self.rotation_time,
                'frames_per_rotation': self.frames_per_rotation,
                'created_at': datetime.now().isoformat(),
                'scale': None,
                'roi_mode': None
            },
            'rotations': []  # 각 바퀴별 데이터
        }
        
        self.current_rotation = {
            'frame_start': 0,
            'notes': [],
            'zodiac_sections': [],
            'raw_rois': []
        }
        
        self.is_recording = False
        self.recorded_rotations = 0
        self.max_rotations = 1  # 첫 바퀴만 녹음
        self.is_loaded = False  # 악보 로드 상태 추가
        self.start_frame = None
        self.rpm = rpm
        self.rotation_time = 60.0 / self.rpm if self.rpm > 0 else float('inf')
        self.frames_per_rotation = int(self.rotation_time * fps) if self.rpm > 0 else 0
        
        self.raw_rois_for_panorama = []
        
        # 세션 폴더 경로는 start_recording에서 설정됨
        self.session_path = None

    def start_recording(self, frame_count, scale, roi_mode):
        """🎙️ 녹음 시작"""
        self.is_recording = True
        self.recorded_rotations = 0
        self.current_rotation['frame_start'] = frame_count
        self.score_data['metadata']['scale'] = scale
        self.score_data['metadata']['roi_mode'] = roi_mode
        
        # 세션 폴더 경로 생성 ('images' -> 'data')
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        mode = "Circular" if roi_mode == 'circular' else "Rectangular"
        scale_name = scale.replace(" ", "")
        folder_name = f"{timestamp}_{mode}_{scale_name}_{self.rpm:.1f}rpm"
        self.session_path = os.path.join("data", folder_name)
        
        print(f"🎙️ 악보 녹음 시작 (첫 바퀴)")
        print(f"📁 세션 폴더: {self.session_path}")
        
    def add_notes(self, frame_count, midi_notes, velocities, durations, raw_roi, zodiac_section=None):
        """📝 노트 데이터와 원본 ROI 데이터 추가"""
        if not self.is_recording:
            return
            
        # 현재 바퀴 내 상대 프레임
        relative_frame = frame_count - self.current_rotation['frame_start']
        
        note_data = {
            'frame': relative_frame,
            'notes': midi_notes.copy(),
            'velocities': velocities.copy(),
            'durations': durations.copy()
        }
        
        self.current_rotation['notes'].append(note_data)
        self.current_rotation['raw_rois'].append(raw_roi)
        
        if zodiac_section:
            self.current_rotation['zodiac_sections'].append({
                'frame': relative_frame,
                'section': zodiac_section
            })
    
    def check_rotation_complete(self, frame_count):
        """🔄 바퀴 완료 확인"""
        if not self.is_recording:
            return False
            
        relative_frame = frame_count - self.current_rotation['frame_start']
        
        if relative_frame >= self.frames_per_rotation:
            # 첫 바퀴 완료 시 시각적 악보 저장
            if self.recorded_rotations == 0:
                self.save_visual_score(self.current_rotation['raw_rois'])
            
            # 바퀴 완료
            self.recorded_rotations += 1
            self.score_data['rotations'].append(self.current_rotation.copy())
            
            print(f"✅ {self.recorded_rotations}번째 바퀴 녹음 완료 ({len(self.current_rotation['notes'])}개 노트)")
            
            # 다음 바퀴 준비
            self.current_rotation = {
                'frame_start': frame_count,
                'notes': [],
                'zodiac_sections': [],
                'raw_rois': []
            }
            
            # 첫 바퀴 완료시 녹음 종료
            if self.recorded_rotations >= self.max_rotations:
                self.stop_recording()
                return True
                
        return False
    
    def stop_recording(self):
        """⏹️ 녹음 종료 및 최종 저장"""
        if not self.is_recording: return
        
        self.is_recording = False
        print(f"🎼 악보 녹음 완료! 총 {self.recorded_rotations}바퀴")
        self.save_score() # JSON 악보 최종 저장
        
    def save_score(self):
        """💾 악보(JSON) 저장. 반드시 세션 폴더 내에 저장됩니다."""
        if not self.session_path:
            print("❌ [CRITICAL] 세션 경로가 설정되지 않아 악보를 저장할 수 없습니다. 'start_recording'이 먼저 호출되어야 합니다.")
            return None

        # 세션 폴더가 없으면 생성
        os.makedirs(self.session_path, exist_ok=True)
        
        filename = os.path.join(self.session_path, "score.json")

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                # 깊은 복사를 통해 원본 데이터 유지
                data_to_save = copy.deepcopy(self.score_data)
                
                # JSON 직렬화를 위해 numpy 배열을 list로 변환
                for rotation in data_to_save.get('rotations', []):
                    if 'raw_rois' in rotation and isinstance(rotation['raw_rois'], list):
                        rotation['raw_rois'] = [
                            roi.tolist() if isinstance(roi, np.ndarray) else roi 
                            for roi in rotation['raw_rois']
                        ]

                json.dump(data_to_save, f, indent=2, ensure_ascii=False)
            print(f"💾 악보 저장 완료: {filename}")
            return filename
        except Exception as e:
            print(f"❌ 악보 저장 실패: {e}")
            return None
            
    def save_visual_score(self, roi_list):
        """🖼️ 첫 바퀴 악보를 이미지와 배열로 저장. 반드시 세션 폴더 내에 저장됩니다."""
        if not self.session_path:
            print("❌ [CRITICAL] 세션 경로가 설정되지 않아 시각적 악보를 저장할 수 없습니다.")
            return

        if not roi_list:
            print("⚠️ 시각적 악보를 저장할 ROI 데이터가 없습니다.")
            return

        print("🖼️  시각적 악보(이미지/배열) 생성 중...")
        
        try:
            # 세션 폴더 생성 (안정성)
            os.makedirs(self.session_path, exist_ok=True)
            
            metadata = self.score_data['metadata']
            roi_mode = metadata.get('roi_mode', 'rectangular').lower()

            # 2. 파노라마 이미지와 데이터 배열 생성
            if roi_mode == 'circular':
                processed_rois = []
                # 모든 스캔라인을 88 길이로 정규화
                for scanline in roi_list:
                    if scanline is None or scanline.size == 0: continue
                    if len(scanline) != 88:
                        indices = np.linspace(0, len(scanline) - 1, 88, dtype=int)
                        resampled = scanline[indices]
                    else:
                        resampled = scanline
                    processed_rois.append(resampled)

                if not processed_rois:
                    print("⚠️ 처리할 원형 ROI 데이터가 없습니다.")
                    return
                
                # 각 스캔라인을 세로 열로 하여 이미지 생성
                score_array = np.array(processed_rois).T.astype(np.uint8)
                score_image = cv.cvtColor(score_array, cv.COLOR_GRAY2BGR)

            elif roi_mode == 'rectangular':
                # 너비가 0인 ROI 필터링
                valid_rois = [roi for roi in roi_list if roi is not None and roi.shape[1] > 0]
                if not valid_rois:
                     print("⚠️ 너비가 0인 ROI만 있어 시각적 악보를 생성할 수 없습니다.")
                     return
                
                # 모든 ROI의 높이를 첫 번째 ROI에 맞춰 통일 (hconcat 오류 방지)
                first_roi_height = valid_rois[0].shape[0]
                resized_rois = [
                    cv.resize(roi, (roi.shape[1], first_roi_height)) if roi.shape[0] != first_roi_height else roi
                    for roi in valid_rois
                ]

                score_image = cv.hconcat(resized_rois)
                score_array = cv.cvtColor(score_image, cv.COLOR_BGR2GRAY)
            
            else:
                print(f"⚠️ 알 수 없는 ROI 모드 '{roi_mode}'로 시각적 악보를 생성할 수 없습니다.")
                return
            
            # 3. 파일로 저장
            png_path = os.path.join(self.session_path, "score.png")
            array_path = os.path.join(self.session_path, "score.npy")

            cv.imwrite(png_path, score_image)
            np.save(array_path, score_array)
            
            print(f"✅ 악보 이미지 저장 완료: {png_path}")
            print(f"✅ 악보 배열 저장 완료: {array_path}")

        except Exception as e:
            import traceback
            print(f"❌ 시각적 악보 저장 실패: {e}")
            traceback.print_exc()

    def load_score_from_session(self, session_path):
        """📂 세션 폴더에서 악보(.json, .npy)를 로드"""
        json_path = os.path.join(session_path, 'score.json')
        npy_path = os.path.join(session_path, 'score.npy')
        
        loaded = False
        if os.path.exists(json_path):
            if self.load_score(json_path):
                # 로드 성공 시 메타데이터 업데이트
                self.rpm = self.score_data['metadata'].get('rpm', self.rpm)
                self.fps = self.score_data['metadata'].get('fps', self.fps)
                self.rotation_time = 60.0 / self.rpm
                self.frames_per_rotation = int(self.rotation_time * self.fps)
                loaded = True

        if os.path.exists(npy_path):
            try:
                # .npy 파일을 로드하여 raw_rois에 저장
                score_array = np.load(npy_path)
                # 파노라마 이미지를 다시 개별 프레임 ROI로 분할
                # 원형 모드: (높이, 프레임수) -> 프레임별 리스트
                # 사각 모드: (높이, 너비) -> 프레임별 리스트 (여기서는 너비를 1로 가정)
                if self.score_data['metadata']['roi_mode'] == 'circular':
                     self.score_data['rotations'] = [{'raw_rois': [score_array[:, i] for i in range(score_array.shape[1])]}]
                else: # rectangular
                     self.score_data['rotations'] = [{'raw_rois': [score_array[:, i:i+1] for i in range(score_array.shape[1])]}]
                
                print(f"📂 NumPy 악보 로드 완료: {npy_path}")
                loaded = True
            except Exception as e:
                print(f"❌ NumPy 악보 로드 실패: {e}")

        self.is_loaded = True # 로드 성공 시 상태 변경
        return loaded

    def get_playback_notes_from_npy(self, frame_count):
        """🎵 .npy 데이터로부터 재생용 MIDI 노트를 생성"""
        if not self.score_data.get('rotations') or 'raw_rois' not in self.score_data['rotations'][0]:
            return [], [], []

        rois = self.score_data['rotations'][0]['raw_rois']
        if not rois:
            return [], [], []
            
        # 현재 프레임에 맞는 ROI 선택
        relative_frame = frame_count % len(rois)
        roi_gray = rois[relative_frame]

        # MIDI 데이터로 변환
        scale = self.score_data['metadata'].get('scale', 'CPentatonic')
        
        if self.score_data['metadata']['roi_mode'] == 'circular':
             return process_circular_roi_to_midi_data(roi_gray, scale)
        else:
             return process_roi_to_midi_data(roi_gray, scale)

    def load_score(self, filename):
        """📂 악보 로드"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                self.score_data = json.load(f)
            print(f"📂 악보 로드 완료: {filename}")
            return True
        except Exception as e:
            print(f"❌ 악보 로드 실패: {e}")
            return False
    
    def get_playback_notes(self, frame_count):
        """🎵 재생용 노트 반환"""
        if not self.score_data['rotations']:
            return [], [], []
        
        # 첫 번째 바퀴 데이터 사용
        rotation = self.score_data['rotations'][0]
        relative_frame = frame_count % self.frames_per_rotation
        
        # 해당 프레임의 노트 찾기
        for note_data in rotation['notes']:
            if note_data['frame'] == relative_frame:
                return note_data['notes'], note_data['velocities'], note_data['durations']
        
        return [], [], []


def setup_camera_properly(camera_index=0, target_resolution=(1920, 1080)):
    """
    🎥 카메라 설정 및 최적화
    """
    cap = cv.VideoCapture(camera_index)
    
    # 📐 해상도 설정
    cap.set(cv.CAP_PROP_FRAME_WIDTH, target_resolution[0])
    cap.set(cv.CAP_PROP_FRAME_HEIGHT, target_resolution[1])
    
    # ⚡ 성능 최적화 설정
    cap.set(cv.CAP_PROP_BUFFERSIZE, 1)  # 버퍼 크기 최소화
    cap.set(cv.CAP_PROP_FPS, 30)  # FPS 설정
    
    # 🔄 첫 프레임 읽기로 설정 확인
    ret, test_frame = cap.read()
    if not ret:
        raise ValueError(f"❌ 카메라 {camera_index}를 열 수 없습니다.")
    
    # 📊 실제 설정값 확인
    actual_width = int(cap.get(cv.CAP_PROP_FRAME_WIDTH))
    actual_height = int(cap.get(cv.CAP_PROP_FRAME_HEIGHT))
    actual_fps = cap.get(cv.CAP_PROP_FPS)
    
    print(f"📹 카메라 설정 완료:")
    print(f"   - 해상도: {actual_width}x{actual_height}")
    print(f"   - FPS: {actual_fps}")
    
    return cap, actual_fps, (actual_width, actual_height)


def calculate_timing_parameters(rpm, fps):
    """
    ⏱️ 타이밍 매개변수 계산 (최적화)
    """
    rotation_time = 60.0 / rpm  # 한 바퀴 시간 (초)
    zodiac_section_time = rotation_time / 12  # Zodiac 구간 시간
    
    frames_per_rotation = int(rotation_time * fps)  # 한 바퀴 프레임 수
    frames_per_zodiac_section = int(zodiac_section_time * fps)  # Zodiac 구간 프레임 수
    degrees_per_frame = 360.0 / frames_per_rotation  # 프레임당 회전 각도
    
    return {
        'rpm': rpm,
        'rotation_time': rotation_time,
        'zodiac_section_time': zodiac_section_time,
        'frames_per_rotation': frames_per_rotation,
        'frames_per_zodiac_section': frames_per_zodiac_section,
        'degrees_per_frame': degrees_per_frame
    }


def detect_center_spindle(frame):
    """
    🎯 턴테이블 중심 스핀들(회색 꼭지) 자동 감지
    """
    # 🎨 Grayscale 변환
    gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
    
    # 🔍 엣지 검출
    edges = cv.Canny(gray, 50, 150)
    
    # 🔘 원형 검출 (스핀들 찾기)
    circles = cv.HoughCircles(
        gray, cv.HOUGH_GRADIENT, dp=1, minDist=50,
        param1=50, param2=30, minRadius=10, maxRadius=100
    )
    
    if circles is not None:
        circles = np.round(circles[0, :]).astype("int")
        
        # 🎯 가장 중앙에 가까운 원 선택
        frame_center_x = frame.shape[1] // 2
        frame_center_y = frame.shape[0] // 2
        
        best_circle = None
        min_distance = float('inf')
        
        for (x, y, r) in circles:
            distance = np.sqrt((x - frame_center_x)**2 + (y - frame_center_y)**2)
            if distance < min_distance:
                min_distance = distance
                best_circle = (x, y, r)
        
        if best_circle:
            return best_circle[0], best_circle[1], best_circle[2]
    
    # 🔍 자동 감지 실패시 프레임 중앙 사용
    print("⚠️ 스핀들 자동 감지 실패, 프레임 중앙 사용")
    return frame.shape[1] // 2, frame.shape[0] // 2, 20


def extract_radial_scanline(frame, center_x, center_y, angle_degrees, max_radius=None):
    """
    🔄 반지름 방향 스캔라인 추출 (최적화)
    """
    # 📐 각도를 라디안으로 변환
    angle_rad = np.radians(angle_degrees)
    
    # 📏 최대 반지름 계산
    if max_radius is None:
        corners = [
            (0, 0), (frame.shape[1], 0),
            (0, frame.shape[0]), (frame.shape[1], frame.shape[0])
        ]
        max_radius = 0
        for corner_x, corner_y in corners:
            dist = np.sqrt((corner_x - center_x)**2 + (corner_y - center_y)**2)
            max_radius = max(max_radius, dist)
    
    # 🔄 반지름 방향 픽셀 추출 (벡터화 최적화)
    r_values = np.arange(0, int(max_radius), 1)
    x_coords = (center_x + r_values * np.cos(angle_rad)).astype(int)
    y_coords = (center_y + r_values * np.sin(angle_rad)).astype(int)
    
    # 경계 확인
    valid_mask = (x_coords >= 0) & (x_coords < frame.shape[1]) & \
                 (y_coords >= 0) & (y_coords < frame.shape[0])
    
    valid_x = x_coords[valid_mask]
    valid_y = y_coords[valid_mask]
    
    if len(valid_x) == 0:
        return np.array([])
    
    # 픽셀 값 추출
    scanline_values = []
    for x, y in zip(valid_x, valid_y):
        pixel_value = frame[y, x]
        if len(pixel_value) == 3:  # BGR
            gray_value = int(0.299 * pixel_value[2] + 0.587 * pixel_value[1] + 0.114 * pixel_value[0])
        else:  # 이미 Grayscale
            gray_value = int(pixel_value)
        scanline_values.append(gray_value)
    
    return np.array(scanline_values)


def draw_circular_overlay(frame, center_x, center_y, radius, angle_degrees, zodiac_info=None):
    """
    🎨 원형 ROI 오버레이 그리기
    """
    overlay_frame = frame.copy()
    
    # 🎯 중심점 표시 (녹색)
    cv.circle(overlay_frame, (center_x, center_y), 8, (0, 255, 0), -1)
    cv.putText(overlay_frame, "Center", (center_x + 15, center_y), 
              cv.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
    
    # 🔄 반지름 스캔라인 표시 (파란색)
    angle_rad = np.radians(angle_degrees)
    end_x = int(center_x + radius * np.cos(angle_rad))
    end_y = int(center_y + radius * np.sin(angle_rad))
    
    cv.line(overlay_frame, (center_x, center_y), (end_x, end_y), (255, 0, 0), 2)
    
    # 🌟 Zodiac 구간 표시 (빨간색 호)
    if zodiac_info:
        zodiac_section = zodiac_info['section']
        zodiac_angle_start = (zodiac_section - 1) * 30  # 12구간 = 360°/12 = 30°
        zodiac_angle_end = zodiac_section * 30
        
        # 호 그리기
        for angle in range(int(zodiac_angle_start), int(zodiac_angle_end), 2):
            angle_rad = np.radians(angle)
            x = int(center_x + radius * np.cos(angle_rad))
            y = int(center_y + radius * np.sin(angle_rad))
            cv.circle(overlay_frame, (x, y), 3, (0, 0, 255), -1)
        
        # 구간 번호 표시
        text_angle = zodiac_angle_start + 15  # 구간 중앙
        text_rad = np.radians(text_angle)
        text_x = int(center_x + (radius + 30) * np.cos(text_rad))
        text_y = int(center_y + (radius + 30) * np.sin(text_rad))
        
        cv.putText(overlay_frame, f"Z{zodiac_section}", (text_x, text_y), 
                  cv.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
    
    # 📊 정보 텍스트
    info_texts = [
        f"Center: ({center_x}, {center_y})",
        f"Radius: {radius}px",
        f"Angle: {angle_degrees:.1f}°",
    ]
    
    if zodiac_info:
        info_texts.append(f"Zodiac: {zodiac_info['section']}/12")
    
    # 배경 박스
    cv.rectangle(overlay_frame, (10, 5), (300, 20 + len(info_texts) * 20), 
                (0, 0, 0), -1)
    cv.rectangle(overlay_frame, (10, 5), (300, 20 + len(info_texts) * 20), 
                (255, 255, 255), 1)
    
    for i, text in enumerate(info_texts):
        cv.putText(overlay_frame, text, (15, 20 + i * 20), 
                  cv.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    
    return overlay_frame


def process_circular_roi_to_midi_data(scanline_values, scale, vel_range=(32, 127), dur_range=(0.8, 1.8)):
    """
    🔄 원형 ROI 스캔라인을 MIDI 데이터로 변환
    """
    # 📏 스캔라인 길이를 88개 노트로 매핑
    if len(scanline_values) == 0:
        return [], [], []
    
    # 🔄 다운샘플링 (88개 노트로)
    if len(scanline_values) > 88:
        # 균등하게 88개로 다운샘플링
        indices = np.linspace(0, len(scanline_values)-1, 88, dtype=int)
        sampled_values = scanline_values[indices]
    else:
        # 부족한 경우 반복
        sampled_values = np.tile(scanline_values, int(np.ceil(88/len(scanline_values))))[:88]
    
    # 🎼 기존 음계 필터링 로직 사용
    return process_roi_to_midi_data(sampled_values.reshape(-1, 1), scale, vel_range, dur_range)


def draw_overlay_info(frame, roi_coords, zodiac_info, timing_info, frame_count, roi_mode="rectangular", 
                     transmission_count=0, current_fps=0, score_recorder=None, detected_rpm=None):
    """
    🎨 전체 프레임에 ROI 및 상태 정보 오버레이
    """
    overlay_frame = frame.copy()
    
    if roi_mode == "rectangular":
        x, y, w, h = roi_coords
        
        # 🎯 전체 ROI 영역 표시 (파란색 테두리)
        cv.rectangle(overlay_frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
        
        # 🌟 Zodiac 모드인 경우 현재 구간 표시
        if zodiac_info:
            zodiac_section = zodiac_info['section']
            # zodiac_info['range']는 (시작 y, 끝 y) 튜플입니다.
            zodiac_y_start, zodiac_y_end = zodiac_info['range']
            
            # 현재 Zodiac 구간 (빨간색 테두리)
            cv.rectangle(overlay_frame, (x, zodiac_y_start), (x + w, zodiac_y_end), 
                        (0, 0, 255), 3)
                
            # 구간 번호 표시
            cv.putText(overlay_frame, f"Zodiac {zodiac_section}/12", 
                      (x + w + 10, zodiac_y_start + 20), 
                      cv.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
        
        # 🎯 중심점 표시 (원형 ROI 준비용)
        center_x = x + w // 2
        center_y = y + h // 2
        cv.circle(overlay_frame, (center_x, center_y), 5, (0, 255, 0), -1)  # 녹색 점
        cv.putText(overlay_frame, "Center", (center_x + 10, center_y), 
                  cv.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)
        
        # 📊 상태 정보 텍스트 오버레이
        info_y = 30
        line_height = 25
        
        # 배경 사각형 (정보 가독성을 위해)
        cv.rectangle(overlay_frame, (10, 5), (450, info_y + line_height * 8), 
                    (0, 0, 0), -1)  # 검은색 배경
        cv.rectangle(overlay_frame, (10, 5), (450, info_y + line_height * 8), 
                    (255, 255, 255), 1)  # 흰색 테두리
        
        # 정보 텍스트
        info_texts = [
            f"Frame: {frame_count}",
            f"FPS: {current_fps:.1f}",
            f"RPM: {timing_info['rpm']:.1f}" + (f" (Detected: {detected_rpm:.1f})" if detected_rpm is not None else ""),
            f"Angle: {(frame_count * timing_info['degrees_per_frame']) % 360:.1f}°",
            f"ROI: {x},{y} ({w}x{h})",
            f"Mode: Rectangular",
            f"Transmission: #{transmission_count}",
        ]
        
        if zodiac_info:
            info_texts.extend([
                f"Zodiac: {zodiac_info['section']}/12",
                f"Section Time: {timing_info['zodiac_section_time']:.1f}s"
            ])
        
        # 녹음 상태 표시
        if score_recorder and score_recorder.is_recording:
            info_texts.append("🎙️ Recording...")
        
        for i, text in enumerate(info_texts):
            cv.putText(overlay_frame, text, (15, info_y + i * line_height), 
                      cv.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    
    elif roi_mode == "circular":
        center_x, center_y, radius = roi_coords
        current_angle = (frame_count * timing_info['degrees_per_frame']) % 360
        
        # 🔄 원형 오버레이 그리기
        overlay_frame = draw_circular_overlay(
            overlay_frame, center_x, center_y, radius, current_angle, zodiac_info)
        
        # 📊 추가 정보
        info_texts = [
            f"Frame: {frame_count}",
            f"FPS: {current_fps:.1f}",
            f"RPM: {timing_info['rpm']:.1f}" + (f" (Detected: {detected_rpm:.1f})" if detected_rpm is not None else ""),
            f"Mode: Circular",
            f"Transmission: #{transmission_count}",
        ]
        
        # 녹음 상태 표시
        if score_recorder and score_recorder.is_recording:
            info_texts.append("🎙️ Recording...")
        
        # 정보 박스 (우상단)
        cv.rectangle(overlay_frame, (frame.shape[1]-250, 5), (frame.shape[1]-10, 20 + len(info_texts) * 20), 
                    (0, 0, 0), -1)
        cv.rectangle(overlay_frame, (frame.shape[1]-250, 5), (frame.shape[1]-10, 20 + len(info_texts) * 20), 
                    (255, 255, 255), 1)
        
        for i, text in enumerate(info_texts):
            cv.putText(overlay_frame, text, (frame.shape[1]-245, 20 + i * 20), 
                      cv.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    
    return overlay_frame


def main():
    """
    🎯 메인 실행 함수
    """
    # 📋 명령행 인수 파싱
    parser = argparse.ArgumentParser(description='Fixed Turntable - LP 턴테이블 시뮬레이터')
    parser.add_argument('-r', '--manual_roi', type=str, default='y', help='수동 ROI 선택 (y/n)')
    parser.add_argument('-s', '--scale', type=str, default='CPentatonic', 
                       help='음계 (piano, CMajor, CPentatonic, CLydian, CWhole)')
    parser.add_argument('--rpm', type=float, default=2.5, help='원판 회전 속도 (RPM)')
    parser.add_argument('--resolution', type=str, default='1920x1080', 
                       help='카메라 해상도 (예: 1920x1080)')
    parser.add_argument('--camera', type=int, default=0, help='카메라 인덱스')
    parser.add_argument('--skip', type=int, default=1, help='프레임 건너뛰기 (1=모든 프레임)')
    parser.add_argument('--vel_min', type=int, default=32, help='최소 벨로시티')
    parser.add_argument('--vel_max', type=int, default=127, help='최대 벨로시티')
    parser.add_argument('--dur_min', type=float, default=0.8, help='최소 지속시간')
    parser.add_argument('--dur_max', type=float, default=1.8, help='최대 지속시간')
    parser.add_argument('--show_full', type=str, default='y', help='전체 화면 표시 (y/n)')
    parser.add_argument('--roi_mode', type=str, default='rectangular', 
                       help='ROI 모드 (rectangular/circular)')
    parser.add_argument('--record_score', type=str, default='y', 
                       help='첫 바퀴 악보 녹음 (y/n)')
    parser.add_argument('--detect_rpm', type=str, default='n',
                          help='실제 RPM 감지 사용 (y/n)')
    parser.add_argument('--load_score', type=str, default=None,
                        help='지정된 세션 폴더에서 악보를 불러와 재생 모드로 시작')
    
    args = parser.parse_args()
    
    # 📐 해상도 파싱
    try:
        width, height = map(int, args.resolution.split('x'))
        target_resolution = (width, height)
    except:
        print("⚠️ 잘못된 해상도 형식. 기본값 1920x1080 사용")
        target_resolution = (1920, 1080)
    
    print("🎯 Fixed Turntable 시작")
    print(f"   - 음계: {args.scale}")
    print(f"   - RPM: {args.rpm}")
    print(f"   - 해상도: {target_resolution[0]}x{target_resolution[1]}")
    print(f"   - ROI 모드: {args.roi_mode}")
    print(f"   - 악보 녹음: {args.record_score}")
    print(f"   - RPM 감지: {'활성화' if args.detect_rpm.lower() == 'y' else '비활성화'}")
    
    if args.load_score:
        print(f"   - 악보 로드: {args.load_score}")

    try:
        # 🎥 카메라 설정
        cap, actual_fps, actual_resolution = setup_camera_properly(
            args.camera, target_resolution)
        
        # ⏱️ 타이밍 매개변수 계산
        timing = calculate_timing_parameters(args.rpm, actual_fps)
        
        # 📡 OSC 클라이언트 초기화
        client_5555 = init_client(port=5555)
        print(f"📡 OSC 클라이언트 초기화 완료 (포트 5555)")
        
        # 🌀 회전 감지기 초기화 (필요시)
        rpm_detector = None
        if args.detect_rpm.lower() == 'y':
            rpm_detector = RotationDetector(actual_fps)

        # 🎼 악보 녹음 시스템 초기화
        score_recorder = TurntableScoreRecorder(args.rpm, actual_fps)
        
        # 📂 저장된 악보 불러오기 (옵션)
        playback_mode = False
        if args.load_score:
            if os.path.isdir(args.load_score):
                if score_recorder.load_score_from_session(args.load_score):
                    print(f"✅ 악보 '{args.load_score}' 로드 완료. 재생 모드로 시작합니다.")
                    playback_mode = True
                    # 로드한 악보의 RPM으로 타이밍 정보 업데이트
                    timing = calculate_timing_parameters(score_recorder.rpm, actual_fps)
                else:
                    print(f"⚠️ 악보 '{args.load_score}' 로드 실패. 실시간 모드로 시작합니다.")
            else:
                print(f"⚠️ 폴더를 찾을 수 없음: '{args.load_score}'. 실시간 모드로 시작합니다.")

        # 🖼️ 첫 프레임 읽기 및 ROI 선택
        ret, first_frame = cap.read()
        if not ret:
            raise ValueError("❌ 첫 프레임을 읽을 수 없습니다.")
        
        # 🔄 수직 방향으로 회전 (기존 로직 유지)
        first_frame = cv.rotate(first_frame, cv.ROTATE_90_CLOCKWISE)
        print(f"📐 프레임 크기: {first_frame.shape}")
        
        # 🌀 회전 감지기 기준 프레임 설정
        if rpm_detector:
            rpm_detector.set_reference_frame(first_frame)

        # 🎯 ROI 설정
        if args.roi_mode == "circular":
            # �� 원형 ROI: 스핀들 자동 감지
            center_x, center_y, spindle_radius = detect_center_spindle(first_frame)
            
            # 📏 반지름 계산 (화면 끝까지)
            corners = [
                (0, 0), (first_frame.shape[1], 0),
                (0, first_frame.shape[0]), (first_frame.shape[1], first_frame.shape[0])
            ]
            max_radius = 0
            for corner_x, corner_y in corners:
                dist = np.sqrt((corner_x - center_x)**2 + (corner_y - center_y)**2)
                max_radius = max(max_radius, dist)
            
            # 스핀들 반지름만큼 제외
            scan_radius = max_radius - spindle_radius - 20  # 여유 20픽셀
            
            roi_coords = (center_x, center_y, int(scan_radius))
            print(f"🎯 원형 ROI 설정: 중심({center_x}, {center_y}), 반지름 {scan_radius}")
            
        else:
            # 📐 직사각형 ROI (기존 방식)
            if args.manual_roi.lower() == 'y':
                print("🖱️ 마우스로 ROI를 선택하세요...")
                
                # 화면에 맞게 크기 조정 (선택용)
                scale_percent = 20
                width = int(first_frame.shape[1] * scale_percent / 100)
                height = int(first_frame.shape[0] * scale_percent / 100)
                resized_frame = cv.resize(first_frame, (width, height), interpolation=cv.INTER_AREA)
                
                x, y, w, h = cv.selectROI('ROI 선택', resized_frame, False)
                
                # 원본 크기로 스케일링
                x = int(x / (scale_percent/100))
                y = int(y / (scale_percent/100))  
                w = int(w / (scale_percent/100))
                h = int(h / (scale_percent/100))
                
                cv.destroyWindow('ROI 선택')
                
            else:
                # 기본 ROI (중앙 세로 라인)
                x = first_frame.shape[1] // 2
                y = 50
                w = 1  # 1픽셀 너비 스캔라인
                h = min(88 * 10, first_frame.shape[0] - y - 50)  # 88*10 또는 가능한 최대
            
            roi_coords = (x, y, w, h)
            print(f"🎯 직사각형 ROI 설정: x={x}, y={y}, w={w}, h={h}")
        
        # 🌟 Zodiac 매개변수
        zodiac_range = 88
        zodiac_mode = True
        
        # 📊 메인 루프
        frame_count = 0
        skip_rate = args.skip
        transmission_count = 0
        last_fps_time = time.time()
        fps_frames = 0
        current_fps = 0.0
        current_rpm = args.rpm
        
        print("🎵 실시간 처리 시작 (ESC로 종료)")
        print("📺 키 조작:")
        print("   - ESC: 종료")
        print("   - 's': 스케일 변경")
        print("   - 'f': 전체 화면 토글")
        print("   - 'r': ROI 다시 선택")
        print("   - 'm': ROI 모드 변경 (직사각형 ↔ 원형)")
        print("   - 'p': 악보 재생 모드 토글")
        print("   - 'd': 회전 감지 기준 프레임 재설정")
        
        show_full_frame = args.show_full.lower() == 'y'
        current_roi_mode = args.roi_mode
        
        # 🎙️ 악보 녹음 시작 (악보 로드 시 비활성화)
        if args.record_score.lower() == 'y' and not args.load_score:
            score_recorder.start_recording(frame_count, args.scale, current_roi_mode)
        
        while True:
            loop_start = time.time()
            
            ret, frame = cap.read()
            if not ret:
                print("❌ 프레임 읽기 실패")
                break
            
            # 🔄 수직 회전
            vertical_frame = cv.rotate(frame, cv.ROTATE_90_CLOCKWISE)
            
            # 🌀 실제 RPM 감지 및 타이밍 정보 업데이트
            detected_rpm_value = None
            if rpm_detector:
                detected_rpm_value = rpm_detector.calculate_rpm(vertical_frame)
                # 감지된 RPM이 안정적일 때만 (0 이상) 업데이트
                if detected_rpm_value > 0.5: 
                    current_rpm = detected_rpm_value
                    timing = calculate_timing_parameters(current_rpm, actual_fps)
                    # 악보 녹음기에도 최신 RPM 반영
                    score_recorder.rpm = current_rpm
                    score_recorder.rotation_time = 60.0 / current_rpm
                    score_recorder.frames_per_rotation = int(score_recorder.rotation_time * actual_fps)

            # 🎯 ROI 처리
            raw_roi_for_record = None
            if current_roi_mode == "circular":
                # 🔄 원형 ROI 처리
                center_x, center_y, radius = roi_coords
                current_angle = (frame_count * timing['degrees_per_frame']) % 360
                
                # 반지름 스캔라인 추출
                scanline_values = extract_radial_scanline(
                    vertical_frame, center_x, center_y, current_angle, radius)
                
                raw_roi_for_record = scanline_values

                # Zodiac 모드 처리
                if zodiac_mode:
                    # 현재 각도를 기준으로 Zodiac 섹션 결정 (0~11)
                    zodiac_section = int(current_angle / 30.0) % 12
                    zodiac_info = {
                        'section': zodiac_section + 1,
                        'range': zodiac_range,
                        'angle': current_angle
                    }
                else:
                    zodiac_info = None
                
                # ROI 이미지 생성 (시각화용)
                roi = np.zeros((len(scanline_values), 50, 3), dtype=np.uint8)
                for i, val in enumerate(scanline_values):
                    roi[i, :] = [val, val, val]
                
            else:
                # 📐 직사각형 ROI 처리 (기존 방식)
                x, y, w, h = roi_coords
                
                if zodiac_mode:
                    # 현재 각도를 기준으로 Zodiac 섹션 결정
                    current_angle = (frame_count * timing['degrees_per_frame']) % 360
                    
                    # 각도에 따라 y 위치 결정 (0~360 -> y ~ y+h)
                    total_h = h # 전체 ROI 높이
                    zodiac_y = y + int((current_angle / 360.0) * total_h)
                    
                    # Zodiac 섹션은 12개로 나누어 계산
                    zodiac_section = int(current_angle / 30.0) % 12

                    # 경계 확인 및 ROI 추출
                    scan_y_start = max(y, zodiac_y - zodiac_range // 2)
                    scan_y_end = min(y + h, zodiac_y + zodiac_range // 2)
                    roi = vertical_frame[scan_y_start:scan_y_end, x:x+w]
                    
                    raw_roi_for_record = roi

                    zodiac_info = {
                        'section': zodiac_section + 1,
                        'range': (scan_y_start, scan_y_end),
                        'angle': current_angle
                    }
                    
                else:
                    roi = vertical_frame[y:y+h, x:x+w]
                    raw_roi_for_record = roi
                    zodiac_info = None
            
            # 🎨 Grayscale 변환
            if current_roi_mode == "circular":
                roi_gray = scanline_values.reshape(-1, 1)
            else:
                roi_gray = cv.cvtColor(roi, cv.COLOR_BGR2GRAY)
            
            # 🖼️ 화면 표시
            if show_full_frame:
                # 📺 전체 프레임에 오버레이 그리기
                overlay_frame = draw_overlay_info(
                    vertical_frame, roi_coords, zodiac_info, timing, frame_count, 
                    current_roi_mode, transmission_count, current_fps, score_recorder,
                    detected_rpm=detected_rpm_value)
                
                # 화면 크기 조정 (너무 클 수 있으므로)
                display_scale = 0.7
                display_width = int(overlay_frame.shape[1] * display_scale)
                display_height = int(overlay_frame.shape[0] * display_scale)
                overlay_resized = cv.resize(overlay_frame, (display_width, display_height))
                
                cv.imshow('Webcam Full View', overlay_resized)
            
            # 🎯 ROI 세부 표시
            if current_roi_mode == "circular":
                # 원형 모드: 스캔라인 시각화
                cv.imshow('Radial Scanline', roi)
            else:
                cv.imshow('ROI Detail', roi)
            
            # 🎵 MIDI 데이터 처리 (프레임 건너뛰기 적용)
            if frame_count % skip_rate == 0:
                try:
                    if playback_mode:
                        # 🎵 재생 모드
                        # .npy 데이터가 있으면 우선 사용, 없으면 .json 데이터 사용
                        if 'raw_rois' in score_recorder.score_data.get('rotations', [{}])[0]:
                            midi_notes, velocities, durations = score_recorder.get_playback_notes_from_npy(frame_count)
                        elif score_recorder.score_data['rotations']:
                            midi_notes, velocities, durations = score_recorder.get_playback_notes(frame_count)
                        else:
                            midi_notes, velocities, durations = [], [], []
                    else:
                        # 🎼 실시간 처리 모드
                        if current_roi_mode == "circular":
                            midi_notes, velocities, durations = process_circular_roi_to_midi_data(
                                scanline_values, args.scale, 
                                (args.vel_min, args.vel_max),
                                (args.dur_min, args.dur_max)
                            )
                        else:
                            midi_notes, velocities, durations = process_roi_to_midi_data(
                                roi_gray, args.scale, 
                                (args.vel_min, args.vel_max),
                                (args.dur_min, args.dur_max)
                            )
                    
                    # 📡 OSC 전송
                    if len(midi_notes) > 0:
                        send_midi(client_5555, len(midi_notes), midi_notes, velocities, durations)
                        transmission_count += 1
                        
                        # 🎙️ 악보 녹음
                        if score_recorder.is_recording:
                            score_recorder.add_notes(frame_count, midi_notes, velocities, durations, 
                                                   raw_roi_for_record,
                                                   zodiac_info['section'] if zodiac_info else None)
                        
                        # 📊 콘솔 로그 (10번마다)
                        if transmission_count % 10 == 0:
                            print(f"📡 #{transmission_count} 전송: {len(midi_notes)}개 노트 (평균 vel: {np.mean(velocities):.1f})")
                    
                except Exception as e:
                    print(f"⚠️ MIDI 처리 오류: {e}")
            
            # 🔄 바퀴 완료 확인 (악보 녹음)
            if score_recorder.is_recording:
                if score_recorder.check_rotation_complete(frame_count):
                    # 녹음이 완료되면(True 반환), 메시지 출력
                    # 저장은 클래스 내부에서 모두 처리됨
                    print("🎼 모든 악보 저장 절차가 완료되었습니다.")
            
            frame_count += 1
            fps_frames += 1
            
            # 📊 FPS 계산 (실시간)
            current_time = time.time()
            if current_time - last_fps_time >= 1.0:  # 1초마다 FPS 계산
                current_fps = fps_frames / (current_time - last_fps_time)
                fps_frames = 0
                last_fps_time = current_time
            
            # ⌨️ 키 입력 처리
            key = cv.waitKey(1) & 0xFF
            if key == 27:  # ESC
                print("👋 사용자가 종료했습니다.")
                break
            elif key == ord('s'):  # 's' 키로 스케일 변경
                scales = SCALES.keys()
                current_idx = scales.index(args.scale) if args.scale in scales else 0
                args.scale = scales[(current_idx + 1) % len(scales)]
                print(f"🎼 스케일 변경: {args.scale}")
            elif key == ord('f'):  # 'f' 키로 전체 화면 토글
                show_full_frame = not show_full_frame
                if not show_full_frame:
                    cv.destroyWindow('Webcam Full View')
                print(f"📺 전체 화면 표시: {'ON' if show_full_frame else 'OFF'}")
            elif key == ord('r'):  # 'r' 키로 ROI 재선택
                print("🖱️ ROI 재선택...")
                if current_roi_mode == "circular":
                    # 원형 ROI 재설정
                    center_x, center_y, spindle_radius = detect_center_spindle(vertical_frame)
                    corners = [
                        (0, 0), (vertical_frame.shape[1], 0),
                        (0, vertical_frame.shape[0]), (vertical_frame.shape[1], vertical_frame.shape[0])
                    ]
                    max_radius = 0
                    for corner_x, corner_y in corners:
                        dist = np.sqrt((corner_x - center_x)**2 + (corner_y - center_y)**2)
                        max_radius = max(max_radius, dist)
                    scan_radius = max_radius - spindle_radius - 20
                    roi_coords = (center_x, center_y, int(scan_radius))
                    print(f"🎯 새 원형 ROI: 중심({center_x}, {center_y}), 반지름 {scan_radius}")
                else:
                    # 직사각형 ROI 재선택
                    scale_percent = 20
                    width = int(vertical_frame.shape[1] * scale_percent / 100)
                    height = int(vertical_frame.shape[0] * scale_percent / 100)
                    resized_frame = cv.resize(vertical_frame, (width, height))
                    
                    new_x, new_y, new_w, new_h = cv.selectROI('ROI 재선택', resized_frame, False)
                    
                    # 원본 크기로 스케일링
                    x = int(new_x / (scale_percent/100))
                    y = int(new_y / (scale_percent/100))
                    w = int(new_w / (scale_percent/100))
                    h = int(new_h / (scale_percent/100))
                    
                    roi_coords = (x, y, w, h)
                    cv.destroyWindow('ROI 재선택')
                    print(f"🎯 새 직사각형 ROI: x={x}, y={y}, w={w}, h={h}")
            elif key == ord('m'):  # 'm' 키로 ROI 모드 변경
                current_roi_mode = "circular" if current_roi_mode == "rectangular" else "rectangular"
                print(f"🔄 ROI 모드 변경: {current_roi_mode}")
                
                # 모드 변경시 ROI 재설정
                if current_roi_mode == "circular":
                    center_x, center_y, spindle_radius = detect_center_spindle(vertical_frame)
                    corners = [
                        (0, 0), (vertical_frame.shape[1], 0),
                        (0, vertical_frame.shape[0]), (vertical_frame.shape[1], vertical_frame.shape[0])
                    ]
                    max_radius = 0
                    for corner_x, corner_y in corners:
                        dist = np.sqrt((corner_x - center_x)**2 + (corner_y - center_y)**2)
                        max_radius = max(max_radius, dist)
                    scan_radius = max_radius - spindle_radius - 20
                    roi_coords = (center_x, center_y, int(scan_radius))
                    print(f"🎯 원형 ROI 설정: 중심({center_x}, {center_y}), 반지름 {scan_radius}")
                else:
                    # 직사각형 모드로 변경
                    x = vertical_frame.shape[1] // 2
                    y = 50
                    w = 1
                    h = min(88 * 10, vertical_frame.shape[0] - y - 50)
                    roi_coords = (x, y, w, h)
                    print(f"🎯 직사각형 ROI 설정: x={x}, y={y}, w={w}, h={h}")
            elif key == ord('p'):  # 'p' 키로 재생 모드 토글
                if score_recorder.score_data['rotations']:
                    playback_mode = not playback_mode
                    print(f"🎵 재생 모드: {'ON' if playback_mode else 'OFF'}")
                else:
                    print("⚠️ 재생할 악보가 없습니다. 먼저 녹음하거나 --load_score 옵션으로 불러오세요.")
            elif key == ord('d'): # 'd' 키로 회전 감지 기준 재설정
                if rpm_detector:
                    ret, frame = cap.read()
                    if ret:
                        rotated_frame = cv.rotate(frame, cv.ROTATE_90_CLOCKWISE)
                        rpm_detector.set_reference_frame(rotated_frame)
                    else:
                        print("⚠️ 기준 프레임 재설정을 위한 프레임 획득 실패")
                else:
                    print("⚠️ RPM 감지 모드가 활성화되지 않았습니다.")

    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        
    finally:
        # 🧹 정리
        if 'cap' in locals():
            cap.release()
        cv.destroyAllWindows()
        print("✅ 정리 완료")


if __name__ == "__main__":
    main() 