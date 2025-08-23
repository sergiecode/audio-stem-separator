#!/usr/bin/env python3
"""
Demo Script for Audio Stem Separator

This script demonstrates the capabilities of the audio stem separator
without requiring actual audio files.

Created by Sergie Code - Software Engineer & Programming Educator
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def main():
    print("🎵 Audio Stem Separator Demo")
    print("Created by Sergie Code")
    print("=" * 50)
    
    try:
        from stem_separator import StemSeparator
        from utils import get_available_models, estimate_processing_time
        
        print("\n1. Available Models:")
        models = get_available_models()
        for model_name, info in models.items():
            print(f"   📦 {model_name.upper()}")
            print(f"      Description: {info['description']}")
            print(f"      Best for: {info['recommended_for']}")
            print(f"      Variants: {', '.join(info['variants'])}")
            print()
        
        print("2. Model Initialization:")
        separator = StemSeparator(model='demucs')
        model_info = separator.get_model_info()
        print(f"   ✅ Model: {model_info['model_type']}")
        print(f"   ✅ Variant: {model_info['model_variant']}")
        print(f"   ✅ Device: {model_info['device']}")
        print(f"   ✅ Supported variants: {', '.join(model_info['supported_variants'])}")
        
        print("\n3. Processing Time Estimates:")
        file_sizes = [10, 50, 100, 200]  # MB
        for size in file_sizes:
            cpu_time = estimate_processing_time(size, 'demucs', 'cpu')
            gpu_time = estimate_processing_time(size, 'demucs', 'cuda')
            
            print(f"   📁 {size}MB file:")
            print(f"      CPU: {cpu_time['estimated_readable']}")
            print(f"      GPU: {gpu_time['estimated_readable']}")
        
        print("\n4. Command Line Usage Examples:")
        examples = [
            "python -m src.main --input song.mp3 --output ./stems",
            "python -m src.main --input song.wav --output ./output --model openunmix",
            "python -m src.main --input music.flac --output ./separated --model demucs --device cuda"
        ]
        
        for i, example in enumerate(examples, 1):
            print(f"   Example {i}: {example}")
        
        print("\n5. Python Integration Example:")
        print("   ```python")
        print("   from src.stem_separator import StemSeparator")
        print("   ")
        print("   separator = StemSeparator(model='demucs')")
        print("   result = separator.separate_audio('song.mp3', './output')")
        print("   ")
        print("   if result['success']:")
        print("       print(f'Stems: {result[\"stems\"]}')")
        print("   ```")
        
        print("\n6. Node.js Integration Example:")
        print("   ```javascript")
        print("   const { separateAudioStems } = require('./examples/nodejs_integration');")
        print("   ")
        print("   const result = await separateAudioStems(")
        print("       './uploads/song.mp3',")
        print("       './output/stems'")
        print("   );")
        print("   ")
        print("   console.log('Result:', result);")
        print("   ```")
        
        print("\n✅ Demo completed successfully!")
        print("\nNext steps:")
        print("   1. Place an audio file in the project directory")
        print("   2. Run: python -m src.main --input your_file.mp3 --output ./test_output")
        print("   3. Check the ./test_output directory for separated stems")
        print("\nFor more examples, see the examples/ directory")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Please install dependencies: pip install -r requirements.txt")
        return 1
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
