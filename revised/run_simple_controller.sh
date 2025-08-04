#!/bin/bash

# Source conda initialization for this script
source ~/.zshrc

# Simple Turntable Controller 실행 스크립트

echo "🎮 Simple Turntable Controller 시작"
echo "=================================="
echo "📋 기능:"
echo "  🚀 START: 3초 후 CLI 모드 실행"
echo "  🛑 STOP: 3초 후 프로그램 종료"
echo "  📋 로그: 실시간 실행 로그 표시"
echo ""

# conda 환경 활성화
conda activate garden

# Simple Controller 실행
echo "🎮 Simple Controller GUI를 시작합니다..."
echo "💡 GUI 창이 나타날 때까지 잠시 기다려주세요..."
echo ""

# GUI 실행
/opt/homebrew/Caskroom/miniconda/base/envs/garden/bin/python simple_controller.py 