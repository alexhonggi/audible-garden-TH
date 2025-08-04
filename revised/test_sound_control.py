#!/usr/bin/env python3
"""
🔇 Sound Control Test Script
============================
소리 켜기/끄기 기능을 테스트하는 스크립트

Author: AI Assistant
Date: 2025-01-08
"""
import time
import sys
import os

# 경로 설정
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

from utils.osc_utils import init_client, send_midi, stop_all_sounds


def test_sound_control():
    """소리 제어 테스트"""
    print("🔇 Sound Control Test")
    print("=" * 30)
    
    # OSC 클라이언트 초기화
    print("📡 OSC 클라이언트 초기화...")
    client = init_client(5555)
    if not client:
        print("❌ OSC 클라이언트 초기화 실패")
        return
    
    try:
        print("✅ OSC 클라이언트 초기화 완료")
        print()
        
        # 테스트 1: 소리 켜기
        print("🎵 테스트 1: 소리 켜기")
        test_notes = [60, 62, 64]  # C, D, E
        test_velocities = [64, 64, 64]
        test_durations = [1000, 1000, 1000]
        
        send_midi(client, len(test_notes), test_notes, test_velocities, test_durations)
        print("✅ 소리 켜기 테스트 완료")
        print()
        
        # 잠시 대기
        time.sleep(2)
        
        # 테스트 2: 소리 끄기
        print("🔇 테스트 2: 소리 끄기")
        stop_all_sounds(client)
        print("✅ 소리 끄기 테스트 완료")
        print()
        
        # 잠시 대기
        time.sleep(1)
        
        # 테스트 3: 빈 리스트로 소리 끄기
        print("🔇 테스트 3: 빈 리스트로 소리 끄기")
        send_midi(client, 1, [], [], [])
        print("✅ 빈 리스트 테스트 완료")
        print()
        
        print("🎉 모든 테스트 완료!")
        print()
        print("💡 결과 확인:")
        print("   - 소리가 켜졌다가 끊어졌다면 정상")
        print("   - 소리가 계속 반복된다면 OSC 수신측에서 처리 필요")
        
    except Exception as e:
        print(f"❌ 테스트 중 오류 발생: {e}")
    finally:
        print("✅ 테스트 종료")


if __name__ == "__main__":
    test_sound_control() 