#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
터테이블 명령어 설정 파일
이 파일을 수정하여 실행할 명령어의 플래그들을 변경할 수 있습니다.
"""

# 기본 스크립트 파일명 (같은 폴더 안에 있음)
SCRIPT_PATH = "turntable_gui_.py"

# 명령어 플래그 설정
COMMAND_FLAGS = {
    "cli": False,          # CLI 모드 (False=GUI 모드로 카메라 화면 표시, True=CLI 모드)
    "duration": 6000,      # 실행 시간 (초) - 약 1시간 40분
    "rpm": 2.5,           # 회전 속도 (RPM)
    "transmission_interval": 30,  # 전송 간격 (프레임)
    "roi_mode": "Circular",       # ROI 모드 (Circular/Rectangular)
    "record": False,              # 녹음 여부
    "exit_on_record_complete": False,  # 녹음 완료 시 자동 종료
    "config": "config.json"       # 설정 파일 경로
}

def get_command():
    """설정된 플래그들을 바탕으로 실행할 명령어를 생성합니다."""
    # conda 환경의 Python 사용
    python_path = "/Users/starchaser/opt/anaconda3/envs/garden/bin/python"
    cmd = [python_path, SCRIPT_PATH]
    
    for flag, value in COMMAND_FLAGS.items():
        if value is True:
            cmd.append(f"--{flag.replace('_', '-')}")
        elif value is not False:  # False가 아닌 모든 값들
            cmd.extend([f"--{flag.replace('_', '-')}", str(value)])
    
    return cmd

def get_command_string():
    """사람이 읽기 쉬운 명령어 문자열을 반환합니다."""
    cmd_list = get_command()
    return " ".join(cmd_list)

if __name__ == "__main__":
    print("현재 설정된 명령어:")
    print(get_command_string())
    print("\n실제 실행될 명령어 리스트:")
    print(get_command()) 