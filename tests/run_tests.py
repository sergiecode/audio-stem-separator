"""
Comprehensive Test Runner for Audio Stem Separator

This script runs all tests and provides detailed reporting.

Created by Sergie Code - Software Engineer & Programming Educator
"""

import unittest
import sys
import time
from pathlib import Path
import importlib.util

# Add src to path for testing
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

# Test discovery
test_modules = [
    'test_utils',
    'test_integration', 
    'test_cli'
]

def check_dependencies():
    """Check if all required dependencies are available."""
    required_modules = [
        'torch',
        'torchaudio', 
        'demucs',
        'openunmix',
        'librosa',
        'soundfile',
        'numpy',
        'scipy'
    ]
    
    missing = []
    available = []
    
    for module in required_modules:
        try:
            importlib.import_module(module)
            available.append(module)
        except ImportError:
            missing.append(module)
    
    return available, missing

def run_basic_tests():
    """Run basic functionality tests without requiring audio files."""
    print("🧪 Running Basic Tests")
    print("=" * 50)
    
    # Check dependencies
    available, missing = check_dependencies()
    
    print(f"✅ Available modules: {', '.join(available)}")
    if missing:
        print(f"❌ Missing modules: {', '.join(missing)}")
        print("⚠️  Some tests may be skipped due to missing dependencies")
    
    # Test imports
    print("\n1. Testing Core Imports:")
    try:
        from stem_separator import StemSeparator
        print("   ✅ StemSeparator imported successfully")
        
        from utils import AudioFileValidator, OutputManager
        print("   ✅ Utility classes imported successfully")
        
        import main
        print("   ✅ CLI module imported successfully")
        
    except ImportError as e:
        print(f"   ❌ Import failed: {e}")
        return False
    
    # Test basic initialization
    print("\n2. Testing Model Initialization:")
    try:
        separator = StemSeparator(model='demucs')
        model_info = separator.get_model_info()
        print(f"   ✅ Demucs model initialized on {model_info['device']}")
        
        # Try Open-Unmix if available
        if 'openunmix' in available:
            separator_openunmix = StemSeparator(model='openunmix')
            print("   ✅ Open-Unmix model initialized")
        
    except Exception as e:
        print(f"   ❌ Model initialization failed: {e}")
        return False
    
    print("\n✅ Basic tests completed successfully!")
    return True

def run_unit_tests(verbosity=1):
    """Run unit tests."""
    print("\n🔬 Running Unit Tests")
    print("=" * 50)
    
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Load tests from test modules
    for module_name in test_modules:
        try:
            # Import test module
            spec = importlib.util.spec_from_file_location(
                module_name, 
                Path(__file__).parent / f"{module_name}.py"
            )
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # Load tests from module
                tests = loader.loadTestsFromModule(module)
                suite.addTests(tests)
                print(f"   ✅ Loaded tests from {module_name}")
        except Exception as e:
            print(f"   ⚠️  Could not load {module_name}: {e}")
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=verbosity, stream=sys.stdout)
    result = runner.run(suite)
    
    return result

def run_performance_tests():
    """Run performance benchmarks."""
    print("\n⚡ Running Performance Tests")
    print("=" * 50)
    
    try:
        import torch
        from stem_separator import StemSeparator
        
        # Device detection
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        print(f"   🖥️  Testing on: {device}")
        
        if device == 'cuda':
            gpu_name = torch.cuda.get_device_name()
            memory = torch.cuda.get_device_properties(0).total_memory / 1024**3
            print(f"   📊 GPU: {gpu_name} ({memory:.1f}GB)")
        
        # Model loading time
        start_time = time.time()
        separator = StemSeparator(model='demucs', device=device)
        load_time = time.time() - start_time
        print(f"   ⏱️  Model loading time: {load_time:.2f}s")
        
        # Memory usage
        import psutil
        import os
        process = psutil.Process(os.getpid())
        memory_mb = process.memory_info().rss / 1024 / 1024
        print(f"   💾 Current memory usage: {memory_mb:.1f}MB")
        
        print("   ✅ Performance tests completed")
        
    except Exception as e:
        print(f"   ❌ Performance tests failed: {e}")

def run_integration_tests():
    """Run integration tests with actual audio processing."""
    print("\n🔗 Running Integration Tests")
    print("=" * 50)
    
    try:
        # Check if we can create test audio
        import numpy as np
        try:
            import soundfile as sf
            can_create_audio = True
        except ImportError:
            can_create_audio = False
            print("   ⚠️  soundfile not available - skipping audio file tests")
        
        if can_create_audio:
            print("   ✅ Audio file generation available")
            
            # Test basic audio processing
            from stem_separator import StemSeparator
            import tempfile
            
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                # Create test audio
                sample_rate = 22050  # Lower sample rate for faster testing
                duration = 2.0  # Short duration
                t = np.linspace(0, duration, int(sample_rate * duration))
                audio = 0.3 * np.sin(2 * np.pi * 440 * t)  # Simple sine wave
                
                test_file = temp_path / "test.wav"
                sf.write(str(test_file), audio, sample_rate)
                
                output_dir = temp_path / "output"
                
                # Test processing
                separator = StemSeparator(model='demucs', device='cpu')  # Use CPU for speed
                result = separator.separate_audio(test_file, output_dir)
                
                if result['success']:
                    print(f"   ✅ Audio processing successful ({result['processing_time']:.1f}s)")
                    print(f"   📁 Generated stems: {len(result['stems'])}")
                else:
                    print(f"   ❌ Audio processing failed: {result.get('error', 'Unknown error')}")
        
    except Exception as e:
        print(f"   ❌ Integration tests failed: {e}")

def generate_test_report(test_result):
    """Generate a comprehensive test report."""
    print("\n📊 Test Report")
    print("=" * 50)
    
    total_tests = test_result.testsRun
    failures = len(test_result.failures)
    errors = len(test_result.errors)
    skipped = len(test_result.skipped) if hasattr(test_result, 'skipped') else 0
    passed = total_tests - failures - errors - skipped
    
    print(f"Total Tests: {total_tests}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failures}")
    print(f"🚫 Errors: {errors}")
    print(f"⏭️  Skipped: {skipped}")
    
    if total_tests > 0:
        success_rate = (passed / total_tests) * 100
        print(f"Success Rate: {success_rate:.1f}%")
    
    # Detailed failure information
    if failures > 0:
        print(f"\n❌ Test Failures ({failures}):")
        for test, traceback in test_result.failures:
            print(f"   - {test}")
    
    if errors > 0:
        print(f"\n🚫 Test Errors ({errors}):")
        for test, traceback in test_result.errors:
            print(f"   - {test}")
    
    return test_result.wasSuccessful()

def main():
    """Main test runner function."""
    print("🎵 Audio Stem Separator - Test Suite")
    print("Created by Sergie Code")
    print("=" * 60)
    
    start_time = time.time()
    
    # Command line arguments
    import argparse
    parser = argparse.ArgumentParser(description="Audio Stem Separator Test Runner")
    parser.add_argument('--basic', action='store_true', help='Run only basic tests')
    parser.add_argument('--unit', action='store_true', help='Run only unit tests')
    parser.add_argument('--integration', action='store_true', help='Run only integration tests')
    parser.add_argument('--performance', action='store_true', help='Run only performance tests')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--quick', action='store_true', help='Quick test run (basic + unit)')
    
    args = parser.parse_args()
    
    verbosity = 2 if args.verbose else 1
    test_result = None
    
    try:
        if args.basic or (not any([args.unit, args.integration, args.performance])):
            if not run_basic_tests():
                print("❌ Basic tests failed - aborting")
                return 1
        
        if args.unit or args.quick or (not any([args.basic, args.integration, args.performance])):
            test_result = run_unit_tests(verbosity)
        
        if args.performance and not args.quick:
            run_performance_tests()
        
        if args.integration and not args.quick:
            run_integration_tests()
        
        # Generate report
        if test_result:
            success = generate_test_report(test_result)
        else:
            success = True  # If we only ran basic tests
        
        total_time = time.time() - start_time
        print(f"\n⏱️  Total test time: {total_time:.1f}s")
        
        if success:
            print("\n🎉 All tests completed successfully!")
            return 0
        else:
            print("\n💥 Some tests failed!")
            return 1
            
    except KeyboardInterrupt:
        print("\n🛑 Tests interrupted by user")
        return 1
    except Exception as e:
        print(f"\n💥 Test runner error: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
