# Quick Start Guide

## Installation

1. **Clone/Download the project**
   ```bash
   git clone <repository-url>
   cd audio-stem-separator
   ```

2. **Run setup script**
   ```powershell
   # Windows
   .\setup.ps1
   
   # Linux/macOS
   chmod +x setup.sh
   ./setup.sh
   ```

## Basic Usage

### Command Line

```bash
# Activate virtual environment
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/macOS

# Basic separation
python -m src.main --input song.mp3 --output ./stems

# With specific model
python -m src.main --input song.wav --output ./output --model openunmix

# High quality processing
python -m src.main --input song.flac --output ./stems --model demucs --device cuda
```

### Python Integration

```python
from src.stem_separator import StemSeparator

# Initialize
separator = StemSeparator(model='demucs')

# Process audio
result = separator.separate_audio('song.mp3', './output')

if result['success']:
    print(f"Stems saved to: {result['output_folder']}")
    print(f"Processing time: {result['processing_time']}s")
```

### Node.js Integration

```javascript
const { separateAudioStems } = require('./examples/nodejs_integration');

async function processAudio() {
    const result = await separateAudioStems(
        './uploads/song.mp3',
        './output/stems'
    );
    
    console.log('Result:', result);
}
```

## Expected Output

After processing, you'll get:
- `vocals.wav` - Isolated vocals
- `drums.wav` - Isolated drums  
- `bass.wav` - Isolated bass
- `other.wav` - Other instruments

## Tips

- **GPU Processing**: Use `--device cuda` for 20-50x faster processing
- **Model Choice**: 
  - `demucs`: Higher quality, slower
  - `openunmix`: Good quality, faster
- **File Formats**: Supports MP3, WAV, FLAC, M4A, AAC
- **Memory**: Ensure 4GB+ RAM for best results

## Troubleshooting

### Common Issues

1. **"No module named 'torch'"**
   - Run: `pip install -r requirements.txt`

2. **Out of memory**
   - Use shorter audio clips
   - Use `--device cpu` instead of `cuda`

3. **"FFmpeg not found"**
   - Install FFmpeg: https://ffmpeg.org/download.html

4. **Slow processing**
   - Use GPU: `--device cuda`
   - Try `openunmix` model for speed

### Getting Help

- Check the full README.md for detailed documentation
- Run tests: `python test_basic.py --basic`
- Check examples in the `examples/` folder
