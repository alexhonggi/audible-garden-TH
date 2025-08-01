#!/bin/bash

# 터테이블 컨트롤러 로그 확인 유틸리티

LOG_FILE="turntable_controller.log"

echo "📋 Turntable Controller 로그 확인 도구"
echo "=================================="

if [ ! -f "$LOG_FILE" ]; then
    echo "❌ 로그 파일을 찾을 수 없습니다: $LOG_FILE"
    echo "💡 먼저 ./run_controller_with_logs.sh 로 프로그램을 실행하세요"
    exit 1
fi

echo "📄 로그 파일: $(pwd)/$LOG_FILE"
echo "📊 파일 크기: $(du -h "$LOG_FILE" | cut -f1)"
echo "🕒 마지막 수정: $(stat -f "%Sm" "$LOG_FILE")"
echo ""

# 메뉴 표시
echo "선택하세요:"
echo "1. 실시간 로그 보기 (tail -f)"
echo "2. 전체 로그 보기"
echo "3. 최근 50줄 보기"
echo "4. 에러만 보기"
echo "5. 종료"
echo ""

read -p "선택 (1-5): " choice

case $choice in
    1)
        echo "🔄 실시간 로그 모니터링 중... (Ctrl+C로 종료)"
        tail -f "$LOG_FILE"
        ;;
    2)
        echo "📖 전체 로그 내용:"
        echo "=================="
        cat "$LOG_FILE"
        ;;
    3)
        echo "📑 최근 50줄:"
        echo "============"
        tail -n 50 "$LOG_FILE"
        ;;
    4)
        echo "🚨 에러 로그:"
        echo "==========="
        grep -i "error\|traceback\|exception\|failed\|fail" "$LOG_FILE" || echo "에러가 발견되지 않았습니다."
        ;;
    5)
        echo "👋 종료합니다."
        ;;
    *)
        echo "❌ 잘못된 선택입니다."
        ;;
esac 