#!/usr/bin/env python3
"""
🎵 CORRECTED AUDIO PROCESSING MODULE 🎵
==========================================
RPM과 시간 관계 수정 및 변수 의존성 정리

📊 올바른 변수 관계:
- 한 바퀴 시간 = 60/RPM (초)
- Zodiac 구간당 시간 = (60/RPM)/12 = 5/RPM (초)  
- 구간당 프레임 수 = fps * (5/RPM)

Author: Code Review & Correction
Date: 2025-01-08
"""

import cv2
import numpy as np
from pythonosc import udp_client
from utils.audio_utils import select_scale, ValMapper


class CorrectedAudioProcessor:
    """
    🎹 수정된 오디오 처리 클래스
    RPM과 시간 관계를 올바르게 반영한 처리 로직
    """
    
    def __init__(self, scale='CPentatonic', osc_port=5555, rpm=2.5, fps=None):
        """
        초기화
        
        Args:
            scale (str): 사용할 음계
            osc_port (int): OSC 전송 포트 번호
            rpm (float): 원판 회전 속도 (2-3 RPM 범위)
            fps (float): 카메라 FPS (None이면 자동 감지)
        """
        # 🎼 음계 설정
        self.note_midis = select_scale(scale)
        self.num_notes = len(self.note_midis)
        
        # ⚙️ 회전 매개변수
        self.rpm = rpm
        self.fps = fps  # 실제 카메라에서 감지
        
        # ⏱️ 시간 계산 (RPM 기반)
        self.rotation_time = 60.0 / self.rpm  # 한 바퀴 시간 (초)
        self.zodiac_section_time = self.rotation_time / 12  # 구간당 시간 (초)
        
        # 🎯 처리 매개변수
        self.vel_min = 32
        self.vel_max = 127
        self.dur_min = 0.8
        self.dur_max = 1.8
        
        # 🌟 Zodiac 모드 매개변수
        self.zodiac_mode = True
        self.zodiac_range = 88   # 88개 픽셀 → 88개 MIDI 노트 (의도된 설계)
        
        # 📡 OSC 클라이언트
        self.osc_client = udp_client.SimpleUDPClient("127.0.0.1", osc_port)
        self.osc_port = osc_port
        
        print(f"🎵 CorrectedAudioProcessor 초기화 완료")
        print(f"   - 음계: {scale} ({self.num_notes}개 노트)")
        print(f"   - RPM: {self.rpm} (한 바퀴: {self.rotation_time:.1f}초)")
        print(f"   - Zodiac 구간당: {self.zodiac_section_time:.1f}초")
        print(f"   - OSC 포트: {osc_port}")


    def update_fps_dependent_values(self, actual_fps):
        """
        📹 실제 FPS가 확인된 후 FPS 의존 변수들 업데이트
        
        Args:
            actual_fps (float): 실제 카메라 FPS
        """
        self.fps = actual_fps
        
        # 📊 FPS 기반 계산
        self.frames_per_rotation = int(self.fps * self.rotation_time)  # 한 바퀴당 프레임 수
        self.frames_per_zodiac_section = int(self.fps * self.zodiac_section_time)  # 구간당 프레임 수
        
        print(f"📹 FPS 의존 변수 업데이트:")
        print(f"   - 실제 FPS: {self.fps:.1f}")
        print(f"   - 한 바퀴당 프레임: {self.frames_per_rotation}")
        print(f"   - Zodiac 구간당 프레임: {self.frames_per_zodiac_section}")


    def calculate_current_position(self, frame_count):
        """
        🧭 현재 프레임에서의 회전 위치 계산
        
        Args:
            frame_count (int): 현재 프레임 번호
            
        Returns:
            rotation_progress (float): 현재 회전 진행률 (0.0-1.0)
            zodiac_section (int): 현재 Zodiac 구간 (0-11)
            angle_degrees (float): 현재 각도 (0-360도)
        """
        if not hasattr(self, 'frames_per_rotation'):
            # FPS가 아직 설정되지 않은 경우 기본값 사용
            estimated_fps = 30
            self.update_fps_dependent_values(estimated_fps)
        
        # 🔄 회전 진행률 계산
        frames_in_current_rotation = frame_count % self.frames_per_rotation
        rotation_progress = frames_in_current_rotation / self.frames_per_rotation
        
        # 🌟 Zodiac 구간 계산
        zodiac_section = (frame_count // self.frames_per_zodiac_section) % 12
        
        # 📐 각도 계산
        angle_degrees = rotation_progress * 360
        
        return rotation_progress, zodiac_section, angle_degrees


    def extract_roi_pixels_rectangular(self, frame, roi_coords, frame_count=0):
        """
        📐 직사각형 ROI 픽셀 추출 (기존 모드 유지)
        
        Args:
            frame: BGR 컬러 프레임
            roi_coords: (x, y, w, h) 직사각형 ROI 좌표
            frame_count: 현재 프레임 번호
            
        Returns:
            roi_gray: Grayscale ROI 이미지
            processing_info: 처리 정보
        """
        x, y, w, h = roi_coords
        
        # 🔄 프레임 회전
        vertical_frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
        
        if self.zodiac_mode:
            # 🌟 Zodiac 모드: 현재 구간 계산
            _, zodiac_section, angle = self.calculate_current_position(frame_count)
            
            # 현재 구간의 시작 위치
            zodiac_y = y + zodiac_section * self.zodiac_range
            zodiac_h = self.zodiac_range
            
            # ROI 추출 (1픽셀 너비로 스캔라인 방식)
            roi = vertical_frame[zodiac_y:zodiac_y+zodiac_h, x:x+1]
            processing_region = (x, zodiac_y, 1, zodiac_h)
            
            processing_info = {
                'mode': 'zodiac_rectangular',
                'section': zodiac_section + 1,
                'angle': angle,
                'region': processing_region
            }
            
        else:
            # 📊 일반 모드: 전체 ROI
            roi = vertical_frame[y:y+h, x:x+1]
            processing_region = (x, y, 1, h)
            
            processing_info = {
                'mode': 'full_rectangular',
                'region': processing_region
            }
        
        # 🎨 Grayscale 변환
        if roi.size == 0:
            raise ValueError(f"❌ 유효하지 않은 ROI: {processing_region}")
            
        roi_gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        
        return roi_gray, processing_info


    def extract_roi_pixels_circular(self, frame, center_coords, radius, frame_count=0):
        """
        🎯 원형 ROI 반지름 스캔라인 추출 (새로운 모드)
        
        LP 턴테이블처럼 원판 중심에서 바깥쪽으로 반지름 방향 스캔
        
        Args:
            frame: BGR 컬러 프레임  
            center_coords: (center_x, center_y) 원판 중심 좌표
            radius: 스캔할 반지름 (픽셀 단위)
            frame_count: 현재 프레임 번호
            
        Returns:
            radial_scanline: 반지름 방향 1차원 스캔라인 (Grayscale)
            processing_info: 처리 정보
        """
        center_x, center_y = center_coords
        
        # 🧭 현재 각도 계산
        _, zodiac_section, angle_degrees = self.calculate_current_position(frame_count)
        angle_radians = np.radians(angle_degrees)
        
        # 🎨 Grayscale 변환
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # 📏 반지름 방향 스캔라인 좌표 계산
        radial_points = []
        scanline_values = []
        
        for r in range(radius):
            # 극좌표 → 직교좌표 변환
            x = int(center_x + r * np.cos(angle_radians))
            y = int(center_y + r * np.sin(angle_radians))
            
            # 이미지 경계 확인
            if 0 <= x < gray_frame.shape[1] and 0 <= y < gray_frame.shape[0]:
                pixel_value = gray_frame[y, x]
                scanline_values.append(pixel_value)
                radial_points.append((x, y))
            else:
                scanline_values.append(0)  # 경계 밖은 0으로 처리
                radial_points.append((x, y))
        
        radial_scanline = np.array(scanline_values, dtype=np.uint8)
        
        processing_info = {
            'mode': 'radial_circular', 
            'angle': angle_degrees,
            'center': center_coords,
            'radius': radius,
            'points': radial_points[:10],  # 처음 10개 점만 저장 (디버깅용)
            'section': zodiac_section + 1 if self.zodiac_mode else None
        }
        
        return radial_scanline, processing_info


    def pixels_to_midi_88_mapping(self, pixel_data, selected_scale=None):
        """
        🎹 88개 픽셀 → MIDI 노트 매핑 (의도된 설계 유지)
        
        Args:
            pixel_data: 픽셀 값 배열 (88개 또는 그보다 적음)
            selected_scale: 사용할 스케일 (None이면 전체 piano 범위)
            
        Returns:
            notes: MIDI 노트 번호 배열
            velocities: 벨로시티 배열
            durations: 지속시간 배열
        """
        # 📊 88개로 패딩 또는 자르기
        if len(pixel_data) < 88:
            # 부족한 경우 0으로 패딩
            padded_data = np.pad(pixel_data, (0, 88 - len(pixel_data)), mode='constant', constant_values=0)
        else:
            # 넘치는 경우 88개로 자르기
            padded_data = pixel_data[:88]
        
        # 🎹 MIDI 노트 범위 (21-108, 총 88개)
        all_midi_notes = list(range(21, 109))
        
        if selected_scale and selected_scale != 'piano':
            # 🎼 특정 스케일을 사용하는 경우, 해당 노트만 선택
            scale_notes = select_scale(selected_scale)
            
            # 88개 중에서 스케일에 해당하는 노트만 활성화
            notes = []
            velocities = []
            
            for i, midi_note in enumerate(all_midi_notes):
                if midi_note in scale_notes:
                    # 스케일에 포함된 노트
                    notes.append(midi_note)
                    
                    # 벨로시티 매핑
                    pixel_value = padded_data[i]
                    velocity = int(self.vel_min + (pixel_value / 255.0) * (self.vel_max - self.vel_min))
                    velocities.append(velocity)
        else:
            # 🎹 전체 88개 노트 사용
            notes = all_midi_notes
            velocities = []
            
            for pixel_value in padded_data:
                velocity = int(self.vel_min + (pixel_value / 255.0) * (self.vel_max - self.vel_min))
                velocities.append(velocity)
        
        # 🎼 지속시간 (모든 노트 동일)
        durations = [1.0] * len(notes)
        
        print(f"🎹 MIDI 매핑: {len(notes)}개 노트 (스케일: {selected_scale or 'piano'})")
        
        return notes, velocities, durations


# 📊 변수 관계 요약 함수
def print_variable_relationships(rpm, fps):
    """
    📋 RPM과 FPS에 따른 모든 변수 관계 출력
    """
    print("🔢 변수 관계 요약:")
    print(f"📐 기본 설정:")
    print(f"   - RPM: {rpm}")
    print(f"   - FPS: {fps}")
    print()
    
    # ⏱️ 시간 관계
    rotation_time = 60.0 / rpm
    zodiac_section_time = rotation_time / 12
    
    print(f"⏱️ 시간 관계:")
    print(f"   - 한 바퀴 시간: 60/{rpm} = {rotation_time:.2f}초")
    print(f"   - Zodiac 구간당: {rotation_time:.2f}/12 = {zodiac_section_time:.2f}초")
    print()
    
    # 📊 프레임 관계
    frames_per_rotation = int(fps * rotation_time)
    frames_per_section = int(fps * zodiac_section_time)
    
    print(f"📊 프레임 관계:")
    print(f"   - 한 바퀴당 프레임: {fps} × {rotation_time:.2f} = {frames_per_rotation}")
    print(f"   - 구간당 프레임: {fps} × {zodiac_section_time:.2f} = {frames_per_section}")
    print()
    
    # 🎯 각도 관계
    degrees_per_frame = 360 / frames_per_rotation
    degrees_per_section = 360 / 12
    
    print(f"🎯 각도 관계:")
    print(f"   - 프레임당 각도: 360/{frames_per_rotation} = {degrees_per_frame:.2f}도")
    print(f"   - 구간당 각도: 360/12 = {degrees_per_section:.1f}도")


if __name__ == "__main__":
    # 🧪 변수 관계 테스트
    print_variable_relationships(rpm=2.5, fps=30)
    print("="*50)
    print_variable_relationships(rpm=3.0, fps=60) 