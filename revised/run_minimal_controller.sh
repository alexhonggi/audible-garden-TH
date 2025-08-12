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

# Minimal Turntable Controller 실행 스크립트

echo "🎮 Minimal Turntable Controller 시작"
echo "===================================="
echo "📋 기능:"
echo "  🚀 START: 즉시 CLI 모드 실행"
echo "  🛑 STOP: 즉시 프로그램 종료"
echo "  🔵 파란 불: 레코드 감지 준비 완료 표시"
echo "  🎯 최소한의 인터페이스 (버튼만)"
echo ""

# conda 환경 활성화
conda activate garden

# Minimal Controller 실행
echo "🎮 Minimal Controller GUI를 시작합니다..."
echo "💡 START/STOP 버튼과 파란 불 표시기가 나타납니다..."
echo ""

# GUI 실행
$PYTHON_PATH minimal_controller.py 
