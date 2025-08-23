"""
Command Line Interface for Audio Stem Separator

This module provides a command-line interface for the audio stem separator,
allowing easy integration with external services and direct usage from terminal.

Created by Sergie Code - Software Engineer & Programming Educator
"""

import argparse
import json
import sys
from pathlib import Path

# Add src directory to path for imports
sys.path.append(str(Path(__file__).parent))

from stem_separator import StemSeparator, process_audio_file


def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description="Audio Stem Separator - Separate audio tracks into individual stems",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python -m src.main --input song.mp3 --output ./stems
    python -m src.main --input song.wav --output ./output --model openunmix
    python -m src.main --input music.flac --output ./separated --model demucs --device cuda

Supported Models:
    demucs (default) - High quality, slower processing
    openunmix        - Good quality, faster processing

Output:
    Results are printed as JSON for easy integration with other services.
        """
    )
    
    # Required arguments
    parser.add_argument(
        '--input', '-i',
        type=str,
        required=True,
        help='Path to the input audio file (MP3, WAV, FLAC, etc.)'
    )
    
    parser.add_argument(
        '--output', '-o',
        type=str,
        required=True,
        help='Directory where separated stems will be saved'
    )
    
    # Optional arguments
    parser.add_argument(
        '--model', '-m',
        type=str,
        default='demucs',
        choices=['demucs', 'openunmix'],
        help='AI model to use for separation (default: demucs)'
    )
    
    parser.add_argument(
        '--device', '-d',
        type=str,
        choices=['cuda', 'cpu', 'auto'],
        default='auto',
        help='Device to use for processing (default: auto)'
    )
    
    parser.add_argument(
        '--model-variant',
        type=str,
        help='Specific model variant to use (optional)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Suppress all output except JSON result'
    )
    
    args = parser.parse_args()
    
    # Set up logging based on arguments
    if args.quiet:
        import logging
        logging.getLogger().setLevel(logging.ERROR)
    elif args.verbose:
        import logging
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Process device argument
    device = None if args.device == 'auto' else args.device
    
    try:
        # Validate input file
        input_path = Path(args.input)
        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {args.input}")
        
        if not args.quiet:
            print(f"Processing: {input_path.name}", file=sys.stderr)
            print(f"Model: {args.model}", file=sys.stderr)
            print(f"Device: {device or 'auto-detect'}", file=sys.stderr)
            print("Starting separation...", file=sys.stderr)
        
        # Create separator and process audio
        if args.model_variant:
            separator = StemSeparator(
                model=args.model,
                model_variant=args.model_variant,
                device=device
            )
            result = separator.separate_audio(args.input, args.output)
        else:
            result = process_audio_file(
                input_file=args.input,
                output_dir=args.output,
                model=args.model,
                device=device
            )
        
        # Output result as JSON for easy parsing by external services
        print(json.dumps(result, indent=2))
        
        # Exit with appropriate code
        sys.exit(0 if result.get('success', False) else 1)
        
    except KeyboardInterrupt:
        error_result = {
            'success': False,
            'error': 'Process interrupted by user',
            'input_file': args.input,
            'output_folder': args.output
        }
        print(json.dumps(error_result, indent=2))
        sys.exit(1)
        
    except Exception as e:
        error_result = {
            'success': False,
            'error': str(e),
            'input_file': args.input,
            'output_folder': args.output
        }
        print(json.dumps(error_result, indent=2))
        sys.exit(1)


def validate_environment():
    """Validate that required dependencies are available."""
    missing_deps = []
    
    try:
        import torch
    except ImportError:
        missing_deps.append("torch")
    
    try:
        import torchaudio
    except ImportError:
        missing_deps.append("torchaudio")
    
    try:
        import demucs
    except ImportError:
        missing_deps.append("demucs")
    
    try:
        import openunmix
    except ImportError:
        missing_deps.append("openunmix-pytorch")
    
    try:
        import librosa
    except ImportError:
        missing_deps.append("librosa")
    
    try:
        import soundfile
    except ImportError:
        missing_deps.append("soundfile")
    
    if missing_deps:
        print("Error: Missing required dependencies:", file=sys.stderr)
        for dep in missing_deps:
            print(f"  - {dep}", file=sys.stderr)
        print("\nPlease install missing dependencies:", file=sys.stderr)
        print("  pip install -r requirements.txt", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    # Validate environment before proceeding
    validate_environment()
    main()
