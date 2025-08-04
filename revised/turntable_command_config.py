#!/usr/bin/env python3
"""
🎵 Turntable Command Configuration
=================================
터테이블 명령어 설정을 관리하는 모듈

Author: AI Assistant
Date: 2025-01-08
"""

import os
import sys

# 스크립트 경로 설정
SCRIPT_PATH = "turntable_gui_.py"

# 기본 명령어 설정
DEFAULT_COMMAND = {
    "duration": 6000,
    "rpm": 2.5,
    "transmission_interval": 30,
    "roi_mode": "Circular",
    "config": "config.json"
}

def get_command_string(flags=None):
    """
    설정된 플래그들을 바탕으로 실행할 명령어 문자열을 생성합니다.
    """
    if flags is None:
        flags = {}
    
    # 기본값과 플래그 병합
    cmd_parts = ["python", SCRIPT_PATH, "--cli"]
    
    # 플래그에 따라 인자 추가
    if flags.get("duration"):
        cmd_parts.extend(["--duration", str(flags["duration"])])
    else:
        cmd_parts.extend(["--duration", str(DEFAULT_COMMAND["duration"])])
    
    if flags.get("rpm"):
        cmd_parts.extend(["--rpm", str(flags["rpm"])])
    else:
        cmd_parts.extend(["--rpm", str(DEFAULT_COMMAND["rpm"])])
    
    if flags.get("transmission_interval"):
        cmd_parts.extend(["--transmission-interval", str(flags["transmission_interval"])])
    else:
        cmd_parts.extend(["--transmission-interval", str(DEFAULT_COMMAND["transmission_interval"])])
    
    if flags.get("roi_mode"):
        cmd_parts.extend(["--roi-mode", flags["roi_mode"]])
    else:
        cmd_parts.extend(["--roi-mode", DEFAULT_COMMAND["roi_mode"]])
    
    if flags.get("config"):
        cmd_parts.extend(["--config", flags["config"]])
    else:
        cmd_parts.extend(["--config", DEFAULT_COMMAND["config"]])
    
    # 녹음 옵션
    if flags.get("record", False):
        cmd_parts.append("--record")
    
    if flags.get("exit_on_record_complete", False):
        cmd_parts.append("--exit-on-record-complete")
    
    return " ".join(cmd_parts)

def get_command(flags=None):
    """
    설정된 플래그들을 바탕으로 실행할 명령어를 생성합니다.
    """
    # conda 환경의 Python 사용
    python_path = "/opt/homebrew/Caskroom/miniconda/base/envs/garden/bin/python"
    cmd = [python_path, SCRIPT_PATH, "--cli"]
    
    # 플래그에 따라 인자 추가
    if flags is None:
        flags = {}
    
    if flags.get("duration"):
        cmd.extend(["--duration", str(flags["duration"])])
    else:
        cmd.extend(["--duration", str(DEFAULT_COMMAND["duration"])])
    
    if flags.get("rpm"):
        cmd.extend(["--rpm", str(flags["rpm"])])
    else:
        cmd.extend(["--rpm", str(DEFAULT_COMMAND["rpm"])])
    
    if flags.get("transmission_interval"):
        cmd.extend(["--transmission-interval", str(flags["transmission_interval"])])
    else:
        cmd.extend(["--transmission-interval", str(DEFAULT_COMMAND["transmission_interval"])])
    
    if flags.get("roi_mode"):
        cmd.extend(["--roi-mode", flags["roi_mode"]])
    else:
        cmd.extend(["--roi-mode", DEFAULT_COMMAND["roi_mode"]])
    
    if flags.get("config"):
        cmd.extend(["--config", flags["config"]])
    else:
        cmd.extend(["--config", DEFAULT_COMMAND["config"]])
    
    # 녹음 옵션
    if flags.get("record", False):
        cmd.append("--record")
    
    if flags.get("exit_on_record_complete", False):
        cmd.append("--exit-on-record-complete")
    
    return cmd

if __name__ == "__main__":
    # 테스트용
    print("기본 명령어:")
    print(get_command_string())
    
    print("\n녹음 포함 명령어:")
    print(get_command_string({"record": True, "exit_on_record_complete": True})) 