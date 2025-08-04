#!/usr/bin/env python3
"""
🔧 First Run Fix Test Script
============================
첫 번째 실행 시 레코드 감지 문제 해결 테스트

Author: AI Assistant
Date: 2025-01-08
"""
import cv2 as cv
import numpy as np
import time
import sys
import os

# 경로 설정
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

from utils.record_detector import create_record_detector
from utils.camera_utils import open_camera, close_camera


def test_first_run_fix():
    """첫 번째 실행 문제 해결 테스트"""
    print("🔧 First Run Fix Test")
    print("=" * 30)
    
    # 카메라 초기화
    print("📷 카메라 초기화 중...")
    camera = open_camera(0, 1280, 720)
    if not camera:
        print("❌ 카메라를 열 수 없습니다.")
        return
    
    try:
        # 첫 번째 프레임 가져오기
        ret, frame = camera.read_frame()
        if not ret:
            print("❌ 첫 번째 프레임을 읽을 수 없습니다.")
            return
        
        # 90도 회전
        frame = cv.rotate(frame, cv.ROTATE_90_CLOCKWISE)
        
        # ROI 자동 설정 (화면 중앙)
        h, w = frame.shape[:2]
        center_x, center_y = w // 2, h // 2
        radius = min(w, h) // 3
        roi_coords = (center_x, center_y, radius)
        
        print(f"🎯 ROI 설정: {roi_coords}")
        
        # 레코드 감지기 초기화 (수정된 순서)
        print("🎵 레코드 감지기 초기화...")
        detector = create_record_detector(
            method="color_analysis",
            threshold=0.2,  # 새로운 임계값
            baseline_frames=30,
            smoothing_factor=0.8
        )
        
        # ROI 설정
        detector.set_roi(roi_coords)
        print("✅ 레코드 감지기 초기화 완료")
        
        # 테스트 1: 첫 번째 실행 시뮬레이션
        print("\n🧪 테스트 1: 첫 번째 실행 시뮬레이션")
        print("기준 수집 중...")
        
        for i in range(35):  # 30 + 5 프레임
            ret, frame = camera.read_frame()
            if ret:
                frame = cv.rotate(frame, cv.ROTATE_90_CLOCKWISE)
                record_present, confidence = detector.detect_record(frame)
                
                if i < 30:
                    print(f"  📊 기준 수집 중... ({i+1}/30)")
                else:
                    print(f"  🔍 감지 테스트: record_present={record_present}, confidence={confidence:.3f}")
                
                time.sleep(0.1)
        
        # 테스트 2: 정지 후 재시작 시뮬레이션
        print("\n🧪 테스트 2: 정지 후 재시작 시뮬레이션")
        print("기준 재설정...")
        detector.reset_baseline()
        
        for i in range(35):  # 30 + 5 프레임
            ret, frame = camera.read_frame()
            if ret:
                frame = cv.rotate(frame, cv.ROTATE_90_CLOCKWISE)
                record_present, confidence = detector.detect_record(frame)
                
                if i < 30:
                    print(f"  📊 기준 수집 중... ({i+1}/30)")
                else:
                    print(f"  🔍 감지 테스트: record_present={record_present}, confidence={confidence:.3f}")
                
                time.sleep(0.1)
        
        print("\n🎉 테스트 완료!")
        print("💡 결과:")
        print("   - 첫 번째 실행: 기준 수집 후 감지 시작")
        print("   - 재시작: 기준 재설정 후 감지 시작")
        print("   - 두 경우 모두 동일하게 작동해야 함")
        
    except Exception as e:
        print(f"❌ 테스트 중 오류 발생: {e}")
    finally:
        close_camera(0)
        print("✅ 정리 완료")


if __name__ == "__main__":
    test_first_run_fix() 