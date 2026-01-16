#!/bin/bash

echo "🚀 Building Audible Garden Turntable App..."
echo "=========================================="

# 0. Move to script directory
cd "$(dirname "$0")"

# 1. Clean previous build
echo "🧹 Cleaning previous build..."
rm -rf build dist

# 2. Run PyInstaller
echo "📦 Running PyInstaller..."
# --windowed: No console window
# --noconfirm: Do not ask for confirmation
# --clean: Clean PyInstaller cache
# --add-data: Bundle config.json and assets
# --name: App name

pyinstaller --noconfirm --clean "Audible Garden.spec"

echo ""
echo "✨ Build Complete!"
echo "📂 App location: dist/Audible Garden.app"
echo ""
echo "💡 To run the app:"
echo "open 'dist/Audible Garden.app'"
