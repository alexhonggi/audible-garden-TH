#!/usr/bin/env python3
"""
🎵 Record Detection Test Script
===============================
레코드 감지 기능을 테스트하는 스크립트

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


def test_record_detection():
    """레코드 감지 테스트"""
    print("🎵 레코드 감지 테스트 시작")
    print("=" * 50)
    
    # 카메라 초기화
    print("📷 카메라 초기화 중...")
    camera = open_camera(0, 1280, 720)
    if not camera:
        print("❌ 카메라를 열 수 없습니다.")
        return
    
    try:
        # 레코드 감지기 초기화
        print("🎯 레코드 감지기 초기화...")
        detector = create_record_detector(
            method="color_analysis",
            threshold=0.2,  # 사용자 요청으로 0.2로 변경
            baseline_frames=30,
            smoothing_factor=0.8
        )
        
        # ROI 자동 설정 (화면 중앙)
        frame_count = 0
        roi_coords = None
        
        print("🔄 테스트 시작...")
        print("💡 레코드를 놓고 빼면서 감지 상태를 확인하세요!")
        print("   - 'q': 종료")
        print("   - 'r': 기준 재설정")
        print("   - 't': 임계값 조정")
        print()
        
        while True:
            ret, frame = camera.read_frame()
            if not ret or frame is None:
                print("⚠️ 프레임 읽기 실패")
                break
            
            # 90도 회전
            frame = cv.rotate(frame, cv.ROTATE_90_CLOCKWISE)
            
            # 첫 프레임에서 ROI 자동 설정
            if roi_coords is None:
                h, w = frame.shape[:2]
                center_x, center_y = w // 2, h // 2
                radius = min(w, h) // 3
                roi_coords = (center_x, center_y, radius)
                detector.set_roi(roi_coords)
                print(f"🎯 ROI 자동 설정: 중심({center_x}, {center_y}), 반지름 {radius}")
            
            # 레코드 감지
            record_present, confidence = detector.detect_record(frame)
            
            # 상태 표시
            status = "✅ 레코드 있음" if record_present else "❌ 레코드 없음"
            print(f"\r{status} | 신뢰도: {confidence:.3f} | 프레임: {frame_count}", end="", flush=True)
            
            # 시각적 피드백
            overlay = frame.copy()
            
            # ROI 영역 표시
            if roi_coords:
                center_x, center_y, radius = roi_coords
                cv.circle(overlay, (center_x, center_y), radius, (255, 255, 0), 2)
                
                # 레코드 상태에 따른 색상
                color = (0, 255, 0) if record_present else (0, 0, 255)
                cv.circle(overlay, (center_x, center_y), 10, color, -1)
            
            # 텍스트 오버레이
            text = f"RECORD: {'ON' if record_present else 'OFF'} ({confidence:.2f})"
            cv.putText(overlay, text, (10, 30), cv.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            
            # 기준 수집 상태 표시
            if not detector.baseline_collected:
                baseline_text = f"기준 수집 중... ({detector.frame_count}/{detector.baseline_frames})"
                cv.putText(overlay, baseline_text, (10, 70), cv.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            
            # 화면 표시
            cv.imshow("Record Detection Test", overlay)
            
            # 키 입력 처리
            key = cv.waitKey(1) & 0xFF
            if key == ord('q'):
                print("\n👋 테스트 종료")
                break
            elif key == ord('r'):
                print("\n🔄 기준 재설정...")
                detector.reset_baseline()
            elif key == ord('t'):
                # 임계값 조정
                current_threshold = detector.threshold
                new_threshold = current_threshold + 0.1 if current_threshold < 0.9 else 0.1
                detector.threshold = new_threshold
                print(f"\n🎛️ 임계값 조정: {current_threshold:.1f} → {new_threshold:.1f}")
            
            frame_count += 1
            time.sleep(0.1)  # 10 FPS
            
    except KeyboardInterrupt:
        print("\n👋 사용자에 의해 중단됨")
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
    finally:
        close_camera(0)
        cv.destroyAllWindows()
        print("✅ 정리 완료")


if __name__ == "__main__":
    test_record_detection() 