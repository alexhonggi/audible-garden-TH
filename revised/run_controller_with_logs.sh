#!/bin/bash

# Source conda initialization for this script

# Dynamic Python path detection
find_conda_python() {
    local env_name="${1:-garden}"
    
    # Method 1: Try conda info
    if command -v conda &> /dev/null; then
        local conda_path=$(conda info --envs --json | grep -o '"[^"]*'${env_name}'[^"]*"' | head -1 | tr -d '"')
        if [ -n "$conda_path" ] && [ -f "$conda_path/bin/python" ]; then
            echo "$conda_path/bin/python"
            return 0
        fi
    fi
    
    # Method 2: Try common paths
    local common_paths=(
        "$HOME/miniconda3/envs/$env_name/bin/python"
        "$HOME/anaconda3/envs/$env_name/bin/python"
        "/opt/homebrew/Caskroom/miniconda/base/envs/$env_name/bin/python"
        "/opt/anaconda3/envs/$env_name/bin/python"
        "/usr/local/anaconda3/envs/$env_name/bin/python"
    )
    
    for path in "${common_paths[@]}"; do
        if [ -f "$path" ]; then
            echo "$path"
            return 0
        fi
    done
    
    # Method 3: Fallback to current Python
    echo "$(which python)"
}

# Get the Python path
PYTHON_PATH=$(find_conda_python "garden")
echo "🐍 Using Python: $PYTHON_PATH"


source ~/.zshrc

# Turntable Controller 실행 스크립트 (로그 저장 버전)
# conda 환경의 정확한 Python을 사용하고 로그를 파일에 저장합니다

echo "🎵 Turntable Controller 시작 중 (로그 저장 모드)..."

# 로그 파일 경로 설정
LOG_FILE="turntable_controller.log"
echo "📄 로그 파일: $(pwd)/$LOG_FILE"

# GUI가 제대로 나타나도록 로그 파일에 출력 저장
"$PYTHON_PATH" turntable_controller.py > "$LOG_FILE" 2>&1 &

echo "GUI 창이 나타날 때까지 잠시 기다려주세요..."
echo ""
echo "📋 로그 확인 방법:"
echo "  실시간 로그 보기: tail -f $LOG_FILE"
echo "  전체 로그 보기:   cat $LOG_FILE"
echo "  로그 파일 위치:   $(pwd)/$LOG_FILE"
echo ""
echo "만약 GUI 창이 보이지 않는다면:"
echo "1. Dock에서 Python 아이콘을 찾아 클릭하세요"
echo "2. Command+Tab을 눌러 Python 앱으로 전환하세요"
echo "3. Mission Control (F3)을 눌러 모든 창을 확인하세요" 
