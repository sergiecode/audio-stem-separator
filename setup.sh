#!/bin/bash
# Installation Script for Linux/macOS

echo "🎵 Audio Stem Separator - Setup Script"
echo "Created by Sergie Code"
echo "========================================"

# Check Python installation
echo "Checking Python installation..."
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo "❌ Python not found. Please install Python 3.8+ first."
    exit 1
fi

echo "✅ Found Python: $($PYTHON_CMD --version)"

# Check Python version
PYTHON_VERSION=$($PYTHON_CMD -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "Python version: $PYTHON_VERSION"

if [[ $(echo "$PYTHON_VERSION >= 3.8" | bc -l) -eq 0 ]]; then
    echo "❌ Python 3.8 or higher required. Found: $PYTHON_VERSION"
    exit 1
fi

# Create virtual environment
echo "Creating virtual environment..."
$PYTHON_CMD -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install PyTorch
echo "Installing PyTorch..."
echo "Checking for CUDA availability..."

if command -v nvidia-smi &> /dev/null; then
    echo "✅ NVIDIA GPU detected. Installing CUDA-enabled PyTorch..."
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
else
    echo "⚠️  No NVIDIA GPU detected. Installing CPU-only PyTorch..."
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
fi

# Install FFmpeg (required for audio processing)
echo "Checking FFmpeg installation..."
if ! command -v ffmpeg &> /dev/null; then
    echo "⚠️  FFmpeg not found. Please install it:"
    echo "  Ubuntu/Debian: sudo apt install ffmpeg"
    echo "  CentOS/RHEL: sudo yum install ffmpeg"
    echo "  macOS: brew install ffmpeg"
else
    echo "✅ FFmpeg found"
fi

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Test installation
echo "Testing installation..."
python -c "
import torch
import demucs
import openunmix
print(f'✅ PyTorch version: {torch.__version__}')
print(f'✅ CUDA available: {torch.cuda.is_available()}')
print(f'✅ Demucs installed')
print(f'✅ Open-Unmix installed')
"

echo "✅ Setup complete!"
echo ""
echo "To activate the environment in the future, run:"
echo "  source venv/bin/activate"
echo ""
echo "To test the installation:"
echo "  python -m src.main --help"
