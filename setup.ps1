# Development Setup Guide

## Installation Script for Windows PowerShell

# Check Python installation
Write-Host "Checking Python installation..." -ForegroundColor Green
python --version
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Python not found. Please install Python 3.8+ from https://python.org" -ForegroundColor Red
    exit 1
}

# Create virtual environment
Write-Host "Creating virtual environment..." -ForegroundColor Green
python -m venv venv

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Green
& "venv\Scripts\Activate.ps1"

# Upgrade pip
Write-Host "Upgrading pip..." -ForegroundColor Green
python -m pip install --upgrade pip

# Install PyTorch with CUDA support (if available)
Write-Host "Installing PyTorch..." -ForegroundColor Green
Write-Host "Checking for CUDA availability..." -ForegroundColor Yellow

# Try to detect CUDA
$cuda_available = $false
try {
    nvidia-smi | Out-Null
    $cuda_available = $true
    Write-Host "✅ NVIDIA GPU detected. Installing CUDA-enabled PyTorch..." -ForegroundColor Green
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
} catch {
    Write-Host "⚠️  No NVIDIA GPU detected. Installing CPU-only PyTorch..." -ForegroundColor Yellow
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
}

# Install other requirements
Write-Host "Installing other dependencies..." -ForegroundColor Green
pip install -r requirements.txt

# Test installation
Write-Host "Testing installation..." -ForegroundColor Green
python -c "import torch; print(f'PyTorch version: {torch.__version__}'); print(f'CUDA available: {torch.cuda.is_available()}')"

Write-Host "✅ Setup complete!" -ForegroundColor Green
Write-Host "To activate the environment in the future, run:" -ForegroundColor Cyan
Write-Host "  venv\Scripts\Activate.ps1" -ForegroundColor Cyan
