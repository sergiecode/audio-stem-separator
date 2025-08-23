"""
Test Suite for Audio Stem Separator

Basic tests to validate the functionality of the stem separator.

Created by Sergie Code - Software Engineer & Programming Educator
"""

import unittest
import tempfile
import shutil
from pathlib import Path
import sys
import os

# Add src to path for testing
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

try:
    from stem_separator import StemSeparator
    from utils import AudioFileValidator, OutputManager
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure to install dependencies: pip install -r requirements.txt")
    sys.exit(1)


class TestAudioFileValidator(unittest.TestCase):
    """Test the audio file validator utility."""
    
    def test_supported_formats(self):
        """Test supported format detection."""
        test_files = [
            Path("test.mp3"),
            Path("test.wav"),
            Path("test.flac"),
            Path("test.m4a"),
            Path("test.xyz")  # unsupported
        ]
        
        expected_results = [True, True, True, True, False]
        
        for file_path, expected in zip(test_files, expected_results):
            with self.subTest(file=file_path):
                result = AudioFileValidator.is_supported_format(file_path)
                self.assertEqual(result, expected)
    
    def test_format_info(self):
        """Test format information extraction."""
        test_file = Path("test.mp3")
        info = AudioFileValidator.get_format_info(test_file)
        
        self.assertEqual(info['extension'], '.mp3')
        self.assertEqual(info['format_name'], 'MP3 Audio')
        self.assertTrue(info['is_supported'])


class TestOutputManager(unittest.TestCase):
    """Test the output manager utility."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
    
    def tearDown(self):
        """Clean up test fixtures."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_prepare_output_directory(self):
        """Test output directory preparation."""
        output_path = self.temp_dir / "test_output"
        result = OutputManager.prepare_output_directory(output_path)
        
        self.assertTrue(result['success'])
        self.assertTrue(result['created'])
        self.assertTrue(result['writable'])
        self.assertTrue(output_path.exists())


class TestStemSeparatorInitialization(unittest.TestCase):
    """Test stem separator initialization without actual processing."""
    
    def test_model_validation(self):
        """Test model validation."""
        # Valid models should not raise exceptions
        try:
            separator_demucs = StemSeparator(model='demucs')
            separator_openunmix = StemSeparator(model='openunmix')
            self.assertIsNotNone(separator_demucs)
            self.assertIsNotNone(separator_openunmix)
        except Exception as e:
            self.fail(f"Valid model initialization failed: {e}")
        
        # Invalid model should raise exception
        with self.assertRaises(ValueError):
            StemSeparator(model='invalid_model')
    
    def test_device_setup(self):
        """Test device setup."""
        separator = StemSeparator(model='demucs')
        device_info = separator.get_model_info()
        
        self.assertIn('device', device_info)
        self.assertIn(device_info['device'], ['cpu', 'cuda'])


class MockTests(unittest.TestCase):
    """Tests using mock data to avoid requiring actual audio files."""
    
    def setUp(self):
        """Set up mock test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.mock_audio_file = self.temp_dir / "test_audio.mp3"
        
        # Create a mock audio file (empty file for testing)
        self.mock_audio_file.touch()
    
    def tearDown(self):
        """Clean up test environment."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_file_validation(self):
        """Test file validation with mock file."""
        result = AudioFileValidator.validate_input_file(self.mock_audio_file)
        
        self.assertTrue(result['exists'])
        self.assertTrue(result['readable'])
        self.assertTrue(result['supported_format'])
        # Note: validation will pass, but actual processing would fail
        # since this is just an empty file


def create_test_suite():
    """Create and return a test suite."""
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTest(unittest.makeSuite(TestAudioFileValidator))
    suite.addTest(unittest.makeSuite(TestOutputManager))
    suite.addTest(unittest.makeSuite(TestStemSeparatorInitialization))
    suite.addTest(unittest.makeSuite(MockTests))
    
    return suite


def run_basic_tests():
    """Run basic functionality tests without requiring audio files."""
    print("🧪 Running Audio Stem Separator Tests")
    print("Created by Sergie Code")
    print("=" * 50)
    
    # Test import capabilities
    print("\n1. Testing imports...")
    try:
        import torch
        print(f"   ✅ PyTorch: {torch.__version__}")
        print(f"   ✅ CUDA available: {torch.cuda.is_available()}")
    except ImportError:
        print("   ❌ PyTorch not available")
        return False
    
    try:
        import demucs
        print("   ✅ Demucs available")
    except ImportError:
        print("   ❌ Demucs not available")
        return False
    
    try:
        import openunmix
        print("   ✅ Open-Unmix available")
    except ImportError:
        print("   ❌ Open-Unmix not available")
        return False
    
    # Test basic functionality
    print("\n2. Testing basic functionality...")
    try:
        separator = StemSeparator(model='demucs')
        model_info = separator.get_model_info()
        print(f"   ✅ Model initialized: {model_info['model_type']}")
        print(f"   ✅ Device: {model_info['device']}")
    except Exception as e:
        print(f"   ❌ Model initialization failed: {e}")
        return False
    
    # Test utilities
    print("\n3. Testing utilities...")
    try:
        validator = AudioFileValidator()
        result = validator.is_supported_format(Path("test.mp3"))
        if result:
            print("   ✅ File validation working")
        else:
            print("   ❌ File validation failed")
            return False
    except Exception as e:
        print(f"   ❌ Utility test failed: {e}")
        return False
    
    print("\n✅ All basic tests passed!")
    print("\nTo test with actual audio files:")
    print("  python -m src.main --input your_file.mp3 --output ./test_output")
    
    return True


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--basic":
        # Run basic tests without unittest framework
        success = run_basic_tests()
        sys.exit(0 if success else 1)
    else:
        # Run full unittest suite
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(create_test_suite())
        
        if result.wasSuccessful():
            print("\n✅ All tests passed!")
        else:
            print(f"\n❌ {len(result.failures)} test(s) failed")
            print(f"❌ {len(result.errors)} error(s) occurred")
        
        sys.exit(0 if result.wasSuccessful() else 1)
