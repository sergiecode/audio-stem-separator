# Audio Stem Separator

A Python-based audio stem separation tool that uses state-of-the-art AI models (Demucs and Open-Unmix) to separate music tracks into individual stems: vocals, drums, bass, and other instruments.

Created by **Sergie Code** - Software Engineer & Programming Educator

## Purpose

This project provides an easy-to-use interface for musicians, producers, and developers to separate audio tracks into individual stems using advanced AI models. Perfect for:

- Music production and remixing
- Karaoke track creation
- Audio analysis and processing
- Educational purposes in audio engineering

## Features

- **Multiple AI Models**: Support for both Demucs and Open-Unmix models
- **High-Quality Separation**: State-of-the-art source separation technology
- **Easy Integration**: Command-line interface for easy integration with other services
- **Flexible Output**: Customizable output directories and formats
- **Production Ready**: Designed to be called from external services (Node.js, APIs, etc.)

## Installation and Setup

### Prerequisites

- Python 3.8 or higher
- pip package manager
- At least 4GB of RAM (8GB+ recommended for better performance)
- CUDA-compatible GPU (optional, for faster processing)

### 1. Clone/Download the Project

```bash
git clone <your-repo-url>
cd audio-stem-separator
```

### 2. Create Virtual Environment (Recommended)

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

**Note**: First-time setup will download AI models (several GB). Ensure you have a stable internet connection and sufficient disk space.

## Usage

### Python Usage

```python
from src.stem_separator import StemSeparator

# Initialize the separator
separator = StemSeparator(model='demucs')

# Separate stems
output_folder = separator.separate_audio(
    input_file='path/to/your/song.mp3',
    output_dir='path/to/output/folder'
)

print(f"Stems saved to: {output_folder}")
```

### Command Line Usage

```bash
# Using Demucs (default)
python -m src.main --input "song.mp3" --output "output_folder"

# Using Open-Unmix
python -m src.main --input "song.mp3" --output "output_folder" --model "openunmix"

# With custom settings
python -m src.main --input "song.mp3" --output "output_folder" --model "demucs" --device "cuda"
```

## Integration with Node.js

### Basic Integration

```javascript
const { exec } = require('child_process');
const path = require('path');

function separateAudioStems(inputFile, outputDir, model = 'demucs') {
    return new Promise((resolve, reject) => {
        const command = `python -m src.main --input "${inputFile}" --output "${outputDir}" --model "${model}"`;
        
        exec(command, { cwd: 'path/to/audio-stem-separator' }, (error, stdout, stderr) => {
            if (error) {
                reject(error);
                return;
            }
            
            const result = JSON.parse(stdout);
            resolve(result);
        });
    });
}

// Usage example
async function processAudio() {
    try {
        const result = await separateAudioStems(
            './uploads/song.mp3',
            './output/stems',
            'demucs'
        );
        
        console.log('Separation complete:', result);
        console.log('Stems location:', result.output_folder);
        console.log('Available stems:', result.stems);
    } catch (error) {
        console.error('Error processing audio:', error);
    }
}
```

### Express.js API Example

```javascript
const express = require('express');
const multer = require('multer');
const path = require('path');

const app = express();
const upload = multer({ dest: 'uploads/' });

app.post('/separate-stems', upload.single('audio'), async (req, res) => {
    try {
        const inputFile = req.file.path;
        const outputDir = `./output/${Date.now()}`;
        const model = req.body.model || 'demucs';
        
        const result = await separateAudioStems(inputFile, outputDir, model);
        
        res.json({
            success: true,
            message: 'Audio separation completed',
            data: result
        });
    } catch (error) {
        res.status(500).json({
            success: false,
            message: 'Error processing audio',
            error: error.message
        });
    }
});
```

## Output Structure

After processing, you'll get the following stem files:

```
output_folder/
├── vocals.wav       # Isolated vocals
├── drums.wav        # Isolated drums
├── bass.wav         # Isolated bass
└── other.wav        # Other instruments (keyboards, guitar, etc.)
```

## Models Comparison

| Model | Quality | Speed | GPU Required | Best For |
|-------|---------|-------|--------------|----------|
| **Demucs** | High | Moderate | Recommended | Professional use, high-quality separation |
| **Open-Unmix** | Good | Fast | Optional | Quick processing, real-time applications |

## Environment Setup Notes

### GPU Acceleration (Optional but Recommended)

For faster processing, install CUDA-compatible PyTorch:

```bash
# For CUDA 11.8
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# For CPU only (slower)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
```

### Troubleshooting

1. **Memory Issues**: Reduce audio file length or use a machine with more RAM
2. **Model Download**: First run requires internet connection to download models
3. **Permissions**: Ensure write permissions for output directories
4. **Audio Format**: Supports MP3, WAV, FLAC, M4A, and most common formats

## Performance Tips

- Use GPU when available (20-50x faster than CPU)
- Process shorter audio clips for faster results
- Use SSD storage for better I/O performance
- Close unnecessary applications to free up RAM

## API Response Format

```json
{
    "success": true,
    "input_file": "path/to/input.mp3",
    "output_folder": "path/to/output/folder",
    "model_used": "demucs",
    "processing_time": 45.2,
    "stems": [
        "vocals.wav",
        "drums.wav", 
        "bass.wav",
        "other.wav"
    ]
}
```

## Contributing

This project is part of Sergie Code's educational content. Feel free to contribute improvements or report issues!

## License

MIT License - Feel free to use in your projects and tutorials.

---

**Created by Sergie Code** - Teaching programming and AI tools for musicians
- 📸 Instagram: https://www.instagram.com/sergiecode

- 🧑🏼‍💻 LinkedIn: https://www.linkedin.com/in/sergiecode/

- 📽️Youtube: https://www.youtube.com/@SergieCode

- 😺 Github: https://github.com/sergiecode

- 👤 Facebook: https://www.facebook.com/sergiecodeok

- 🎞️ Tiktok: https://www.tiktok.com/@sergiecode

- 🕊️Twitter: https://twitter.com/sergiecode

- 🧵Threads: https://www.threads.net/@sergiecode

