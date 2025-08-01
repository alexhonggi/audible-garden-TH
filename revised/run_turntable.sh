#!/bin/bash

# 터테이블 실행 모드 선택 스크립트

echo "🎵 Audible Garden Turntable 실행"
echo "================================"
echo ""
echo "실행 모드를 선택하세요:"
echo ""
echo "1. 🎥 카메라 화면과 함께 실행 (GUI 모드)"
echo "   - 터테이블과 카메라 화면이 모두 표시됩니다"
echo "   - 시각적으로 회전 상태를 확인할 수 있습니다"
echo ""
echo "2. 🎵 카메라 화면 없이 실행 (CLI 모드)"
echo "   - 터미널에서만 로그가 표시됩니다"
echo "   - 시스템 리소스를 적게 사용합니다"
echo ""
echo "3. 🎮 GUI 컨트롤러로 실행"
echo "   - START/STOP 버튼으로 제어합니다"
echo "   - 로그 모니터링이 가능합니다"
echo ""

read -p "선택 (1-3): " choice

case $choice in
    1)
        echo ""
        echo "🎥 카메라 화면과 함께 실행합니다..."
        ./run_with_camera.sh
        ;;
    2)
        echo ""
        echo "🎵 카메라 화면 없이 실행합니다..."
        ./run_without_camera.sh
        ;;
    3)
        echo ""
        echo "🎮 GUI 컨트롤러를 시작합니다..."
        ./run_controller.sh
        echo ""
        echo "💡 로그 확인: ./monitor_both_logs.sh"
        ;;
    *)
        echo ""
        echo "❌ 잘못된 선택입니다. 카메라 화면과 함께 실행합니다..."
        ./run_with_camera.sh
        ;;
esac 