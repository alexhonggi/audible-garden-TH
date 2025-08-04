#!/bin/bash

# Source conda initialization for this script
source ~/.zshrc

# Minimal Turntable Controller 실행 스크립트

echo "🎮 Minimal Turntable Controller 시작"
echo "===================================="
echo "📋 기능:"
echo "  🚀 START: 즉시 CLI 모드 실행"
echo "  🛑 STOP: 즉시 프로그램 종료"
echo "  🔵 파란 불: 레코드 감지 준비 완료 표시"
echo "  🎯 최소한의 인터페이스 (버튼만)"
echo ""

# conda 환경 활성화
conda activate garden

# Minimal Controller 실행
echo "🎮 Minimal Controller GUI를 시작합니다..."
echo "💡 START/STOP 버튼과 파란 불 표시기가 나타납니다..."
echo ""

# GUI 실행
/opt/homebrew/Caskroom/miniconda/base/envs/garden/bin/python minimal_controller.py 