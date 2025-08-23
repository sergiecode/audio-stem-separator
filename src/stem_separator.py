"""
Audio Stem Separator - Core Module

This module provides the main functionality for separating audio stems using
Demucs and Open-Unmix models.

Created by Sergie Code - Software Engineer & Programming Educator
"""

import time
import logging
from pathlib import Path
from typing import Dict, List, Optional, Union, Tuple

import torch
import torchaudio
import numpy as np
from demucs import pretrained
from demucs.apply import apply_model
from openunmix import predict
import librosa
import soundfile as sf


# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StemSeparator:
    """
    A class for separating audio tracks into individual stems using AI models.
    
    Supports both Demucs and Open-Unmix models for high-quality source separation.
    """
    
    SUPPORTED_MODELS = {
        'demucs': ['htdemucs', 'htdemucs_ft', 'mdx_extra'],
        'openunmix': ['umxhq', 'umx']
    }
    
    STEM_NAMES = {
        'demucs': ['drums', 'bass', 'other', 'vocals'],
        'openunmix': ['drums', 'bass', 'other', 'vocals']
    }
    
    def __init__(self, model: str = 'demucs', model_variant: Optional[str] = None, 
                 device: Optional[str] = None):
        """
        Initialize the StemSeparator.
        
        Args:
            model: Model type ('demucs' or 'openunmix')
            model_variant: Specific model variant (optional)
            device: Device to use ('cuda', 'cpu', or auto-detect)
        """
        self.model_type = model.lower()
        self.device = self._setup_device(device)
        self.model = None
        self.model_variant = model_variant
        
        # Validate model type
        if self.model_type not in self.SUPPORTED_MODELS:
            raise ValueError(f"Unsupported model: {model}. Use {list(self.SUPPORTED_MODELS.keys())}")
        
        logger.info(f"Initializing {self.model_type} on {self.device}")
        self._load_model()
    
    def _setup_device(self, device: Optional[str] = None) -> str:
        """Setup and return the appropriate device for processing."""
        if device and device != "auto":
            return device
        
        if torch.cuda.is_available():
            device = 'cuda'
            logger.info(f"CUDA available. Using GPU: {torch.cuda.get_device_name()}")
        else:
            device = 'cpu'
            logger.info("CUDA not available. Using CPU (processing will be slower)")
        
        return device
    
    def _load_model(self):
        """Load the specified model."""
        try:
            if self.model_type == 'demucs':
                self._load_demucs_model()
            elif self.model_type == 'openunmix':
                self._load_openunmix_model()
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise
    
    def _load_demucs_model(self):
        """Load Demucs model."""
        model_name = self.model_variant or 'htdemucs'
        
        logger.info(f"Loading Demucs model: {model_name}")
        logger.info("First time setup may take several minutes to download models...")
        
        try:
            self.model = pretrained.get_model(model_name)
            self.model.to(self.device)
            self.model.eval()
            logger.info(f"Demucs model {model_name} loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load Demucs model {model_name}: {e}")
            # Fallback to basic model
            logger.info("Attempting to load fallback model...")
            self.model = pretrained.get_model('htdemucs')
            self.model.to(self.device)
            self.model.eval()
    
    def _load_openunmix_model(self):
        """Load Open-Unmix model."""
        model_name = self.model_variant or 'umxhq'
        
        logger.info(f"Loading Open-Unmix model: {model_name}")
        
        try:
            # Open-Unmix models are loaded during prediction
            self.model = model_name
            logger.info(f"Open-Unmix model {model_name} ready")
        except Exception as e:
            logger.error(f"Failed to setup Open-Unmix model {model_name}: {e}")
            raise
    
    def separate_audio(self, input_file: Union[str, Path], 
                      output_dir: Union[str, Path]) -> Dict:
        """
        Separate an audio file into individual stems.
        
        Args:
            input_file: Path to the input audio file
            output_dir: Directory to save the separated stems
            
        Returns:
            Dictionary with separation results and metadata
        """
        input_path = Path(input_file)
        output_path = Path(output_dir)
        
        # Validate input file
        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")
        
        # Create output directory
        output_path.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Processing: {input_path.name}")
        logger.info(f"Output directory: {output_path}")
        
        start_time = time.time()
        
        try:
            # Load audio
            audio_data, sample_rate = self._load_audio(input_path)
            
            # Separate stems
            if self.model_type == 'demucs':
                separated_stems = self._separate_with_demucs(audio_data, sample_rate)
            else:
                separated_stems = self._separate_with_openunmix(audio_data, sample_rate)
            
            # Save stems
            stem_files = self._save_stems(separated_stems, output_path, sample_rate)
            
            processing_time = time.time() - start_time
            
            result = {
                'success': True,
                'input_file': str(input_path),
                'output_folder': str(output_path),
                'model_used': self.model_type,
                'processing_time': round(processing_time, 2),
                'stems': stem_files
            }
            
            logger.info(f"Separation completed in {processing_time:.2f} seconds")
            return result
            
        except Exception as e:
            logger.error(f"Error during separation: {e}")
            return {
                'success': False,
                'error': str(e),
                'input_file': str(input_path),
                'output_folder': str(output_path)
            }
    
    def _load_audio(self, file_path: Path) -> Tuple[torch.Tensor, int]:
        """Load audio file and return tensor and sample rate."""
        try:
            # Try using torchaudio first
            audio, sample_rate = torchaudio.load(str(file_path))
            
            # Convert to mono if stereo
            if audio.shape[0] > 1:
                audio = torch.mean(audio, dim=0, keepdim=True)
            
            logger.info(f"Loaded audio: {audio.shape}, SR: {sample_rate}")
            return audio, sample_rate
            
        except Exception as e:
            logger.warning(f"torchaudio failed, trying librosa: {e}")
            
            # Fallback to librosa
            try:
                audio, sample_rate = librosa.load(str(file_path), sr=None, mono=True)
                audio_tensor = torch.from_numpy(audio).unsqueeze(0).float()
                return audio_tensor, sample_rate
            except Exception as e2:
                raise RuntimeError(f"Failed to load audio with both torchaudio and librosa: {e2}")
    
    def _separate_with_demucs(self, audio: torch.Tensor, sample_rate: int) -> Dict[str, torch.Tensor]:
        """Separate audio using Demucs model."""
        logger.info("Separating with Demucs...")
        
        # Ensure audio is in the right format for Demucs
        if audio.dim() == 2 and audio.shape[0] == 1:
            # Convert mono to stereo for better separation
            audio = audio.repeat(2, 1)
        elif audio.dim() == 1:
            audio = audio.unsqueeze(0).repeat(2, 1)
        
        # Add batch dimension
        audio = audio.unsqueeze(0).to(self.device)
        
        with torch.no_grad():
            separated = apply_model(self.model, audio)
        
        # Remove batch dimension and convert to CPU
        separated = separated.squeeze(0).cpu()
        
        # Map to stem names
        stem_names = self.STEM_NAMES['demucs']
        stems = {}
        
        for i, name in enumerate(stem_names):
            if i < separated.shape[0]:
                stems[name] = separated[i]
        
        return stems
    
    def _separate_with_openunmix(self, audio: torch.Tensor, sample_rate: int) -> Dict[str, torch.Tensor]:
        """Separate audio using Open-Unmix model."""
        logger.info("Separating with Open-Unmix...")
        
        try:
            # Use Open-Unmix predict function (expects torch tensor)
            estimates = predict.separate(
                audio,
                rate=sample_rate,
                model_str_or_path=self.model_variant or 'umxl',
                device=self.device
            )
            
            # Convert to our expected format
            stems = {}
            stem_names = self.STEM_NAMES['openunmix']
            
            for i, name in enumerate(stem_names):
                if name in estimates:
                    stems[name] = estimates[name]
            
            return stems
            
        except Exception as e:
            logger.error(f"Open-Unmix separation failed: {e}")
            raise
    
    def _save_stems(self, stems: Dict[str, torch.Tensor], 
                   output_dir: Path, sample_rate: int) -> List[str]:
        """Save separated stems to files."""
        stem_files = []
        
        for stem_name, stem_data in stems.items():
            filename = f"{stem_name}.wav"
            file_path = output_dir / filename
            
            try:
                # Ensure correct format for saving
                if stem_data.dim() == 2:
                    # Convert to mono by averaging channels
                    stem_data = torch.mean(stem_data, dim=0)
                
                # Convert to numpy and ensure it's in the right range
                stem_np = stem_data.detach().cpu().numpy().astype(np.float32)
                
                # Normalize to prevent clipping
                if np.max(np.abs(stem_np)) > 1.0:
                    stem_np = stem_np / np.max(np.abs(stem_np))
                
                # Save using soundfile
                sf.write(str(file_path), stem_np, sample_rate)
                stem_files.append(filename)
                
                logger.info(f"Saved: {filename}")
                
            except Exception as e:
                logger.error(f"Failed to save {stem_name}: {e}")
                continue
        
        return stem_files
    
    def get_model_info(self) -> Dict:
        """Get information about the current model."""
        return {
            'model_type': self.model_type,
            'model_variant': self.model_variant or 'default',
            'device': self.device,
            'supported_variants': self.SUPPORTED_MODELS[self.model_type]
        }


def process_audio_file(input_file: str, output_dir: str, 
                      model: str = 'demucs', device: str = None) -> Dict:
    """
    Convenience function for processing a single audio file.
    
    Args:
        input_file: Path to input audio file
        output_dir: Directory for output stems
        model: Model to use ('demucs' or 'openunmix')
        device: Device to use ('cuda', 'cpu', or None for auto)
    
    Returns:
        Dictionary with processing results
    """
    separator = StemSeparator(model=model, device=device)
    return separator.separate_audio(input_file, output_dir)
