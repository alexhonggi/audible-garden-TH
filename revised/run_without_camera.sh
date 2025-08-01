#!/bin/bash

# 카메라 화면 없이 터테이블 실행 (CLI 모드)

echo "🎵 카메라 화면 없이 터테이블 실행"
echo "=============================="
echo "📟 CLI 모드 (카메라 화면 없음)"
echo "⏱️  6000초 동안 실행됩니다"
echo "⚠️  터미널 창을 닫으면 프로그램이 종료됩니다!"
echo ""

# CLI 모드로 터테이블 직접 실행 (카메라 화면 없음)
/Users/starchaser/opt/anaconda3/envs/garden/bin/python turntable_gui_.py --cli --duration 6000 --rpm 2.5 --transmission-interval 30 --roi-mode Circular --config config.json 