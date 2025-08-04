#!/bin/bash

# Source conda initialization for this script
source ~/.zshrc

# 카메라 화면과 함께 터테이블 실행 (GUI 모드)

echo "🎥 카메라 화면과 함께 터테이블 실행"
echo "=================================="
echo "📷 카메라 화면이 표시됩니다"
echo "⏱️  6000초 동안 실행됩니다"
echo "⚠️  터미널 창을 닫으면 프로그램이 종료됩니다!"
echo ""

# GUI 모드로 터테이블 직접 실행 (카메라 화면 표시)
/opt/homebrew/Caskroom/miniconda/base/envs/garden/bin/python turntable_gui_.py --duration 6000 --rpm 2.5 --transmission-interval 30 --roi-mode Circular --config config.json 