"""
Audio Stem Separator

A Python module for separating audio tracks into individual stems using AI models.
Created by Sergie Code - Software Engineer & Programming Educator

This module provides easy-to-use functions for:
- Loading and processing audio files
- Separating stems using Demucs and Open-Unmix models
- Saving separated stems to specified directories
- Integration with external services via command line
"""

__version__ = "1.0.0"
__author__ = "Sergie Code"
__email__ = "sergiocode@example.com"

from .stem_separator import StemSeparator

__all__ = ["StemSeparator"]
