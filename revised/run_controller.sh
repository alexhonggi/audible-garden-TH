#!/bin/bash

# Turntable Controller 실행 스크립트
# conda 환경의 정확한 Python을 사용하고 macOS에서 GUI를 제대로 표시합니다

echo "🎵 Turntable Controller 시작 중..."

# GUI가 제대로 나타나도록 nohup과 백그라운드 실행 사용 (로그 파일에 저장)
nohup /Users/starchaser/opt/anaconda3/envs/garden/bin/python turntable_controller.py > turntable_controller.log 2>&1 &

echo "GUI 창이 나타날 때까지 잠시 기다려주세요..."
echo ""
echo "📋 로그 확인 방법:"
echo "  실시간 로그 보기: tail -f turntable_controller.log"
echo "  로그 모니터링:   ./monitor_logs.sh"
echo ""
echo "만약 창이 보이지 않는다면:"
echo "1. Dock에서 Python 아이콘을 찾아 클릭하세요"
echo "2. Command+Tab을 눌러 Python 앱으로 전환하세요"
echo "3. Mission Control (F3)을 눌러 모든 창을 확인하세요" 