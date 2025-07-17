#!/usr/bin/env python3
"""
🎵 CORE AUDIO PROCESSING MODULE 🎵
=====================================
현재 Audible Garden Turntable 시스템의 핵심 데이터 플로우 분석 및 정리

📊 데이터 플로우: 웹캠 → 음악 데이터 변환
1. 카메라 입력 (BGR 프레임)
2. ROI 추출 (직사각형 영역)
3. Grayscale 변환
4. 픽셀 값 → 음악 데이터 매핑
5. OSC/MIDI 전송

Author: Code Analysis & Cleanup
Date: 2025-01-08
"""

import cv2
import numpy as np
import pandas as pd
from pythonosc import udp_client
from utils.audio_utils import select_scale, ValMapper


class AudioProcessor:
    """
    🎹 오디오 처리 클래스
    웹캠 픽셀 데이터를 실시간 MIDI 데이터로 변환하는 핵심 로직
    """
    
    def __init__(self, scale='CPentatonic', osc_port=5555):
        """
        초기화
        
        Args:
            scale (str): 사용할 음계 ('piano', 'CMajor', 'CPentatonic', 'CLydian', 'CWhole')
            osc_port (int): OSC 전송 포트 번호
        """
        # 🎼 음계 설정
        self.note_midis = select_scale(scale)
        self.num_notes = len(self.note_midis)
        
        # 🎯 처리 매개변수
        self.vel_min = 32        # 최소 벨로시티
        self.vel_max = 127       # 최대 벨로시티  
        self.dur_min = 0.8       # 최소 지속시간
        self.dur_max = 1.8       # 최대 지속시간
        
        # 🌟 Zodiac 모드 매개변수
        self.zodiac_mode = True
        self.zodiac_range = 88   # Zodiac 구간당 픽셀 수
        self.time_per_zodiac = 30  # 구간당 시간(초)
        
        # 📡 OSC 클라이언트 초기화
        self.osc_client = udp_client.SimpleUDPClient("127.0.0.1", osc_port)
        self.osc_port = osc_port
        
        print(f"🎵 AudioProcessor 초기화 완료")
        print(f"   - 음계: {scale} ({self.num_notes}개 노트)")
        print(f"   - OSC 포트: {osc_port}")
        print(f"   - Zodiac 모드: {'활성화' if self.zodiac_mode else '비활성화'}")


    def extract_roi_pixels(self, frame, roi_coords, frame_count=0, fps=30):
        """
        📐 ROI에서 픽셀 값 추출 (현재 구현 방식)
        
        현재 시스템은 직사각형 ROI를 처리합니다.
        향후 원형 ROI 처리로 업그레이드 필요.
        
        Args:
            frame: BGR 컬러 프레임
            roi_coords: (x, y, w, h) 직사각형 ROI 좌표
            frame_count: 현재 프레임 번호 (Zodiac 모드용)
            fps: 초당 프레임 수
            
        Returns:
            roi_gray: Grayscale ROI 이미지
            processing_region: 실제 처리할 영역의 좌표
        """
        x, y, w, h = roi_coords
        
        # 🔄 프레임 회전 (현재 시스템은 90도 회전 적용)
        vertical_frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
        
        if self.zodiac_mode:
            # 🌟 Zodiac 모드: 12개 구간 중 현재 시간에 해당하는 구간 선택
            hour_frame = fps * self.time_per_zodiac  # 구간당 프레임 수
            hour_idx = (frame_count // hour_frame) % 12  # 현재 구간 (0-11)
            
            # 현재 구간의 시작 위치 계산
            zodiac_y = y + hour_idx * self.zodiac_range
            zodiac_h = self.zodiac_range
            
            # ROI 추출
            roi = vertical_frame[zodiac_y:zodiac_y+zodiac_h, x:x+1]  # 1픽셀 너비
            processing_region = (x, zodiac_y, 1, zodiac_h)
            
            print(f"🌟 Zodiac 모드: 구간 {hour_idx+1}/12 처리중")
            
        else:
            # 📊 일반 모드: 전체 ROI 처리
            roi = vertical_frame[y:y+h, x:x+1]  # 1픽셀 너비
            processing_region = (x, y, 1, h)
        
        # 🎨 Grayscale 변환
        if roi.size == 0:
            raise ValueError(f"❌ 유효하지 않은 ROI: {processing_region}")
            
        roi_gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        
        return roi_gray, processing_region


    def pixels_to_magnitudes(self, roi_gray, processing_mode='zodiac'):
        """
        🔢 픽셀 값을 음악적 크기(magnitude) 배열로 변환
        
        Args:
            roi_gray: Grayscale ROI 이미지
            processing_mode: 'zodiac' 또는 'normal'
            
        Returns:
            magnitudes: 각 음표에 해당하는 크기 값 배열
            raw_data: 원본 픽셀 데이터 (디버깅용)
        """
        if processing_mode == 'zodiac':
            # 🌟 Zodiac 모드: zodiac_range 픽셀을 처리
            num_pixels = self.zodiac_range
            target_area_size = 1  # 현재는 1픽셀씩 처리
        else:
            # 📊 일반 모드: 음표 수에 맞춰 분할
            num_pixels = roi_gray.shape[0]
            target_area_size = num_pixels // self.num_notes
        
        # 📋 픽셀 데이터 추출
        data = []
        magnitudes = []
        
        if processing_mode == 'zodiac':
            # Zodiac: 각 픽셀을 개별 처리
            for pixel_idx in range(num_pixels):
                pixel_start = pixel_idx * target_area_size
                pixel_end = (pixel_idx + 1) * target_area_size
                
                # 해당 영역의 평균값 계산
                pixel_region = roi_gray[pixel_start:pixel_end, :]
                magnitude = np.mean(pixel_region) if pixel_region.size > 0 else 0
                
                magnitudes.append(magnitude)
                data.append({
                    'pixel_index': pixel_idx,
                    'magnitude': magnitude,
                    'region': (pixel_start, pixel_end)
                })
        else:
            # 일반 모드: 음표 수에 맞춰 구간 분할
            for note_idx in range(self.num_notes):
                note_start = note_idx * target_area_size
                note_end = (note_idx + 1) * target_area_size
                
                note_region = roi_gray[note_start:note_end, :]
                magnitude = np.mean(note_region) if note_region.size > 0 else 0
                
                magnitudes.append(magnitude)
                data.append({
                    'note_index': note_idx,
                    'midi_note': self.note_midis[note_idx],
                    'magnitude': magnitude,
                    'region': (note_start, note_end)
                })
        
        print(f"📊 {len(magnitudes)}개 크기 값 추출 완료 (모드: {processing_mode})")
        
        return np.array(magnitudes), data


    def magnitudes_to_midi(self, magnitudes, add_variation=True):
        """
        🎹 크기 값을 MIDI 벨로시티와 지속시간으로 변환
        
        Args:
            magnitudes: 픽셀 크기 값 배열
            add_variation: 음악적 다양성을 위한 랜덤 변화 추가 여부
            
        Returns:
            velocities: MIDI 벨로시티 배열 (32-127)
            durations: 음표 지속시간 배열
            notes: MIDI 노트 번호 배열
        """
        # 🎵 벨로시티 매핑 (선형)
        vel_mapper = ValMapper(
            mode='linear',
            value=magnitudes,
            min_value=magnitudes.min(),
            max_value=magnitudes.max(),
            min_bound=self.vel_min,
            max_bound=self.vel_max
        )
        velocities = vel_mapper()
        
        # 🎼 지속시간 매핑 (변화를 위해 약간의 랜덤성 추가)
        if add_variation:
            light_bound = 20
            lightness = np.random.randint(-light_bound, light_bound, len(magnitudes))
            varied_magnitudes = magnitudes + lightness
        else:
            varied_magnitudes = magnitudes
            
        dur_mapper = ValMapper(
            mode='linear',
            value=varied_magnitudes,
            min_value=varied_magnitudes.min(),
            max_value=varied_magnitudes.max(),
            min_bound=self.dur_min,
            max_bound=self.dur_max
        )
        durations = dur_mapper()
        
        # 🎹 MIDI 노트 배열 (현재는 전체 스케일 사용)
        notes = self.note_midis
        
        # 📊 값 정리 (소수점 1자리)
        velocities = [round(float(v), 1) for v in velocities]
        durations = [round(float(d), 1) for d in durations]
        
        print(f"🎹 MIDI 변환 완료: {len(notes)}개 노트")
        print(f"   - 벨로시티 범위: {min(velocities):.1f} ~ {max(velocities):.1f}")
        print(f"   - 지속시간 범위: {min(durations):.1f} ~ {max(durations):.1f}")
        
        return velocities, durations, notes


    def send_osc_data(self, notes, velocities, durations, mode_info=""):
        """
        📡 OSC를 통해 음악 데이터 전송
        
        Args:
            notes: MIDI 노트 번호 배열
            velocities: 벨로시티 배열  
            durations: 지속시간 배열
            mode_info: 추가 정보 (로그용)
        """
        try:
            # 📤 OSC 메시지 전송
            self.osc_client.send_message('/note', notes)
            self.osc_client.send_message('/velocity', velocities)
            self.osc_client.send_message('/duration', durations)
            
            # 📝 로그 출력
            note_vel_pairs = [f"{n}:{v}" for n, v in zip(notes[:5], velocities[:5])]  # 처음 5개만
            log_msg = f"📡 OSC [{self.osc_port}] - {mode_info} | "
            log_msg += f"Notes: {', '.join(note_vel_pairs)}{'...' if len(notes) > 5 else ''} | "
            log_msg += f"Duration: {durations[0]:.1f}s"
            
            print(log_msg)
            
        except Exception as e:
            print(f"❌ OSC 전송 실패: {e}")


    def process_frame_to_audio(self, frame, roi_coords, frame_count=0, fps=30):
        """
        🎵 완전한 처리 파이프라인: 프레임 → 음악 데이터
        
        Args:
            frame: 카메라 프레임
            roi_coords: ROI 좌표
            frame_count: 프레임 번호
            fps: 초당 프레임 수
        """
        try:
            # 1️⃣ ROI 픽셀 추출
            roi_gray, processing_region = self.extract_roi_pixels(
                frame, roi_coords, frame_count, fps
            )
            
            # 2️⃣ 픽셀 → 크기 값 변환
            processing_mode = 'zodiac' if self.zodiac_mode else 'normal'
            magnitudes, raw_data = self.pixels_to_magnitudes(roi_gray, processing_mode)
            
            # 3️⃣ 크기 값 → MIDI 변환
            velocities, durations, notes = self.magnitudes_to_midi(magnitudes)
            
            # 4️⃣ OSC 전송
            mode_info = ""
            if self.zodiac_mode:
                hour_idx = (frame_count // (fps * self.time_per_zodiac)) % 12
                mode_info = f"zodiac[{hour_idx+1}/12]"
            else:
                mode_info = "full"
                
            self.send_osc_data(notes, velocities, durations, mode_info)
            
            return {
                'success': True,
                'processing_region': processing_region,
                'magnitudes': magnitudes,
                'notes': notes,
                'velocities': velocities,
                'durations': durations,
                'mode': mode_info
            }
            
        except Exception as e:
            print(f"❌ 프레임 처리 실패: {e}")
            return {'success': False, 'error': str(e)}


# 🧪 테스트용 함수들
def test_audio_processor():
    """AudioProcessor 클래스 테스트"""
    processor = AudioProcessor(scale='CPentatonic', osc_port=5555)
    
    # 더미 데이터로 테스트
    dummy_frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    dummy_roi = (100, 100, 50, 200)  # x, y, w, h
    
    result = processor.process_frame_to_audio(dummy_frame, dummy_roi, frame_count=0)
    
    if result['success']:
        print("✅ 테스트 성공!")
        print(f"   - 처리 영역: {result['processing_region']}")
        print(f"   - 모드: {result['mode']}")
    else:
        print(f"❌ 테스트 실패: {result['error']}")


if __name__ == "__main__":
    test_audio_processor() 