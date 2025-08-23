"""
Test Configuration and Utilities

Common test utilities and fixtures for the test suite.

Created by Sergie Code - Software Engineer & Programming Educator
"""

import unittest
import tempfile
import shutil
import numpy as np
import torch
from pathlib import Path
import sys
import json
import time

# Add src to path for testing
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))


class TestBase(unittest.TestCase):
    """Base test class with common setup and utilities."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.test_data_dir = self.temp_dir / "test_data"
        self.test_data_dir.mkdir(exist_ok=True)
        
    def tearDown(self):
        """Clean up test fixtures."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def create_mock_audio_file(self, filename: str, duration_seconds: float = 10.0, 
                              sample_rate: int = 44100, channels: int = 2) -> Path:
        """Create a mock audio file for testing."""
        import soundfile as sf
        
        # Generate simple sine wave test audio
        t = np.linspace(0, duration_seconds, int(sample_rate * duration_seconds))
        
        # Create a simple stereo signal with different frequencies for L/R
        left_channel = 0.3 * np.sin(2 * np.pi * 440 * t)  # A4 note
        right_channel = 0.3 * np.sin(2 * np.pi * 554.37 * t)  # C#5 note
        
        if channels == 1:
            audio_data = (left_channel + right_channel) / 2
        else:
            audio_data = np.column_stack([left_channel, right_channel])
        
        file_path = self.test_data_dir / filename
        sf.write(str(file_path), audio_data, sample_rate)
        
        return file_path
    
    def create_mock_tensor_audio(self, duration_seconds: float = 5.0, 
                                sample_rate: int = 44100, channels: int = 2) -> torch.Tensor:
        """Create a mock audio tensor for testing."""
        num_samples = int(sample_rate * duration_seconds)
        
        if channels == 1:
            audio = torch.randn(1, num_samples) * 0.1
        else:
            audio = torch.randn(2, num_samples) * 0.1
            
        return audio
    
    def assert_audio_file_exists(self, file_path: Path):
        """Assert that an audio file exists and is valid."""
        self.assertTrue(file_path.exists(), f"Audio file should exist: {file_path}")
        self.assertGreater(file_path.stat().st_size, 0, "Audio file should not be empty")
    
    def assert_stems_generated(self, output_dir: Path, expected_stems: list):
        """Assert that all expected stem files were generated."""
        self.assertTrue(output_dir.exists(), "Output directory should exist")
        
        for stem in expected_stems:
            stem_file = output_dir / f"{stem}.wav"
            self.assert_audio_file_exists(stem_file)


class MockAudioData:
    """Mock audio data generator for testing."""
    
    @staticmethod
    def generate_sine_wave(frequency: float = 440.0, duration: float = 1.0, 
                          sample_rate: int = 44100, amplitude: float = 0.3) -> np.ndarray:
        """Generate a sine wave signal."""
        t = np.linspace(0, duration, int(sample_rate * duration))
        return amplitude * np.sin(2 * np.pi * frequency * t)
    
    @staticmethod
    def generate_white_noise(duration: float = 1.0, sample_rate: int = 44100, 
                           amplitude: float = 0.1) -> np.ndarray:
        """Generate white noise signal."""
        num_samples = int(sample_rate * duration)
        return amplitude * np.random.randn(num_samples)
    
    @staticmethod
    def generate_mixed_signal(duration: float = 5.0, sample_rate: int = 44100) -> np.ndarray:
        """Generate a mixed signal simulating multiple instruments."""
        # Simulate drums (noise burst)
        drums = MockAudioData.generate_white_noise(duration, sample_rate, 0.2)
        
        # Simulate bass (low frequency sine)
        bass = MockAudioData.generate_sine_wave(80, duration, sample_rate, 0.4)
        
        # Simulate vocals (mid frequency with harmonics)
        vocals = (MockAudioData.generate_sine_wave(220, duration, sample_rate, 0.3) +
                 MockAudioData.generate_sine_wave(440, duration, sample_rate, 0.2))
        
        # Simulate other instruments (higher frequencies)
        other = (MockAudioData.generate_sine_wave(880, duration, sample_rate, 0.2) +
                MockAudioData.generate_sine_wave(1320, duration, sample_rate, 0.1))
        
        # Mix all components
        mixed = drums + bass + vocals + other
        
        # Normalize to prevent clipping
        if np.max(np.abs(mixed)) > 1.0:
            mixed = mixed / np.max(np.abs(mixed)) * 0.9
            
        return mixed


class TestRunner:
    """Test runner utility for different test configurations."""
    
    @staticmethod
    def run_test_suite(test_classes: list, verbosity: int = 2):
        """Run a test suite with multiple test classes."""
        suite = unittest.TestSuite()
        
        for test_class in test_classes:
            tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
            suite.addTests(tests)
        
        runner = unittest.TextTestRunner(verbosity=verbosity)
        result = runner.run(suite)
        
        return result.wasSuccessful()
    
    @staticmethod
    def run_performance_tests(duration: int = 30):
        """Run performance benchmarks for specified duration."""
        print(f"Running performance tests for {duration} seconds...")
        
        # This would contain actual performance testing logic
        # For now, it's a placeholder
        time.sleep(1)  # Simulate test execution
        
        return {
            'cpu_usage': 45.2,
            'memory_usage': 512.8,
            'processing_speed': 2.3
        }


# Test configuration constants
TEST_CONFIG = {
    'SHORT_AUDIO_DURATION': 3.0,  # seconds
    'MEDIUM_AUDIO_DURATION': 10.0,  # seconds
    'LONG_AUDIO_DURATION': 30.0,  # seconds
    'TEST_SAMPLE_RATE': 44100,
    'TEST_CHANNELS': 2,
    'EXPECTED_STEMS': ['vocals', 'drums', 'bass', 'other'],
    'SUPPORTED_FORMATS': ['.mp3', '.wav', '.flac', '.m4a', '.aac'],
    'UNSUPPORTED_FORMATS': ['.txt', '.pdf', '.xyz', '.doc'],
    'MAX_PROCESSING_TIME': 300,  # seconds
    'MIN_AUDIO_FILE_SIZE': 1024,  # bytes
}

# Test data for various scenarios
TEST_SCENARIOS = {
    'basic_separation': {
        'description': 'Basic audio separation with default settings',
        'model': 'demucs',
        'duration': TEST_CONFIG['SHORT_AUDIO_DURATION']
    },
    'openunmix_separation': {
        'description': 'Audio separation using Open-Unmix model',
        'model': 'openunmix', 
        'duration': TEST_CONFIG['SHORT_AUDIO_DURATION']
    },
    'gpu_processing': {
        'description': 'GPU-accelerated processing',
        'model': 'demucs',
        'device': 'cuda',
        'duration': TEST_CONFIG['MEDIUM_AUDIO_DURATION']
    },
    'cpu_processing': {
        'description': 'CPU-only processing',
        'model': 'demucs',
        'device': 'cpu',
        'duration': TEST_CONFIG['SHORT_AUDIO_DURATION']
    }
}
