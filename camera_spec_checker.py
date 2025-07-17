#!/usr/bin/env python3
"""
📹 CAMERA SPECIFICATION CHECKER 📹
====================================
실제 연결된 카메라의 스펙을 확인하는 유틸리티

- 해상도 (지원되는 최대/최소)
- FPS (실제 달성 가능한 값)
- 코덱 및 백엔드 정보
- 여러 카메라 장치 스캔

Author: Camera Spec Analysis
Date: 2025-01-08
"""

import cv2
import time
import numpy as np


def check_camera_specs(camera_index=0):
    """
    📹 지정된 카메라의 상세 스펙 확인
    
    Args:
        camera_index (int): 카메라 인덱스 (보통 0부터 시작)
        
    Returns:
        dict: 카메라 스펙 정보
    """
    print(f"📹 카메라 {camera_index} 스펙 확인 중...")
    
    # 🎥 카메라 연결
    cap = cv2.VideoCapture(camera_index)
    
    if not cap.isOpened():
        print(f"❌ 카메라 {camera_index}에 연결할 수 없습니다.")
        return None
    
    specs = {}
    
    # 📊 기본 정보
    specs['camera_index'] = camera_index
    specs['backend'] = cap.getBackendName()
    
    # 📐 현재 해상도
    current_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    current_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    specs['current_resolution'] = (current_width, current_height)
    
    # 🎯 현재 FPS
    current_fps = cap.get(cv2.CAP_PROP_FPS)
    specs['declared_fps'] = current_fps
    
    # 🔍 기타 속성들
    specs['brightness'] = cap.get(cv2.CAP_PROP_BRIGHTNESS)
    specs['contrast'] = cap.get(cv2.CAP_PROP_CONTRAST)
    specs['saturation'] = cap.get(cv2.CAP_PROP_SATURATION)
    specs['hue'] = cap.get(cv2.CAP_PROP_HUE)
    specs['gain'] = cap.get(cv2.CAP_PROP_GAIN)
    specs['exposure'] = cap.get(cv2.CAP_PROP_EXPOSURE)
    
    # ⚡ 실제 FPS 측정 (10프레임)
    print("⚡ 실제 FPS 측정 중 (10프레임)...")
    
    frame_times = []
    for i in range(10):
        start_time = time.time()
        ret, frame = cap.read()
        end_time = time.time()
        
        if ret:
            frame_times.append(end_time - start_time)
        else:
            print(f"❌ 프레임 {i} 읽기 실패")
            break
    
    if frame_times:
        avg_frame_time = np.mean(frame_times)
        actual_fps = 1.0 / avg_frame_time
        specs['actual_fps'] = actual_fps
        specs['frame_time_avg'] = avg_frame_time
        specs['frame_time_std'] = np.std(frame_times)
    else:
        specs['actual_fps'] = 0
    
    cap.release()
    return specs


def test_resolution_settings(camera_index=0, test_resolutions=None):
    """
    📐 다양한 해상도 설정 테스트
    
    Args:
        camera_index (int): 카메라 인덱스
        test_resolutions (list): 테스트할 해상도 리스트
        
    Returns:
        dict: 지원되는 해상도 정보
    """
    if test_resolutions is None:
        # 🎯 일반적인 해상도들
        test_resolutions = [
            (640, 480),    # VGA
            (1280, 720),   # HD 720p
            (1920, 1080),  # HD 1080p
            (2560, 1440),  # QHD
            (3840, 2160),  # 4K UHD
            (3000, 3000),  # 정사각형 (final_turntable.py에서 시도한 값)
        ]
    
    print(f"📐 카메라 {camera_index} 해상도 지원 테스트...")
    
    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        print(f"❌ 카메라 {camera_index}에 연결할 수 없습니다.")
        return None
    
    supported_resolutions = []
    
    for width, height in test_resolutions:
        # 해상도 설정 시도
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        
        # 실제 설정된 해상도 확인
        actual_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        actual_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # 프레임 읽기 테스트
        ret, frame = cap.read()
        
        if ret and frame is not None:
            frame_shape = frame.shape[:2]  # (height, width)
            
            result = {
                'requested': (width, height),
                'set_values': (actual_width, actual_height),
                'actual_frame': (frame_shape[1], frame_shape[0]),  # (width, height)
                'success': ret,
                'matches_request': (actual_width == width and actual_height == height)
            }
            
            supported_resolutions.append(result)
            
            status = "✅" if result['matches_request'] else "⚠️"
            print(f"  {status} {width}x{height} → 설정: {actual_width}x{actual_height}, 프레임: {result['actual_frame'][0]}x{result['actual_frame'][1]}")
        else:
            print(f"  ❌ {width}x{height} → 프레임 읽기 실패")
    
    cap.release()
    return supported_resolutions


def find_available_cameras(max_index=5):
    """
    🔍 사용 가능한 모든 카메라 장치 찾기
    
    Args:
        max_index (int): 확인할 최대 카메라 인덱스
        
    Returns:
        list: 사용 가능한 카메라 인덱스 리스트
    """
    print(f"🔍 카메라 장치 스캔 중 (0-{max_index})...")
    
    available_cameras = []
    
    for i in range(max_index + 1):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            # 프레임 읽기 테스트
            ret, frame = cap.read()
            if ret and frame is not None:
                available_cameras.append(i)
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                print(f"  ✅ 카메라 {i}: {width}x{height}")
            else:
                print(f"  ⚠️ 카메라 {i}: 연결되었지만 프레임 읽기 실패")
        else:
            print(f"  ❌ 카메라 {i}: 연결 불가")
        
        cap.release()
    
    return available_cameras


def diagnose_final_turntable_camera_issues():
    """
    🔧 final_turntable.py의 카메라 설정 문제 진단
    """
    print("🔧 final_turntable.py 카메라 설정 문제 진단...")
    
    # final_turntable.py에서 시도하는 설정들
    problematic_settings = [
        ('WIDTH 중복 설정', 'CAP_PROP_FRAME_WIDTH를 두 번 설정'),
        ('HEIGHT 누락', 'CAP_PROP_FRAME_HEIGHT 설정이 없음'),
        ('3000x3000 해상도', '대부분 웹캠에서 지원하지 않는 해상도'),
        ('AVFoundation 백엔드', 'macOS에서만 사용 가능')
    ]
    
    print("📋 발견된 문제점들:")
    for issue_name, description in problematic_settings:
        print(f"  ❌ {issue_name}: {description}")
    
    print("\n💡 권장 해결방안:")
    print("  1. HEIGHT 설정 추가")
    print("  2. 지원되는 해상도로 변경 (1920x1080 또는 1280x720)")
    print("  3. 해상도 설정 후 실제 값 확인")
    print("  4. FPS 실측값 사용")


def full_camera_analysis(camera_index=0):
    """
    🎯 전체 카메라 분석 실행
    """
    print("="*60)
    print("📹 FULL CAMERA ANALYSIS 📹")
    print("="*60)
    
    # 1. 사용 가능한 카메라 찾기
    available_cameras = find_available_cameras()
    print(f"\n🎯 사용 가능한 카메라: {available_cameras}")
    
    if camera_index not in available_cameras:
        if available_cameras:
            camera_index = available_cameras[0]
            print(f"⚠️ 요청한 카메라 {camera_index}가 없어 {available_cameras[0]}번 사용")
        else:
            print("❌ 사용 가능한 카메라가 없습니다.")
            return None
    
    # 2. 카메라 스펙 확인
    print(f"\n📊 카메라 {camera_index} 상세 스펙:")
    specs = check_camera_specs(camera_index)
    
    if specs:
        print(f"  - 백엔드: {specs['backend']}")
        print(f"  - 현재 해상도: {specs['current_resolution'][0]}x{specs['current_resolution'][1]}")
        print(f"  - 선언된 FPS: {specs['declared_fps']:.1f}")
        print(f"  - 실제 FPS: {specs['actual_fps']:.1f}")
        print(f"  - 프레임 시간: {specs['frame_time_avg']*1000:.1f}ms ± {specs['frame_time_std']*1000:.1f}ms")
        
        # 3. 해상도 지원 테스트
        print(f"\n📐 해상도 지원 테스트:")
        resolutions = test_resolution_settings(camera_index)
        
        # 4. final_turntable.py 문제 진단
        print(f"\n🔧 기존 코드 문제 진단:")
        diagnose_final_turntable_camera_issues()
        
        return {
            'specs': specs,
            'resolutions': resolutions,
            'camera_index': camera_index
        }
    
    return None


if __name__ == "__main__":
    # 🎯 전체 분석 실행
    analysis_result = full_camera_analysis(camera_index=0)
    
    if analysis_result:
        print("\n✅ 분석 완료! 결과를 참고하여 카메라 설정을 최적화하세요.")
    else:
        print("\n❌ 분석 실패. 카메라 연결을 확인하세요.") 