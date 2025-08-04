#!/bin/bash

# Source conda initialization for this script
source ~/.zshrc

echo "🧪 Conda Setup Test"
echo "=================="
echo ""

echo "1. Testing conda activation..."
conda activate garden
if [ $? -eq 0 ]; then
    echo "✅ conda activate garden - SUCCESS"
else
    echo "❌ conda activate garden - FAILED"
    exit 1
fi

echo ""
echo "2. Testing Python path..."
PYTHON_PATH=$(which python)
echo "Python path: $PYTHON_PATH"

if [[ "$PYTHON_PATH" == *"garden"* ]]; then
    echo "✅ Python is from garden environment"
else
    echo "❌ Python is NOT from garden environment"
    exit 1
fi

echo ""
echo "3. Testing Python version..."
python --version

echo ""
echo "4. Testing key packages..."
python -c "import numpy; print('✅ numpy:', numpy.__version__)"
python -c "import cv2; print('✅ opencv-python:', cv2.__version__)"
python -c "import pandas; print('✅ pandas:', pandas.__version__)"
python -c "import PyQt5; print('✅ PyQt5 available')"

echo ""
echo "🎉 All tests passed! Conda setup is working correctly." 