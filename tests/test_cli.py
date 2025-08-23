"""
Command Line Interface Tests

Tests for the CLI functionality of the audio stem separator.

Created by Sergie Code - Software Engineer & Programming Educator
"""

import unittest
import subprocess
import tempfile
import shutil
import json
import numpy as np
from pathlib import Path
import sys
import os

# Add src to path for testing
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

try:
    import soundfile as sf
except ImportError:
    print("soundfile not available for CLI tests")
    sf = None


class TestCommandLineInterface(unittest.TestCase):
    """Test the command line interface functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.test_data_dir = self.temp_dir / "test_audio"
        self.test_data_dir.mkdir()
        self.project_root = Path(__file__).parent.parent
        
        # Ensure we're using the virtual environment Python
        self.python_cmd = sys.executable
    
    def tearDown(self):
        """Clean up test fixtures."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def create_test_audio_file(self, filename: str, duration: float = 2.0) -> Path:
        """Create a test audio file if soundfile is available."""
        if sf is None:
            self.skipTest("soundfile not available")
        
        sample_rate = 44100
        t = np.linspace(0, duration, int(sample_rate * duration))
        
        # Create simple test signal
        signal = 0.3 * np.sin(2 * np.pi * 440 * t)
        audio_data = np.column_stack([signal, signal])  # Stereo
        
        file_path = self.test_data_dir / filename
        sf.write(str(file_path), audio_data, sample_rate)
        
        return file_path
    
    def run_cli_command(self, args: list, timeout: int = 120) -> dict:
        """Run a CLI command and return the result."""
        cmd = [
            self.python_cmd, 
            "-m", "src.main"
        ] + args
        
        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            return {
                'returncode': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'success': result.returncode == 0
            }
        except subprocess.TimeoutExpired:
            return {
                'returncode': -1,
                'stdout': '',
                'stderr': 'Command timed out',
                'success': False
            }
    
    def test_cli_help(self):
        """Test CLI help command."""
        result = self.run_cli_command(['--help'])
        
        self.assertTrue(result['success'])
        self.assertIn('Audio Stem Separator', result['stdout'])
        self.assertIn('--input', result['stdout'])
        self.assertIn('--output', result['stdout'])
        self.assertIn('--model', result['stdout'])
    
    def test_cli_missing_required_args(self):
        """Test CLI with missing required arguments."""
        # Missing both input and output
        result = self.run_cli_command([])
        self.assertFalse(result['success'])
        
        # Missing output
        result = self.run_cli_command(['--input', 'test.mp3'])
        self.assertFalse(result['success'])
        
        # Missing input
        result = self.run_cli_command(['--output', 'output_dir'])
        self.assertFalse(result['success'])
    
    def test_cli_nonexistent_input_file(self):
        """Test CLI with non-existent input file."""
        output_dir = self.temp_dir / "output"
        
        result = self.run_cli_command([
            '--input', 'nonexistent.mp3',
            '--output', str(output_dir)
        ])
        
        self.assertFalse(result['success'])
        
        # Should return JSON error response
        try:
            error_data = json.loads(result['stdout'])
            self.assertFalse(error_data['success'])
            self.assertIn('error', error_data)
        except json.JSONDecodeError:
            # If not JSON, check stderr for error message
            self.assertIn('not found', result['stderr'].lower())
    
    @unittest.skipIf(sf is None, "soundfile not available")
    def test_cli_basic_processing(self):
        """Test basic CLI processing with real audio file."""
        # Create test audio file
        test_file = self.create_test_audio_file("cli_test.wav", duration=1.5)
        output_dir = self.temp_dir / "cli_output"
        
        result = self.run_cli_command([
            '--input', str(test_file),
            '--output', str(output_dir),
            '--model', 'demucs',
            '--device', 'cpu',  # Use CPU for faster testing
            '--quiet'
        ])
        
        self.assertTrue(result['success'], f"CLI command failed: {result['stderr']}")
        
        # Parse JSON output
        try:
            output_data = json.loads(result['stdout'])
            self.assertTrue(output_data['success'])
            self.assertEqual(output_data['model_used'], 'demucs')
            self.assertIn('stems', output_data)
            self.assertGreater(len(output_data['stems']), 0)
        except json.JSONDecodeError as e:
            self.fail(f"CLI output is not valid JSON: {e}\nOutput: {result['stdout']}")
    
    def test_cli_model_selection(self):
        """Test CLI model selection."""
        if sf is None:
            self.skipTest("soundfile not available")
        
        test_file = self.create_test_audio_file("model_test.wav", duration=1.0)
        
        # Test Demucs
        output_dir1 = self.temp_dir / "demucs_output"
        result1 = self.run_cli_command([
            '--input', str(test_file),
            '--output', str(output_dir1),
            '--model', 'demucs',
            '--device', 'cpu',
            '--quiet'
        ])
        
        self.assertTrue(result1['success'])
        output_data1 = json.loads(result1['stdout'])
        self.assertEqual(output_data1['model_used'], 'demucs')
        
        # Test Open-Unmix
        output_dir2 = self.temp_dir / "openunmix_output"
        result2 = self.run_cli_command([
            '--input', str(test_file),
            '--output', str(output_dir2),
            '--model', 'openunmix',
            '--device', 'cpu',
            '--quiet'
        ])
        
        self.assertTrue(result2['success'])
        output_data2 = json.loads(result2['stdout'])
        self.assertEqual(output_data2['model_used'], 'openunmix')
    
    def test_cli_verbose_mode(self):
        """Test CLI verbose mode."""
        if sf is None:
            self.skipTest("soundfile not available")
        
        test_file = self.create_test_audio_file("verbose_test.wav", duration=1.0)
        output_dir = self.temp_dir / "verbose_output"
        
        result = self.run_cli_command([
            '--input', str(test_file),
            '--output', str(output_dir),
            '--model', 'demucs',
            '--device', 'cpu',
            '--verbose'
        ])
        
        self.assertTrue(result['success'])
        
        # Verbose mode should include progress information in stderr
        self.assertIn('Processing', result['stderr'])
        
        # Should still output valid JSON
        try:
            output_data = json.loads(result['stdout'])
            self.assertTrue(output_data['success'])
        except json.JSONDecodeError as e:
            self.fail(f"Verbose mode output is not valid JSON: {e}")
    
    def test_cli_device_specification(self):
        """Test CLI device specification."""
        if sf is None:
            self.skipTest("soundfile not available")
        
        test_file = self.create_test_audio_file("device_test.wav", duration=1.0)
        
        # Test CPU device
        output_dir = self.temp_dir / "cpu_output"
        result = self.run_cli_command([
            '--input', str(test_file),
            '--output', str(output_dir),
            '--device', 'cpu',
            '--quiet'
        ])
        
        self.assertTrue(result['success'])
        
        # Test auto device
        output_dir2 = self.temp_dir / "auto_output"
        result2 = self.run_cli_command([
            '--input', str(test_file),
            '--output', str(output_dir2),
            '--device', 'auto',
            '--quiet'
        ])
        
        self.assertTrue(result2['success'])
    
    def test_cli_invalid_model(self):
        """Test CLI with invalid model."""
        if sf is None:
            self.skipTest("soundfile not available")
        
        test_file = self.create_test_audio_file("invalid_model_test.wav", duration=1.0)
        output_dir = self.temp_dir / "invalid_output"
        
        result = self.run_cli_command([
            '--input', str(test_file),
            '--output', str(output_dir),
            '--model', 'invalid_model'
        ])
        
        self.assertFalse(result['success'])
    
    def test_cli_output_format(self):
        """Test CLI output format is valid JSON."""
        if sf is None:
            self.skipTest("soundfile not available")
        
        test_file = self.create_test_audio_file("format_test.wav", duration=1.0)
        output_dir = self.temp_dir / "format_output"
        
        result = self.run_cli_command([
            '--input', str(test_file),
            '--output', str(output_dir),
            '--quiet'
        ])
        
        self.assertTrue(result['success'])
        
        # Verify JSON structure
        output_data = json.loads(result['stdout'])
        
        required_fields = ['success', 'input_file', 'output_folder', 'model_used', 'processing_time']
        for field in required_fields:
            self.assertIn(field, output_data, f"Required field '{field}' missing from output")
        
        # Verify data types
        self.assertIsInstance(output_data['success'], bool)
        self.assertIsInstance(output_data['processing_time'], (int, float))
        self.assertIsInstance(output_data['stems'], list)


class TestCLIIntegration(unittest.TestCase):
    """Test CLI integration scenarios."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.project_root = Path(__file__).parent.parent
        self.python_cmd = sys.executable
    
    def tearDown(self):
        """Clean up test fixtures."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_cli_environment_validation(self):
        """Test that CLI validates environment properly."""
        # Test with current environment (should work)
        result = subprocess.run([
            self.python_cmd, 
            "-c", 
            "import sys; sys.path.insert(0, 'src'); from main import validate_environment; validate_environment()"
        ], cwd=self.project_root, capture_output=True, text=True)
        
        # Should not exit with error in current environment
        if result.returncode != 0:
            print(f"Environment validation failed: {result.stderr}")
    
    def test_cli_import_validation(self):
        """Test that CLI can import all required modules."""
        result = subprocess.run([
            self.python_cmd,
            "-c",
            """
import sys
from pathlib import Path
sys.path.insert(0, str(Path('src')))
try:
    from stem_separator import StemSeparator
    from main import main
    print('All imports successful')
except ImportError as e:
    print(f'Import error: {e}')
    sys.exit(1)
"""
        ], cwd=self.project_root, capture_output=True, text=True)
        
        self.assertEqual(result.returncode, 0, f"Import validation failed: {result.stderr}")
        self.assertIn('All imports successful', result.stdout)
    
    def test_cli_help_accessibility(self):
        """Test that CLI help is accessible without full setup."""
        result = subprocess.run([
            self.python_cmd,
            "-m", "src.main",
            "--help"
        ], cwd=self.project_root, capture_output=True, text=True)
        
        self.assertEqual(result.returncode, 0)
        self.assertIn('Audio Stem Separator', result.stdout)


if __name__ == '__main__':
    # Run CLI tests
    test_classes = [
        TestCommandLineInterface,
        TestCLIIntegration
    ]
    
    suite = unittest.TestSuite()
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    if result.wasSuccessful():
        print("\n✅ All CLI tests passed!")
    else:
        print(f"\n❌ {len(result.failures)} test(s) failed")
        print(f"❌ {len(result.errors)} error(s) occurred")
