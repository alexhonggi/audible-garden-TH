#!/bin/bash

# 터테이블 컨트롤러 로그 실시간 모니터링

LOG_FILE="turntable_controller.log"

echo "🔍 터테이블 컨트롤러 실시간 로그 모니터링"
echo "========================================"
echo "📄 로그 파일: $(pwd)/$LOG_FILE"
echo "🎯 GUI에서 START 버튼을 눌러보세요!"
echo "⚠️  Ctrl+C로 모니터링을 중지할 수 있습니다."
echo ""

# 기존 로그가 있다면 마지막 부분만 표시
if [ -f "$LOG_FILE" ]; then
    echo "📋 기존 로그 (마지막 5줄):"
    echo "========================"
    tail -n 5 "$LOG_FILE"
    echo "========================"
    echo ""
fi

echo "🔄 실시간 로그 모니터링 시작..."
echo ""

# 실시간 로그 모니터링
tail -f "$LOG_FILE" 2>/dev/null || echo "로그 파일이 아직 생성되지 않았습니다. START 버튼을 눌러주세요." 