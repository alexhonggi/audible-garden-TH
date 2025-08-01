#!/bin/bash

# 터테이블 컨트롤러 + 프로세스 로그 실시간 모니터링

CONTROLLER_LOG="turntable_controller.log"
PROCESS_LOG="turntable_process.log"

echo "🔍 터테이블 시스템 실시간 로그 모니터링"
echo "========================================"
echo "📄 GUI 컨트롤러 로그: $(pwd)/$CONTROLLER_LOG"
echo "📄 터테이블 프로세스 로그: $(pwd)/$PROCESS_LOG"
echo "🎯 GUI에서 START 버튼을 눌러보세요!"
echo "⚠️  Ctrl+C로 모니터링을 중지할 수 있습니다."
echo ""

# 메뉴 표시
echo "선택하세요:"
echo "1. 터테이블 프로세스 로그 실시간 보기 (추천)"
echo "2. GUI 컨트롤러 로그 실시간 보기"
echo "3. 터테이블 프로세스 로그 최근 20줄"
echo "4. 두 로그 동시 모니터링"
echo ""

read -p "선택 (1-4): " choice

case $choice in
    1)
        echo "🎵 터테이블 프로세스 로그 실시간 모니터링 중..."
        echo "=================================="
        if [ -f "$PROCESS_LOG" ]; then
            tail -f "$PROCESS_LOG"
        else
            echo "터테이블 프로세스 로그가 없습니다. START 버튼을 눌러주세요."
            touch "$PROCESS_LOG"
            tail -f "$PROCESS_LOG"
        fi
        ;;
    2)
        echo "🎮 GUI 컨트롤러 로그 실시간 모니터링 중..."
        echo "=================================="
        if [ -f "$CONTROLLER_LOG" ]; then
            tail -f "$CONTROLLER_LOG"
        else
            echo "GUI 컨트롤러 로그가 없습니다."
            touch "$CONTROLLER_LOG"
            tail -f "$CONTROLLER_LOG"
        fi
        ;;
    3)
        echo "📑 터테이블 프로세스 로그 최근 20줄:"
        echo "=================================="
        if [ -f "$PROCESS_LOG" ]; then
            tail -n 20 "$PROCESS_LOG"
        else
            echo "터테이블 프로세스 로그가 없습니다."
        fi
        ;;
    4)
        echo "🔄 두 로그 동시 모니터링 중..."
        echo "============================="
        echo "GUI 컨트롤러 로그 | 터테이블 프로세스 로그"
        echo "-------------------------------------------|"
        if command -v multitail >/dev/null 2>&1; then
            multitail "$CONTROLLER_LOG" "$PROCESS_LOG"
        else
            echo "multitail이 설치되지 않음. 터테이블 프로세스 로그만 표시:"
            tail -f "$PROCESS_LOG"
        fi
        ;;
    *)
        echo "❌ 잘못된 선택입니다. 터테이블 프로세스 로그를 표시합니다:"
        tail -f "$PROCESS_LOG"
        ;;
esac 