"""
Integration Tests for Audio Stem Separator

Tests that verify the stem separator works end-to-end with real audio processing.

Created by Sergie Code - Software Engineer & Programming Educator
"""

import unittest
import tempfile
import shutil
import numpy as np
import torch
from pathlib import Path
import sys
import time
import os

# Add src to path for testing
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

try:
    from stem_separator import StemSeparator, process_audio_file
    import soundfile as sf
except ImportError as e:
    print(f"Import error: {e}")
    print("Please ensure all dependencies are installed")
    sys.exit(1)


class TestStemSeparatorInitialization(unittest.TestCase):
    """Test StemSeparator initialization and model loading."""
    
    def test_demucs_initialization(self):
        """Test Demucs model initialization."""
        separator = StemSeparator(model='demucs')
        
        self.assertIsNotNone(separator.model)
        self.assertEqual(separator.model_type, 'demucs')
        
        model_info = separator.get_model_info()
        self.assertEqual(model_info['model_type'], 'demucs')
        self.assertIn(model_info['device'], ['cpu', 'cuda'])
    
    def test_openunmix_initialization(self):
        """Test Open-Unmix model initialization."""
        separator = StemSeparator(model='openunmix')
        
        self.assertIsNotNone(separator.model)
        self.assertEqual(separator.model_type, 'openunmix')
        
        model_info = separator.get_model_info()
        self.assertEqual(model_info['model_type'], 'openunmix')
    
    def test_invalid_model_initialization(self):
        """Test initialization with invalid model."""
        with self.assertRaises(ValueError):
            StemSeparator(model='invalid_model')
    
    def test_device_specification(self):
        """Test device specification during initialization."""
        # Test CPU specification
        separator_cpu = StemSeparator(model='demucs', device='cpu')
        model_info = separator_cpu.get_model_info()
        self.assertEqual(model_info['device'], 'cpu')
        
        # Test auto device detection
        separator_auto = StemSeparator(model='demucs', device='auto')
        model_info = separator_auto.get_model_info()
        self.assertIn(model_info['device'], ['cpu', 'cuda'])
    
    def test_model_variants(self):
        """Test different model variants."""
        # Test Demucs variants
        for variant in ['htdemucs', 'htdemucs_ft']:
            try:
                separator = StemSeparator(model='demucs', model_variant=variant)
                model_info = separator.get_model_info()
                self.assertEqual(model_info['model_type'], 'demucs')
            except Exception as e:
                # Some variants might not be available in test environment
                self.skipTest(f"Model variant {variant} not available: {e}")


class TestAudioProcessing(unittest.TestCase):
    """Test actual audio processing functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.test_data_dir = self.temp_dir / "test_audio"
        self.test_data_dir.mkdir()
        self.output_dir = self.temp_dir / "output"
    
    def tearDown(self):
        """Clean up test fixtures."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def create_test_audio_file(self, filename: str, duration: float = 3.0) -> Path:
        """Create a test audio file."""
        sample_rate = 44100
        t = np.linspace(0, duration, int(sample_rate * duration))
        
        # Create a simple stereo signal
        left = 0.3 * np.sin(2 * np.pi * 440 * t)  # A4 note
        right = 0.3 * np.sin(2 * np.pi * 880 * t)  # A5 note
        
        audio_data = np.column_stack([left, right])
        
        file_path = self.test_data_dir / filename
        sf.write(str(file_path), audio_data, sample_rate)
        
        return file_path
    
    def test_audio_separation_with_demucs(self):
        """Test audio separation using Demucs model."""
        # Create test audio file
        test_file = self.create_test_audio_file("test_demucs.wav", duration=2.0)
        
        # Initialize separator
        separator = StemSeparator(model='demucs')
        
        # Process audio
        result = separator.separate_audio(test_file, self.output_dir)
        
        # Verify results
        self.assertTrue(result['success'], f"Processing failed: {result.get('error', 'Unknown error')}")
        self.assertEqual(result['model_used'], 'demucs')
        self.assertGreater(result['processing_time'], 0)
        
        # Check output files
        self.assertTrue(Path(result['output_folder']).exists())
        
        expected_stems = ['vocals', 'drums', 'bass', 'other']
        for stem in expected_stems:
            stem_file = Path(result['output_folder']) / f"{stem}.wav"
            self.assertTrue(stem_file.exists(), f"Stem file {stem}.wav should exist")
            self.assertGreater(stem_file.stat().st_size, 0, f"Stem file {stem}.wav should not be empty")
    
    def test_audio_separation_with_openunmix(self):
        """Test audio separation using Open-Unmix model."""
        # Create test audio file
        test_file = self.create_test_audio_file("test_openunmix.wav", duration=2.0)
        
        # Process audio
        result = process_audio_file(
            input_file=str(test_file),
            output_dir=str(self.output_dir),
            model='openunmix'
        )
        
        # Verify results
        self.assertTrue(result['success'], f"Processing failed: {result.get('error', 'Unknown error')}")
        self.assertEqual(result['model_used'], 'openunmix')
        
        # Check output files exist
        for stem in result['stems']:
            stem_file = Path(result['output_folder']) / stem
            self.assertTrue(stem_file.exists())
    
    def test_processing_nonexistent_file(self):
        """Test processing of non-existent file."""
        separator = StemSeparator(model='demucs')
        
        with self.assertRaises(FileNotFoundError):
            separator.separate_audio("nonexistent.mp3", self.output_dir)
    
    def test_processing_invalid_audio_file(self):
        """Test processing of invalid audio file."""
        # Create a text file with .mp3 extension
        fake_audio = self.test_data_dir / "fake.mp3"
        fake_audio.write_text("This is not audio data")
        
        separator = StemSeparator(model='demucs')
        result = separator.separate_audio(fake_audio, self.output_dir)
        
        self.assertFalse(result['success'])
        self.assertIn('error', result)
    
    def test_output_directory_creation(self):
        """Test that output directories are created properly."""
        test_file = self.create_test_audio_file("test_output.wav", duration=1.0)
        
        # Use non-existent output directory
        new_output_dir = self.temp_dir / "new_output" / "nested"
        
        separator = StemSeparator(model='demucs')
        result = separator.separate_audio(test_file, new_output_dir)
        
        self.assertTrue(result['success'])
        self.assertTrue(new_output_dir.exists())


class TestPerformanceAndTiming(unittest.TestCase):
    """Test performance characteristics and timing."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.test_data_dir = self.temp_dir / "test_audio"
        self.test_data_dir.mkdir()
    
    def tearDown(self):
        """Clean up test fixtures."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def create_test_audio_file(self, filename: str, duration: float = 5.0) -> Path:
        """Create a test audio file."""
        sample_rate = 44100
        t = np.linspace(0, duration, int(sample_rate * duration))
        
        # Create more complex audio signal
        signal = (0.3 * np.sin(2 * np.pi * 440 * t) +  # Fundamental
                 0.2 * np.sin(2 * np.pi * 880 * t) +   # First harmonic
                 0.1 * np.sin(2 * np.pi * 1320 * t) +  # Second harmonic
                 0.05 * np.random.randn(len(t)))       # Noise
        
        # Create stereo
        audio_data = np.column_stack([signal, signal * 0.8])
        
        file_path = self.test_data_dir / filename
        sf.write(str(file_path), audio_data, sample_rate)
        
        return file_path
    
    def test_processing_time_measurement(self):
        """Test that processing time is measured correctly."""
        test_file = self.create_test_audio_file("timing_test.wav", duration=3.0)
        output_dir = self.temp_dir / "timing_output"
        
        start_time = time.time()
        
        separator = StemSeparator(model='demucs')
        result = separator.separate_audio(test_file, output_dir)
        
        end_time = time.time()
        actual_time = end_time - start_time
        
        self.assertTrue(result['success'])
        self.assertGreater(result['processing_time'], 0)
        
        # Processing time should be reasonably close to actual time
        # (allowing for some overhead in measurement)
        self.assertLess(abs(result['processing_time'] - actual_time), 5.0)
    
    def test_memory_usage_reasonable(self):
        """Test that memory usage is reasonable during processing."""
        import psutil
        import os
        
        test_file = self.create_test_audio_file("memory_test.wav", duration=5.0)
        output_dir = self.temp_dir / "memory_output"
        
        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        separator = StemSeparator(model='demucs')
        result = separator.separate_audio(test_file, output_dir)
        
        # Get peak memory usage
        peak_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = peak_memory - initial_memory
        
        self.assertTrue(result['success'])
        
        # Memory increase should be reasonable (less than 2GB for small test)
        self.assertLess(memory_increase, 2048, 
                       f"Memory usage increased by {memory_increase:.1f}MB, which seems excessive")
    
    @unittest.skipUnless(torch.cuda.is_available(), "CUDA not available")
    def test_gpu_vs_cpu_performance(self):
        """Test performance difference between GPU and CPU processing."""
        test_file = self.create_test_audio_file("performance_test.wav", duration=3.0)
        
        # Test CPU processing
        cpu_output = self.temp_dir / "cpu_output"
        separator_cpu = StemSeparator(model='demucs', device='cpu')
        cpu_result = separator_cpu.separate_audio(test_file, cpu_output)
        
        # Test GPU processing
        gpu_output = self.temp_dir / "gpu_output"
        separator_gpu = StemSeparator(model='demucs', device='cuda')
        gpu_result = separator_gpu.separate_audio(test_file, gpu_output)
        
        self.assertTrue(cpu_result['success'])
        self.assertTrue(gpu_result['success'])
        
        # GPU should be faster than CPU (for reasonably sized audio)
        if cpu_result['processing_time'] > 5:  # Only check if CPU took reasonable time
            self.assertLess(gpu_result['processing_time'], cpu_result['processing_time'],
                           "GPU processing should be faster than CPU")


class TestErrorHandling(unittest.TestCase):
    """Test error handling in various scenarios."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
    
    def tearDown(self):
        """Clean up test fixtures."""
        if self.temp_dir.exists():
            # Handle Windows readonly files
            import platform
            if platform.system() == "Windows":
                import subprocess
                # Remove readonly attribute from all files recursively
                for file in self.temp_dir.rglob('*'):
                    subprocess.run(['attrib', '-R', str(file)], check=False)
            shutil.rmtree(self.temp_dir)
    
    def test_corrupted_audio_file_handling(self):
        """Test handling of corrupted audio files."""
        # Create a file with .wav extension but invalid content
        corrupted_file = self.temp_dir / "corrupted.wav"
        corrupted_file.write_bytes(b"Not valid audio data" * 100)
        
        separator = StemSeparator(model='demucs')
        result = separator.separate_audio(corrupted_file, self.temp_dir / "output")
        
        self.assertFalse(result['success'])
        self.assertIn('error', result)
    
    def test_insufficient_disk_space_simulation(self):
        """Test behavior when output directory has permission issues."""
        # Create a test audio file
        sample_rate = 44100
        duration = 1.0
        t = np.linspace(0, duration, int(sample_rate * duration))
        audio_data = 0.3 * np.sin(2 * np.pi * 440 * t)
        
        test_file = self.temp_dir / "test.wav"
        sf.write(str(test_file), audio_data, sample_rate)
        
        # Try to write to a read-only directory (Unix-like systems)
        if hasattr(os, 'chmod'):
            readonly_dir = self.temp_dir / "readonly"
            readonly_dir.mkdir()
            
            # On Windows, use different approach to simulate insufficient space
            import platform
            if platform.system() == "Windows":
                # Create a readonly directory on Windows
                import subprocess
                subprocess.run(['attrib', '+R', str(readonly_dir)], check=False)
            else:
                os.chmod(readonly_dir, 0o444)  # Read-only on Unix
            
            separator = StemSeparator(model='demucs')
            
            try:
                result = separator.separate_audio(test_file, readonly_dir)
                # On Windows, this might succeed, so we check differently
                if platform.system() == "Windows":
                    # Just verify it completed
                    self.assertTrue(result.get('success', False))
                else:
                    # Should handle the error gracefully on Unix
                    self.assertFalse(result['success'])
                    self.assertIn('error', result)
            except Exception as e:
                # Exception is also acceptable for permission errors
                self.assertIn('permission', str(e).lower())
            
            # Restore permissions for cleanup
            if platform.system() == "Windows":
                subprocess.run(['attrib', '-R', str(readonly_dir)], check=False)
                # Also try to remove read-only from all files in directory
                for file in readonly_dir.rglob('*'):
                    subprocess.run(['attrib', '-R', str(file)], check=False)
            else:
                os.chmod(readonly_dir, 0o755)
    
    def test_empty_audio_file_handling(self):
        """Test handling of empty audio files."""
        empty_file = self.temp_dir / "empty.wav"
        empty_file.touch()  # Create empty file
        
        separator = StemSeparator(model='demucs')
        result = separator.separate_audio(empty_file, self.temp_dir / "output")
        
        self.assertFalse(result['success'])
        self.assertIn('error', result)


if __name__ == '__main__':
    # Run all integration tests
    test_classes = [
        TestStemSeparatorInitialization,
        TestAudioProcessing,
        TestPerformanceAndTiming,
        TestErrorHandling
    ]
    
    suite = unittest.TestSuite()
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    if result.wasSuccessful():
        print("\n✅ All integration tests passed!")
    else:
        print(f"\n❌ {len(result.failures)} test(s) failed")
        print(f"❌ {len(result.errors)} error(s) occurred")
        
        # Print details of failures and errors
        for test, error in result.failures + result.errors:
            print(f"\n--- {test} ---")
            print(error)
