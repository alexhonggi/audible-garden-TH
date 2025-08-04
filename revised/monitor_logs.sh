#!/bin/bash

# Source conda initialization for this script
source ~/.zshrc

# 로그 모니터링 스크립트
echo "📊 Turntable Log Monitor"
echo "========================"
echo ""

# 로그 파일 확인
LOG_FILE="turntable_controller.log"
if [ -f "$LOG_FILE" ]; then
    echo "✅ 로그 파일 발견: $LOG_FILE"
    echo "📈 실시간 로그 모니터링을 시작합니다..."
    echo "💡 종료하려면 Ctrl+C를 누르세요"
    echo ""
    
    # 실시간 로그 모니터링
    tail -f "$LOG_FILE"
else
    echo "❌ 로그 파일을 찾을 수 없습니다: $LOG_FILE"
    echo ""
    echo "💡 로그 파일이 생성되지 않았을 수 있습니다:"
    echo "   1. 컨트롤러가 실행 중인지 확인하세요"
    echo "   2. ./run_controller.sh를 실행해보세요"
    echo ""
fi 