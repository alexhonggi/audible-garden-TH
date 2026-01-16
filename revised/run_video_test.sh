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

# Default video file
DEFAULT_VIDEO="assets/IMG_5071.mov"
VIDEO_FILE="$DEFAULT_VIDEO"
EXTRA_ARGS=""

# Check if first argument exists and doesn't start with - (so it's a filename)
if [ -n "$1" ] && [[ "$1" != -* ]]; then
    VIDEO_FILE="$1"
    shift # Remove filename from arguments list
fi

# All remaining arguments are passed to the python script
EXTRA_ARGS="$@"

echo "🎥 비디오 파일로 터테이블 테스트 실행"
echo "=================================="
echo "🎬 입력 파일: $VIDEO_FILE"
echo "⏱️  Radius Scanning 활성화 (Circular Mode)"
echo "🔧 추가 옵션: $EXTRA_ARGS"
echo ""

# GUI 모드로 실행하며 비디오 파일 입력
"$PYTHON_PATH" turntable_gui_.py --input "$VIDEO_FILE" --roi-mode Circular --config config.json $EXTRA_ARGS
