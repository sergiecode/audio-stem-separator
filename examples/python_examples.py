"""
Python Usage Examples for Audio Stem Separator

This file demonstrates various ways to use the audio stem separator
in your Python applications.

Created by Sergie Code - Software Engineer & Programming Educator
"""

import sys
from pathlib import Path

# Add the src directory to the path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from stem_separator import StemSeparator, process_audio_file


def basic_usage_example():
    """Basic usage example with default settings."""
    print("=== Basic Usage Example ===")
    
    # Simple one-line processing
    result = process_audio_file(
        input_file="path/to/your/song.mp3",
        output_dir="./output/basic_example",
        model="demucs"
    )
    
    if result['success']:
        print(f"✅ Processing completed in {result['processing_time']} seconds")
        print(f"📁 Stems saved to: {result['output_folder']}")
        print(f"🎵 Generated stems: {', '.join(result['stems'])}")
    else:
        print(f"❌ Error: {result['error']}")


def advanced_usage_example():
    """Advanced usage with custom settings and error handling."""
    print("=== Advanced Usage Example ===")
    
    try:
        # Initialize separator with specific model
        separator = StemSeparator(
            model='demucs',
            model_variant='htdemucs_ft',  # High-quality variant
            device='cuda'  # Use GPU if available
        )
        
        # Get model information
        model_info = separator.get_model_info()
        print(f"Using model: {model_info['model_type']} ({model_info['model_variant']})")
        print(f"Device: {model_info['device']}")
        
        # Process audio file
        result = separator.separate_audio(
            input_file="path/to/your/song.wav",
            output_dir="./output/advanced_example"
        )
        
        # Handle results
        if result['success']:
            print(f"✅ Success! Processing time: {result['processing_time']}s")
            
            # List generated stems
            for stem in result['stems']:
                stem_path = Path(result['output_folder']) / stem
                print(f"🎵 {stem}: {stem_path}")
        else:
            print(f"❌ Processing failed: {result['error']}")
            
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


def batch_processing_example():
    """Process multiple audio files in batch."""
    print("=== Batch Processing Example ===")
    
    # List of input files
    input_files = [
        "path/to/song1.mp3",
        "path/to/song2.wav", 
        "path/to/song3.flac"
    ]
    
    # Initialize separator once for efficiency
    separator = StemSeparator(model='demucs', device='auto')
    
    results = []
    
    for i, input_file in enumerate(input_files, 1):
        print(f"Processing file {i}/{len(input_files)}: {Path(input_file).name}")
        
        # Create unique output directory for each file
        output_dir = f"./output/batch_processing/song_{i}"
        
        try:
            result = separator.separate_audio(input_file, output_dir)
            results.append(result)
            
            if result['success']:
                print(f"  ✅ Completed in {result['processing_time']}s")
            else:
                print(f"  ❌ Failed: {result['error']}")
                
        except Exception as e:
            print(f"  ❌ Error processing {input_file}: {e}")
            results.append({
                'success': False,
                'error': str(e),
                'input_file': input_file
            })
    
    # Summary
    successful = sum(1 for r in results if r.get('success', False))
    print(f"\n📊 Batch Summary: {successful}/{len(input_files)} files processed successfully")


def compare_models_example():
    """Compare different models on the same audio file."""
    print("=== Model Comparison Example ===")
    
    input_file = "path/to/your/test_song.mp3"
    models_to_test = ['demucs', 'openunmix']
    
    results = {}
    
    for model in models_to_test:
        print(f"\nTesting {model.upper()} model...")
        
        output_dir = f"./output/comparison/{model}"
        
        try:
            result = process_audio_file(
                input_file=input_file,
                output_dir=output_dir,
                model=model
            )
            
            results[model] = result
            
            if result['success']:
                print(f"  ✅ {model}: {result['processing_time']}s")
            else:
                print(f"  ❌ {model}: {result['error']}")
                
        except Exception as e:
            print(f"  ❌ {model}: {e}")
            results[model] = {'success': False, 'error': str(e)}
    
    # Compare results
    print("\n📊 Comparison Results:")
    for model, result in results.items():
        if result.get('success'):
            print(f"  {model.upper()}: {result['processing_time']}s")
        else:
            print(f"  {model.upper()}: Failed")


def custom_output_organization_example():
    """Example with custom output organization and metadata."""
    print("=== Custom Output Organization Example ===")
    
    from datetime import datetime
    import json
    
    # Custom output structure
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_output = Path(f"./output/session_{timestamp}")
    
    input_file = "path/to/your/song.mp3"
    song_name = Path(input_file).stem
    
    # Create organized directory structure
    stems_dir = base_output / "stems" / song_name
    metadata_dir = base_output / "metadata"
    
    stems_dir.mkdir(parents=True, exist_ok=True)
    metadata_dir.mkdir(parents=True, exist_ok=True)
    
    # Process audio
    separator = StemSeparator(model='demucs')
    result = separator.separate_audio(input_file, stems_dir)
    
    if result['success']:
        # Save custom metadata
        metadata = {
            'session_info': {
                'timestamp': timestamp,
                'song_name': song_name,
                'original_file': str(input_file)
            },
            'processing_result': result,
            'model_info': separator.get_model_info()
        }
        
        metadata_file = metadata_dir / f"{song_name}_metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"✅ Processing completed!")
        print(f"📁 Stems: {stems_dir}")
        print(f"📄 Metadata: {metadata_file}")
    else:
        print(f"❌ Processing failed: {result['error']}")


def integration_ready_function(input_file_path, output_directory, 
                              model_choice='demucs', use_gpu=True):
    """
    Production-ready function for integration with web services.
    
    Args:
        input_file_path (str): Path to input audio file
        output_directory (str): Directory for output stems
        model_choice (str): 'demucs' or 'openunmix'
        use_gpu (bool): Whether to use GPU if available
    
    Returns:
        dict: Processing results with detailed information
    """
    try:
        # Validate inputs
        input_path = Path(input_file_path)
        if not input_path.exists():
            return {
                'success': False,
                'error': f'Input file not found: {input_file_path}',
                'code': 'FILE_NOT_FOUND'
            }
        
        # Determine device
        device = 'cuda' if use_gpu else 'cpu'
        
        # Process audio
        result = process_audio_file(
            input_file=input_file_path,
            output_dir=output_directory,
            model=model_choice,
            device=device
        )
        
        # Add additional metadata for web service
        if result.get('success'):
            result['code'] = 'SUCCESS'
            result['stems_info'] = []
            
            output_path = Path(result['output_folder'])
            for stem_file in result['stems']:
                stem_path = output_path / stem_file
                if stem_path.exists():
                    result['stems_info'].append({
                        'name': stem_file,
                        'path': str(stem_path),
                        'size_bytes': stem_path.stat().st_size,
                        'relative_path': stem_file
                    })
        else:
            result['code'] = 'PROCESSING_ERROR'
        
        return result
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'code': 'UNEXPECTED_ERROR',
            'input_file': input_file_path,
            'output_folder': output_directory
        }


if __name__ == "__main__":
    """
    Run examples (commented out to prevent accidental execution).
    Uncomment and modify file paths to test.
    """
    
    print("Audio Stem Separator - Python Examples")
    print("Created by Sergie Code\n")
    
    # NOTE: Update file paths before running examples
    print("⚠️  Please update file paths in the examples before running!")
    print("Examples available:")
    print("- basic_usage_example()")
    print("- advanced_usage_example()")
    print("- batch_processing_example()")
    print("- compare_models_example()")
    print("- custom_output_organization_example()")
    
    # Uncomment to run specific examples:
    # basic_usage_example()
    # advanced_usage_example()
    # batch_processing_example()
    # compare_models_example()
    # custom_output_organization_example()
