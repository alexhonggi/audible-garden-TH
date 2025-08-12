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

# Turntable Controller 실행 스크립트 (터미널 출력 버전)
# conda 환경의 정확한 Python을 사용하고 터미널에서 직접 로그를 봅니다

echo "🎵 Turntable Controller 시작 중 (터미널 출력 모드)..."
echo "⚠️  이 터미널 창을 닫으면 프로그램이 종료됩니다!"
echo "🔄 프로그램을 백그라운드로 실행하려면 Ctrl+Z 후 'bg' 명령을 사용하세요"
echo ""
echo "🎯 터테이블 프로그램을 직접 실행합니다 (6000초간)..."
echo ""

# 터테이블 프로그램을 직접 실행 (모든 출력이 터미널에 표시됨)
"$PYTHON_PATH" turntable_gui_.py --cli --duration 6000 --rpm 2.5 --transmission-interval 30 --roi-mode Circular --config config.json 
