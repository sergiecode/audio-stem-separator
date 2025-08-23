"""
Audio Processing Utilities

Additional utility functions for audio processing and file handling.

Created by Sergie Code - Software Engineer & Programming Educator
"""

import os
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class AudioFileValidator:
    """Validates audio files and provides format information."""
    
    SUPPORTED_FORMATS = {
        '.mp3': 'MP3 Audio',
        '.wav': 'WAV Audio', 
        '.flac': 'FLAC Audio',
        '.m4a': 'M4A Audio',
        '.aac': 'AAC Audio',
        '.ogg': 'OGG Audio',
        '.wma': 'WMA Audio'
    }
    
    @classmethod
    def is_supported_format(cls, file_path: Path) -> bool:
        """Check if the file format is supported."""
        return file_path.suffix.lower() in cls.SUPPORTED_FORMATS
    
    @classmethod
    def get_format_info(cls, file_path: Path) -> Dict:
        """Get information about the audio file format."""
        suffix = file_path.suffix.lower()
        return {
            'extension': suffix,
            'format_name': cls.SUPPORTED_FORMATS.get(suffix, 'Unknown'),
            'is_supported': suffix in cls.SUPPORTED_FORMATS
        }
    
    @classmethod
    def validate_input_file(cls, file_path: Path) -> Dict:
        """Validate an input audio file."""
        result = {
            'valid': False,
            'exists': False,
            'readable': False,
            'supported_format': False,
            'file_size': 0,
            'format_info': {},
            'errors': []
        }
        
        try:
            # Check if file exists
            if not file_path.exists():
                result['errors'].append(f"File does not exist: {file_path}")
                return result
            result['exists'] = True
            
            # Check if file is readable
            if not os.access(file_path, os.R_OK):
                result['errors'].append(f"File is not readable: {file_path}")
                return result
            result['readable'] = True
            
            # Get file size
            result['file_size'] = file_path.stat().st_size
            
            # Check file format
            format_info = cls.get_format_info(file_path)
            result['format_info'] = format_info
            result['supported_format'] = format_info['is_supported']
            
            if not result['supported_format']:
                result['errors'].append(
                    f"Unsupported format: {format_info['extension']}. "
                    f"Supported formats: {list(cls.SUPPORTED_FORMATS.keys())}"
                )
                return result
            
            # Check file size (warn if too large)
            max_size_mb = 500  # 500MB warning threshold
            if result['file_size'] > max_size_mb * 1024 * 1024:
                logger.warning(f"Large file detected ({result['file_size'] / 1024 / 1024:.1f}MB). "
                             "Processing may take significant time and memory.")
            
            result['valid'] = True
            
        except Exception as e:
            result['errors'].append(f"Error validating file: {str(e)}")
        
        return result


class OutputManager:
    """Manages output directories and file organization."""
    
    @staticmethod
    def create_output_structure(base_dir: Path, input_filename: str) -> Path:
        """Create organized output directory structure."""
        # Create timestamped folder
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Clean input filename for folder name
        clean_name = Path(input_filename).stem
        clean_name = "".join(c for c in clean_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        
        output_dir = base_dir / f"{clean_name}_{timestamp}"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        return output_dir
    
    @staticmethod
    def prepare_output_directory(output_path: Path, create_subdirs: bool = True) -> Dict:
        """Prepare and validate output directory."""
        result = {
            'success': False,
            'path': output_path,
            'created': False,
            'writable': False,
            'errors': []
        }
        
        try:
            # Create directory if it doesn't exist
            if not output_path.exists():
                output_path.mkdir(parents=True, exist_ok=True)
                result['created'] = True
                logger.info(f"Created output directory: {output_path}")
            
            # Check if directory is writable
            test_file = output_path / ".write_test"
            try:
                test_file.touch()
                test_file.unlink()
                result['writable'] = True
            except Exception as e:
                result['errors'].append(f"Directory not writable: {e}")
                return result
            
            # Create subdirectories if requested
            if create_subdirs:
                (output_path / "stems").mkdir(exist_ok=True)
                (output_path / "metadata").mkdir(exist_ok=True)
            
            result['success'] = True
            
        except Exception as e:
            result['errors'].append(f"Error preparing output directory: {e}")
        
        return result
    
    @staticmethod
    def cleanup_temp_files(directory: Path, pattern: str = "*.tmp") -> int:
        """Clean up temporary files in directory."""
        count = 0
        try:
            for temp_file in directory.glob(pattern):
                temp_file.unlink()
                count += 1
            if count > 0:
                logger.info(f"Cleaned up {count} temporary files")
        except Exception as e:
            logger.warning(f"Error cleaning temporary files: {e}")
        
        return count


class MetadataManager:
    """Manages metadata for processed audio files."""
    
    @staticmethod
    def create_processing_metadata(input_file: Path, output_dir: Path, 
                                 model_info: Dict, processing_time: float,
                                 stems: List[str]) -> Dict:
        """Create comprehensive metadata for the processing session."""
        from datetime import datetime
        
        metadata = {
            'processing_info': {
                'timestamp': datetime.now().isoformat(),
                'input_file': {
                    'path': str(input_file),
                    'name': input_file.name,
                    'size_bytes': input_file.stat().st_size if input_file.exists() else 0,
                    'format': input_file.suffix.lower()
                },
                'output_directory': str(output_dir),
                'processing_time_seconds': processing_time,
                'model_info': model_info,
                'stems_generated': stems
            },
            'system_info': {
                'python_version': get_python_version(),
                'platform': get_platform_info()
            }
        }
        
        return metadata
    
    @staticmethod
    def save_metadata(metadata: Dict, output_dir: Path) -> Path:
        """Save metadata to JSON file."""
        import json
        
        metadata_file = output_dir / "processing_metadata.json"
        
        try:
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Metadata saved to: {metadata_file}")
            return metadata_file
            
        except Exception as e:
            logger.error(f"Failed to save metadata: {e}")
            raise


def get_python_version() -> str:
    """Get current Python version."""
    import sys
    return f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"


def get_platform_info() -> Dict:
    """Get platform information."""
    import platform
    
    return {
        'system': platform.system(),
        'release': platform.release(),
        'machine': platform.machine(),
        'processor': platform.processor()
    }


def estimate_processing_time(file_size_mb: float, model_type: str, 
                           device: str = 'cpu') -> Dict:
    """Estimate processing time based on file size and model."""
    # Rough estimates based on typical performance
    base_times = {
        'demucs': {'cpu': 30, 'cuda': 2},  # seconds per MB
        'openunmix': {'cpu': 15, 'cuda': 1}
    }
    
    multiplier = base_times.get(model_type, base_times['demucs']).get(device, 30)
    estimated_seconds = file_size_mb * multiplier
    
    return {
        'estimated_seconds': estimated_seconds,
        'estimated_minutes': estimated_seconds / 60,
        'estimated_readable': format_duration(estimated_seconds)
    }


def format_duration(seconds: float) -> str:
    """Format duration in human-readable format."""
    if seconds < 60:
        return f"{seconds:.1f} seconds"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f} minutes"
    else:
        hours = seconds / 3600
        return f"{hours:.1f} hours"


def get_available_models() -> Dict:
    """Get information about available models and their variants."""
    models_info = {
        'demucs': {
            'variants': ['htdemucs', 'htdemucs_ft', 'mdx_extra'],
            'description': 'High-quality separation, slower processing',
            'recommended_for': 'Professional use, high-quality output'
        },
        'openunmix': {
            'variants': ['umxhq', 'umx'],
            'description': 'Good quality separation, faster processing',
            'recommended_for': 'Quick processing, real-time applications'
        }
    }
    
    return models_info
