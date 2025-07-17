#!/usr/bin/env python3
"""
🎵 SIMPLE AUDIO UTILS - audiolazy 없는 버전
==========================================
audiolazy 의존성 없이 기본적인 음악 기능 제공

Author: Temporary Solution
Date: 2025-01-08
"""
import time
import random
import numpy as np
from pythonosc import udp_client


class ValMapper:
    """
    🎛️ 값 매핑 클래스 (audiolazy.ValMapper 대체)
    """
    
    def __init__(self, mode, input_values, input_min, input_max, output_min, output_max):
        """
        초기화
        
        Args:
            mode (str): 매핑 모드 ('linear')
            input_values: 입력 값들
            input_min: 입력 최소값
            input_max: 입력 최대값  
            output_min: 출력 최소값
            output_max: 출력 최대값
        """
        self.mode = mode
        self.input_values = np.array(input_values)
        self.input_min = input_min
        self.input_max = input_max
        self.output_min = output_min
        self.output_max = output_max
    
    def __call__(self):
        """
        매핑 실행
        
        Returns:
            np.array: 매핑된 값들
        """
        if self.mode == 'linear':
            # 선형 매핑: (x - input_min) / (input_max - input_min) * (output_max - output_min) + output_min
            input_range = self.input_max - self.input_min
            output_range = self.output_max - self.output_min
            
            if input_range == 0:
                # 입력 범위가 0인 경우 중간값 반환
                return np.full_like(self.input_values, (self.output_min + self.output_max) / 2)
            
            normalized = (self.input_values - self.input_min) / input_range
            mapped = normalized * output_range + self.output_min
            
            # 출력 범위 제한
            mapped = np.clip(mapped, self.output_min, self.output_max)
            
            return mapped
        else:
            raise ValueError(f"지원하지 않는 매핑 모드: {self.mode}")


def init_client(ip="127.0.0.1", port=5555):
    """
    📡 OSC 클라이언트 초기화
    
    Args:
        ip (str): OSC 서버 IP
        port (int): OSC 서버 포트
        
    Returns:
        SimpleUDPClient: OSC 클라이언트
    """
    try:
        client = udp_client.SimpleUDPClient(ip, port)
        print(f"📡 OSC 클라이언트 초기화 완료: {ip}:{port}")
        return client
    except Exception as e:
        print(f"❌ OSC 클라이언트 초기화 실패: {e}")
        return None


def send_midi(client, midi_notes, velocities, durations):
    """
    🎵 MIDI 데이터를 OSC로 전송
    
    Args:
        client: OSC 클라이언트
        midi_notes (list): MIDI 노트 번호들
        velocities (list): 벨로시티 값들
        durations (list): 지속시간 값들
    """
    if client is None:
        print("❌ OSC 클라이언트가 초기화되지 않음")
        return
    
    try:
        # 📊 데이터 검증
        actual_notes = min(len(midi_notes), len(velocities), len(durations))
        
        if actual_notes == 0:
            print("⚠️ 전송할 MIDI 데이터가 없음")
            return

        # 📡 OSC 메시지 전송
        for i in range(len(midi_notes)):
            note = int(midi_notes[i])
            velocity = int(velocities[i])
            duration = int(durations[i])
            
            # OSC 메시지 전송
            client.send_message("/note", note)
            client.send_message("/velocity", velocity)  
            client.send_message("/duration", duration)
            time.sleep(0.5)
        print(f"📡 OSC 전송 완료: {len(midi_notes)}개 노트")
        time.sleep(3)
        
    except Exception as e:
        print(f"❌ OSC 전송 오류: {e}")


def str2midi(note_str):
    """
    🎵 노트 문자열을 MIDI 번호로 변환 (간단한 버전)
    
    Args:
        note_str (str): 노트 문자열 (예: 'C4', 'A#3')
        
    Returns:
        int: MIDI 노트 번호
    """
    # 간단한 구현 (C4 = 60)
    note_map = {'C': 0, 'C#': 1, 'D': 2, 'D#': 3, 'E': 4, 'F': 5, 
                'F#': 6, 'G': 7, 'G#': 8, 'A': 9, 'A#': 10, 'B': 11}
    
    if len(note_str) < 2:
        return 60  # 기본값 C4
    
    note_name = note_str[:-1]
    octave = int(note_str[-1])
    
    if note_name in note_map:
        midi_note = note_map[note_name] + (octave + 1) * 12
        return max(0, min(127, midi_note))
    
    return 60  # 기본값


def generate_midi_from_roi(roi_gray, config):
    """
    🎹 설정 파일(config)을 기반으로 ROI 픽셀을 MIDI 데이터로 변환합니다.
    '세로축=음높이, 밝기=세기' 모델을 사용하며, 밝기 반전 및 샘플링 모드를 지원합니다.
    """
    # --- 0. 입력 유효성 검사 ---
    if not isinstance(roi_gray, np.ndarray) or roi_gray.size == 0:
        return [], [], [] # 유효하지 않은 입력이면 즉시 빈 값 반환

    # --- 1. 설정값 불러오기 ---
    gen_config = config.get('midi_generation', {})
    sampling_mode = gen_config.get('sampling_mode', 'importance')
    note_count_max = gen_config.get('note_count_max', 5)
    vel_range = gen_config.get('velocity_range', [32, 127])
    vel_threshold = gen_config.get('velocity_threshold', 32)
    # fixed_duration = gen_config.get('fixed_duration_seconds', 1.5)

    scale_config = config.get('scales', {})
    scale_name = scale_config.get('default_scale', 'Piano')
    
    # config에서 직접 스케일 정의 가져오기
    definitions = scale_config.get('definitions', {})
    if scale_name == 'Piano':
        try:
            scale_notes = list(eval(definitions.get('Piano', 'list(range(21, 109))')))
        except:
            scale_notes = list(range(21, 109))
    else:
        scale_notes = definitions.get(scale_name, list(range(21, 109)))

    # --- 2. 입력 ROI 처리 (밝기 반전 및 정규화) ---
    # 요청사항: 검은색(0)이 높은 값(255)이 되도록 밝기 반전
    roi_inverted = 255 - roi_gray

    # --- 최종 방어 코드 ---
    # cv.resize가 요구하는 uint8 타입으로 명시적 변환
    if roi_inverted.dtype != np.uint8:
        roi_inverted = roi_inverted.astype(np.uint8)

    if roi_inverted.shape[0] != 88:
        import cv2 as cv
        # 리사이즈 직전 shape 확인
        # print(f"--- Resizing from shape: {roi_inverted.shape}, dtype: {roi_inverted.dtype}")
        roi_normalized = cv.resize(roi_inverted, (roi_inverted.shape[1], 88), interpolation=cv.INTER_LINEAR)
    else:
        roi_normalized = roi_inverted
    
    # 각 88개 행의 평균 밝기(반전된 값) 계산
    magnitudes = np.mean(roi_normalized, axis=1)

    # --- 3. '가상 키보드' 매핑 및 연주 후보 선정 ---
    
    # 88개 행 인덱스(0-87)를 전체 피아노 음역(21-108)에 매핑
    piano_notes = np.arange(108, 20, -1) # 108, 107, ..., 21 (세로 위쪽이 높은 음)

    # 피아노 음역을 사용하는 음계의 노트에 매핑
    available_scale_notes = sorted([n for n in piano_notes if n in scale_notes], reverse=True)
    if not available_scale_notes: # 스케일에 해당하는 노트가 없으면 빈 값 반환
        return [], [], []

    # 연주 후보 리스트 생성: (MIDI 노트, 벨로시티)
    candidates = []
    for i in range(88): # 88개 모든 행에 대해
        # i번째 행이 어떤 음계의 음에 해당하는지 찾기
        # (가장 가까운 음계의 음을 찾는 방식으로 근사치 매핑)
        note_index = np.abs(np.array(available_scale_notes) - piano_notes[i]).argmin()
        mapped_note = available_scale_notes[note_index]

        # 밝기를 벨로시티로 변환
        velocity = np.interp(magnitudes[i], [100, 255], vel_range)
        
        # 벨로시티가 임계값을 넘으면 후보에 추가
        if velocity >= vel_threshold:
            # 중복된 음이 추가되지 않도록 확인
            if not any(c[0] == mapped_note for c in candidates):
                 candidates.append((mapped_note, velocity))

    if not candidates:
        return [], [], []

    # --- 4. 최종 노트 선택 (샘플링 모드에 따라 분기) ---
    final_notes = []
    if sampling_mode == 'random':
        # 후보 중에서 무작위로 N개 선택
        random.shuffle(candidates)
        final_notes = candidates[:note_count_max]
    else: # 'importance' 모드가 기본
        # 벨로시티(밝기)가 높은 순으로 정렬하여 N개 선택
        candidates.sort(key=lambda x: x[1], reverse=True)
        final_notes = candidates[:note_count_max]

    # --- 5. 최종 데이터 생성 ---
    output_notes = [int(n[0]) for n in final_notes]
    output_velocities = [int(n[1]) for n in final_notes]
    output_durations = [random.uniform(500, 3000) for i in range(len(output_notes))]
    # output_durations = [fixed_duration] * len(output_notes) # 고정된 duration 적용

    return output_notes, output_velocities, output_durations


def process_roi_to_midi_data(*args, **kwargs):
    """
    [DEPRECATED] 이 함수는 더 이상 사용되지 않습니다.
    대신 `generate_midi_from_roi` 함수와 `config.json`을 사용하세요.
    """
    raise DeprecationWarning(
        "`process_roi_to_midi_data` is deprecated. "
        "Use `generate_midi_from_roi` with a config object instead."
    ) 