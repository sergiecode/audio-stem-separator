"""
Unit Tests for Audio File Utilities

Tests for the utility functions including file validation, 
output management, and metadata handling.

Created by Sergie Code - Software Engineer & Programming Educator
"""

import unittest
import tempfile
import shutil
from pathlib import Path
import sys
import json
import os

# Add src to path for testing
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

try:
    from utils import (
        AudioFileValidator, 
        OutputManager, 
        MetadataManager,
        get_available_models,
        estimate_processing_time,
        format_duration,
        get_python_version,
        get_platform_info
    )
except ImportError as e:
    print(f"Import error: {e}")
    print("Please ensure dependencies are installed")


class TestAudioFileValidator(unittest.TestCase):
    """Test the AudioFileValidator class."""
    
    def test_supported_formats_detection(self):
        """Test detection of supported audio formats."""
        supported_files = [
            Path("test.mp3"),
            Path("test.wav"),
            Path("test.flac"),
            Path("test.m4a"),
            Path("test.aac"),
            Path("test.ogg")
        ]
        
        for file_path in supported_files:
            with self.subTest(file=file_path):
                self.assertTrue(
                    AudioFileValidator.is_supported_format(file_path),
                    f"{file_path.suffix} should be supported"
                )
    
    def test_unsupported_formats_detection(self):
        """Test detection of unsupported file formats."""
        unsupported_files = [
            Path("test.txt"),
            Path("test.pdf"),
            Path("test.doc"),
            Path("test.xyz"),
            Path("test.mp4"),  # video file
            Path("test.jpg")   # image file
        ]
        
        for file_path in unsupported_files:
            with self.subTest(file=file_path):
                self.assertFalse(
                    AudioFileValidator.is_supported_format(file_path),
                    f"{file_path.suffix} should not be supported"
                )
    
    def test_format_info_extraction(self):
        """Test extraction of format information."""
        test_file = Path("test.mp3")
        info = AudioFileValidator.get_format_info(test_file)
        
        self.assertEqual(info['extension'], '.mp3')
        self.assertEqual(info['format_name'], 'MP3 Audio')
        self.assertTrue(info['is_supported'])
        
        # Test unsupported format
        unsupported_file = Path("test.xyz")
        info = AudioFileValidator.get_format_info(unsupported_file)
        self.assertEqual(info['extension'], '.xyz')
        self.assertEqual(info['format_name'], 'Unknown')
        self.assertFalse(info['is_supported'])
    
    def test_validate_nonexistent_file(self):
        """Test validation of non-existent file."""
        nonexistent_file = Path("nonexistent.mp3")
        result = AudioFileValidator.validate_input_file(nonexistent_file)
        
        self.assertFalse(result['valid'])
        self.assertFalse(result['exists'])
        self.assertGreater(len(result['errors']), 0)
        self.assertIn("does not exist", result['errors'][0])


class TestOutputManager(unittest.TestCase):
    """Test the OutputManager class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
    
    def tearDown(self):
        """Clean up test fixtures."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_prepare_output_directory_creation(self):
        """Test creation of new output directory."""
        output_path = self.temp_dir / "new_output"
        result = OutputManager.prepare_output_directory(output_path)
        
        self.assertTrue(result['success'])
        self.assertTrue(result['created'])
        self.assertTrue(result['writable'])
        self.assertTrue(output_path.exists())
        self.assertEqual(len(result['errors']), 0)
    
    def test_prepare_existing_output_directory(self):
        """Test preparation of existing output directory."""
        output_path = self.temp_dir / "existing_output"
        output_path.mkdir()
        
        result = OutputManager.prepare_output_directory(output_path)
        
        self.assertTrue(result['success'])
        self.assertFalse(result['created'])  # Directory already existed
        self.assertTrue(result['writable'])
        self.assertEqual(len(result['errors']), 0)
    
    def test_create_output_structure(self):
        """Test creation of organized output structure."""
        input_filename = "test_song.mp3"
        output_dir = OutputManager.create_output_structure(self.temp_dir, input_filename)
        
        self.assertTrue(output_dir.exists())
        self.assertIn("test_song", output_dir.name)
        # Should contain timestamp
        self.assertRegex(output_dir.name, r"test_song_\d{8}_\d{6}")
    
    def test_cleanup_temp_files(self):
        """Test cleanup of temporary files."""
        # Create some temp files
        temp_files = [
            self.temp_dir / "file1.tmp",
            self.temp_dir / "file2.tmp",
            self.temp_dir / "file3.temp"
        ]
        
        for temp_file in temp_files:
            temp_file.touch()
        
        # Cleanup .tmp files
        count = OutputManager.cleanup_temp_files(self.temp_dir, "*.tmp")
        
        self.assertEqual(count, 2)  # Should clean 2 .tmp files
        self.assertFalse(temp_files[0].exists())
        self.assertFalse(temp_files[1].exists())
        self.assertTrue(temp_files[2].exists())  # .temp file should remain


class TestMetadataManager(unittest.TestCase):
    """Test the MetadataManager class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.test_input_file = self.temp_dir / "test.mp3"
        self.test_input_file.touch()  # Create empty file
        
        # Write some data to make it non-empty
        with open(self.test_input_file, 'wb') as f:
            f.write(b"fake mp3 data" * 100)
    
    def tearDown(self):
        """Clean up test fixtures."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_create_processing_metadata(self):
        """Test creation of processing metadata."""
        output_dir = self.temp_dir / "output"
        model_info = {
            'model_type': 'demucs',
            'model_variant': 'htdemucs',
            'device': 'cuda'
        }
        processing_time = 45.7
        stems = ['vocals.wav', 'drums.wav', 'bass.wav', 'other.wav']
        
        metadata = MetadataManager.create_processing_metadata(
            self.test_input_file, output_dir, model_info, processing_time, stems
        )
        
        # Check structure
        self.assertIn('processing_info', metadata)
        self.assertIn('system_info', metadata)
        
        # Check processing info
        proc_info = metadata['processing_info']
        self.assertEqual(proc_info['input_file']['name'], 'test.mp3')
        self.assertEqual(proc_info['processing_time_seconds'], processing_time)
        self.assertEqual(proc_info['model_info'], model_info)
        self.assertEqual(proc_info['stems_generated'], stems)
        
        # Check system info
        sys_info = metadata['system_info']
        self.assertIn('python_version', sys_info)
        self.assertIn('platform', sys_info)
    
    def test_save_metadata(self):
        """Test saving metadata to file."""
        output_dir = self.temp_dir / "output"
        output_dir.mkdir()
        
        test_metadata = {
            'test_key': 'test_value',
            'nested': {
                'key': 'value'
            }
        }
        
        metadata_file = MetadataManager.save_metadata(test_metadata, output_dir)
        
        self.assertTrue(metadata_file.exists())
        self.assertEqual(metadata_file.name, 'processing_metadata.json')
        
        # Verify content
        with open(metadata_file, 'r') as f:
            loaded_metadata = json.load(f)
        
        self.assertEqual(loaded_metadata, test_metadata)


class TestUtilityFunctions(unittest.TestCase):
    """Test standalone utility functions."""
    
    def test_get_available_models(self):
        """Test getting available model information."""
        models = get_available_models()
        
        self.assertIn('demucs', models)
        self.assertIn('openunmix', models)
        
        # Check structure of model info
        demucs_info = models['demucs']
        self.assertIn('variants', demucs_info)
        self.assertIn('description', demucs_info)
        self.assertIn('recommended_for', demucs_info)
        
        # Check variants
        self.assertIsInstance(demucs_info['variants'], list)
        self.assertIn('htdemucs', demucs_info['variants'])
    
    def test_estimate_processing_time(self):
        """Test processing time estimation."""
        file_size_mb = 50.0
        
        # Test Demucs CPU
        cpu_estimate = estimate_processing_time(file_size_mb, 'demucs', 'cpu')
        self.assertIn('estimated_seconds', cpu_estimate)
        self.assertIn('estimated_minutes', cpu_estimate)
        self.assertIn('estimated_readable', cpu_estimate)
        self.assertGreater(cpu_estimate['estimated_seconds'], 0)
        
        # Test Demucs GPU (should be faster)
        gpu_estimate = estimate_processing_time(file_size_mb, 'demucs', 'cuda')
        self.assertLess(gpu_estimate['estimated_seconds'], cpu_estimate['estimated_seconds'])
        
        # Test Open-Unmix (should be faster than Demucs)
        openunmix_estimate = estimate_processing_time(file_size_mb, 'openunmix', 'cpu')
        self.assertLess(openunmix_estimate['estimated_seconds'], cpu_estimate['estimated_seconds'])
    
    def test_format_duration(self):
        """Test duration formatting."""
        # Test seconds
        self.assertEqual(format_duration(30), "30.0 seconds")
        
        # Test minutes
        self.assertEqual(format_duration(90), "1.5 minutes")
        
        # Test hours
        self.assertEqual(format_duration(3661), "1.0 hours")
    
    def test_get_python_version(self):
        """Test Python version detection."""
        version = get_python_version()
        self.assertRegex(version, r"\d+\.\d+\.\d+")
        
        # Should match current Python version
        import sys
        expected = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        self.assertEqual(version, expected)
    
    def test_get_platform_info(self):
        """Test platform information detection."""
        platform_info = get_platform_info()
        
        required_keys = ['system', 'release', 'machine', 'processor']
        for key in required_keys:
            self.assertIn(key, platform_info)
            self.assertIsInstance(platform_info[key], str)


class TestFileOperations(unittest.TestCase):
    """Test file operation utilities."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
    
    def tearDown(self):
        """Clean up test fixtures."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_file_validation_with_real_file(self):
        """Test file validation with actual file."""
        # Create a test file
        test_file = self.temp_dir / "test.mp3"
        test_file.write_bytes(b"fake mp3 data" * 1000)  # Make it reasonably sized
        
        result = AudioFileValidator.validate_input_file(test_file)
        
        self.assertTrue(result['valid'])
        self.assertTrue(result['exists'])
        self.assertTrue(result['readable'])
        self.assertTrue(result['supported_format'])
        self.assertGreater(result['file_size'], 0)
        self.assertEqual(len(result['errors']), 0)
    
    def test_file_validation_permissions(self):
        """Test file validation with permission issues."""
        # Create a test file
        test_file = self.temp_dir / "test.mp3"
        test_file.write_text("test data")
        
        # Make file unreadable (platform-dependent)
        if os.name == 'posix':  # Unix-like systems
            os.chmod(test_file, 0o000)
            
            result = AudioFileValidator.validate_input_file(test_file)
            
            self.assertFalse(result['valid'])
            self.assertTrue(result['exists'])
            self.assertFalse(result['readable'])
            
            # Restore permissions for cleanup
            os.chmod(test_file, 0o644)


if __name__ == '__main__':
    # Run specific test classes
    test_classes = [
        TestAudioFileValidator,
        TestOutputManager,
        TestMetadataManager,
        TestUtilityFunctions,
        TestFileOperations
    ]
    
    suite = unittest.TestSuite()
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    if result.wasSuccessful():
        print("\n✅ All utility tests passed!")
    else:
        print(f"\n❌ {len(result.failures)} test(s) failed")
        print(f"❌ {len(result.errors)} error(s) occurred")
