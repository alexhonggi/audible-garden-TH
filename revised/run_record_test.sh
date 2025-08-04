#!/bin/bash

# Source conda initialization for this script
source ~/.zshrc

echo "🎵 레코드 감지 테스트 실행"
echo "=========================="
echo ""

# conda 환경 활성화
conda activate garden

# 테스트 실행
python test_record_detection.py 