# API Documentation

## Python API

### StemSeparator Class

The main class for audio stem separation.

#### Constructor

```python
StemSeparator(model='demucs', model_variant=None, device=None)
```

**Parameters:**
- `model` (str): Model type ('demucs' or 'openunmix')
- `model_variant` (str, optional): Specific model variant
- `device` (str, optional): Device to use ('cuda', 'cpu', or 'auto')

#### Methods

##### `separate_audio(input_file, output_dir)`

Separate an audio file into stems.

**Parameters:**
- `input_file` (str/Path): Path to input audio file
- `output_dir` (str/Path): Output directory for stems

**Returns:**
```python
{
    'success': bool,
    'input_file': str,
    'output_folder': str,
    'model_used': str,
    'processing_time': float,
    'stems': List[str]
}
```

##### `get_model_info()`

Get information about the loaded model.

**Returns:**
```python
{
    'model_type': str,
    'model_variant': str,
    'device': str,
    'supported_variants': List[str]
}
```

### Utility Functions

#### `process_audio_file(input_file, output_dir, model='demucs', device=None)`

Convenience function for one-off processing.

## Command Line API

### Basic Usage

```bash
python -m src.main --input INPUT --output OUTPUT [OPTIONS]
```

### Options

- `--input, -i`: Input audio file path (required)
- `--output, -o`: Output directory (required)
- `--model, -m`: Model choice (demucs/openunmix)
- `--device, -d`: Processing device (cuda/cpu/auto)
- `--model-variant`: Specific model variant
- `--verbose, -v`: Enable verbose logging
- `--quiet, -q`: Suppress output except JSON result

### Output Format

JSON response format:
```json
{
    "success": true,
    "input_file": "path/to/input.mp3",
    "output_folder": "path/to/output",
    "model_used": "demucs",
    "processing_time": 45.2,
    "stems": ["vocals.wav", "drums.wav", "bass.wav", "other.wav"]
}
```

## Node.js Integration API

### Basic Function

```javascript
separateAudioStems(inputFile, outputDir, options)
```

**Parameters:**
- `inputFile` (string): Path to input audio file
- `outputDir` (string): Output directory path  
- `options` (object): Processing options
  - `model`: 'demucs' or 'openunmix'
  - `device`: 'auto', 'cuda', or 'cpu'
  - `verbose`: boolean

**Returns:** Promise resolving to processing result

### Express.js Integration

```javascript
const app = createExpressApp();

// POST /api/separate-stems
// - Upload audio file
// - Returns processing result with download URLs

// GET /api/download/:sessionId/:filename  
// - Download separated stem files

// GET /api/models
// - Get available models and information

// GET /api/health
// - Health check endpoint
```

### WebSocket Support

```javascript
// Real-time progress updates
socket.on('progress', (data) => {
    console.log(`Progress: ${data.percentage}%`);
});

socket.emit('start-separation', {
    inputFile: 'path/to/audio.mp3',
    outputDir: './output',
    options: { model: 'demucs' }
});
```

## Error Handling

### Common Error Codes

- `FILE_NOT_FOUND`: Input file doesn't exist
- `PROCESSING_ERROR`: Error during audio separation
- `UNEXPECTED_ERROR`: Unexpected system error
- `TIMEOUT`: Processing timed out

### Error Response Format

```json
{
    "success": false,
    "error": "Error message",
    "code": "ERROR_CODE",
    "input_file": "path/to/input",
    "output_folder": "path/to/output"
}
```

## Performance Guidelines

### GPU vs CPU

| Device | Speed | Quality | Requirements |
|--------|-------|---------|-------------|
| CUDA GPU | 20-50x faster | Same | NVIDIA GPU |
| CPU | Baseline | Same | Any system |

### Model Comparison

| Model | Quality | Speed | Best For |
|-------|---------|-------|----------|
| Demucs | Excellent | Slower | Professional use |
| Open-Unmix | Good | Faster | Quick processing |

### Optimization Tips

1. **Use GPU when available**
2. **Process shorter clips for testing**
3. **Choose appropriate model for use case**
4. **Ensure sufficient RAM (4GB+ recommended)**
5. **Use SSD storage for better I/O**
