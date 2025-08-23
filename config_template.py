# Configuration file for the Audio Stem Separator
# Copy this file to config.py and modify as needed

import os
from pathlib import Path

# Base configuration
BASE_DIR = Path(__file__).parent
OUTPUT_BASE_DIR = BASE_DIR / "output"
TEMP_DIR = BASE_DIR / "temp"
LOG_DIR = BASE_DIR / "logs"

# Model configuration
DEFAULT_MODEL = "demucs"
DEFAULT_MODEL_VARIANTS = {
    "demucs": "htdemucs",
    "openunmix": "umxhq"
}

# Processing configuration
MAX_FILE_SIZE_MB = 500
PROCESSING_TIMEOUT_SECONDS = 1800  # 30 minutes
DEFAULT_SAMPLE_RATE = 44100

# Device configuration
AUTO_DETECT_DEVICE = True
PREFER_GPU = True
FALLBACK_TO_CPU = True

# Output configuration
OUTPUT_FORMAT = "wav"
OUTPUT_QUALITY = "high"
NORMALIZE_OUTPUT = True
CREATE_TIMESTAMPED_FOLDERS = True

# API configuration
API_PORT = 3000
API_MAX_CONCURRENT_JOBS = 2
API_RATE_LIMIT_PER_MINUTE = 10
API_CORS_ORIGINS = ["*"]

# Logging configuration
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_TO_FILE = True
LOG_TO_CONSOLE = True

# Performance tuning
AUDIO_CHUNK_SIZE = 1024 * 1024  # 1MB chunks
MEMORY_EFFICIENT_MODE = True
CLEANUP_TEMP_FILES = True

# Environment-specific overrides
if os.getenv("PRODUCTION"):
    LOG_LEVEL = "WARNING"
    API_RATE_LIMIT_PER_MINUTE = 5
    API_MAX_CONCURRENT_JOBS = 1

# Development mode
if os.getenv("DEVELOPMENT"):
    LOG_LEVEL = "DEBUG"
    API_RATE_LIMIT_PER_MINUTE = 100
