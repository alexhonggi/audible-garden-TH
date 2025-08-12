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

# 카메라 화면 없이 터테이블 실행 (CLI 모드)

echo "🎵 카메라 화면 없이 터테이블 실행"
echo "=============================="
echo "📟 CLI 모드 (카메라 화면 없음)"
echo "⏱️  6000초 동안 실행됩니다"
echo "⚠️  터미널 창을 닫으면 프로그램이 종료됩니다!"
echo ""

# CLI 모드로 터테이블 직접 실행 (카메라 화면 없음)
"$PYTHON_PATH" turntable_gui_.py --cli --duration 6000 --rpm 2.5 --transmission-interval 30 --roi-mode Circular --config config.json 
