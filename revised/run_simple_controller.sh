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

# Simple Turntable Controller 실행 스크립트

echo "🎮 Simple Turntable Controller 시작"
echo "=================================="
echo "📋 기능:"
echo "  🚀 START: 3초 후 CLI 모드 실행"
echo "  🛑 STOP: 3초 후 프로그램 종료"
echo "  📋 로그: 실시간 실행 로그 표시"
echo ""

# conda 환경 활성화
conda activate garden

# Simple Controller 실행
echo "🎮 Simple Controller GUI를 시작합니다..."
echo "💡 GUI 창이 나타날 때까지 잠시 기다려주세요..."
echo ""

# GUI 실행
"$PYTHON_PATH" simple_controller.py 
