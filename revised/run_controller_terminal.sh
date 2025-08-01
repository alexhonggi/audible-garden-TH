#!/bin/bash

# Turntable Controller 실행 스크립트 (터미널 출력 버전)
# conda 환경의 정확한 Python을 사용하고 터미널에서 직접 로그를 봅니다

echo "🎵 Turntable Controller 시작 중 (터미널 출력 모드)..."
echo "⚠️  이 터미널 창을 닫으면 프로그램이 종료됩니다!"
echo "🔄 프로그램을 백그라운드로 실행하려면 Ctrl+Z 후 'bg' 명령을 사용하세요"
echo ""
echo "🎯 터테이블 프로그램을 직접 실행합니다 (6000초간)..."
echo ""

# 터테이블 프로그램을 직접 실행 (모든 출력이 터미널에 표시됨)
/Users/starchaser/opt/anaconda3/envs/garden/bin/python turntable_gui_.py --cli --duration 6000 --rpm 2.5 --transmission-interval 30 --roi-mode Circular --config config.json 