# Node.js Backend Integration Guide for Audio Stem Separator

*Created by Sergie Code - Software Engineer & Programming Educator*

This guide provides comprehensive instructions for integrating the Audio Stem Separator with Node.js backends, including Express.js APIs, real-time processing, and production deployment.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Project Setup](#project-setup)
3. [Basic Integration](#basic-integration)
4. [Express.js API Implementation](#expressjs-api-implementation)
5. [File Upload Handling](#file-upload-handling)
6. [Real-time Processing with WebSockets](#real-time-processing-with-websockets)
7. [Production Deployment](#production-deployment)
8. [Error Handling](#error-handling)
9. [Performance Optimization](#performance-optimization)
10. [Testing](#testing)

## Prerequisites

Before starting, ensure you have:

- **Node.js 14+** installed
- **Python 3.8+** with the Audio Stem Separator dependencies
- Basic knowledge of Node.js and Express.js
- Understanding of asynchronous JavaScript

## Project Setup

### 1. Initialize Node.js Project

```bash
# Create new Node.js project (if starting from scratch)
mkdir my-music-api
cd my-music-api
npm init -y

# Install dependencies
npm install express multer cors helmet morgan winston
npm install --save-dev nodemon jest supertest
```

### 2. Install Audio Stem Separator Dependencies

```bash
# Navigate to the audio-stem-separator directory
cd path/to/audio-stem-separator

# Install Python dependencies
pip install -r requirements.txt

# Test the separator works
python -m src.main --help
```

### 3. Project Structure

Create the following structure for your Node.js backend:

```
my-music-api/
├── src/
│   ├── controllers/
│   │   └── audioController.js
│   ├── middleware/
│   │   ├── upload.js
│   │   └── validation.js
│   ├── routes/
│   │   └── audioRoutes.js
│   ├── services/
│   │   └── stemSeparatorService.js
│   └── utils/
│       └── logger.js
├── uploads/
├── outputs/
├── tests/
├── server.js
└── package.json
```

## Basic Integration

### Core Service Implementation

Create `src/services/stemSeparatorService.js`:

```javascript
const { exec } = require('child_process');
const fs = require('fs').promises;
const path = require('path');
const util = require('util');

const execAsync = util.promisify(exec);

class StemSeparatorService {
    constructor() {
        this.config = {
            pythonPath: 'python', // Adjust based on your system
            projectPath: path.join(__dirname, '../../../audio-stem-separator'),
            defaultModel: 'demucs',
            timeout: 300000, // 5 minutes
            maxFileSize: 500 * 1024 * 1024 // 500MB
        };
    }

    /**
     * Separate audio into stems
     * @param {string} inputFile - Path to input audio file
     * @param {string} outputDir - Output directory
     * @param {object} options - Processing options
     */
    async separateStems(inputFile, outputDir, options = {}) {
        const {
            model = this.config.defaultModel,
            device = 'auto',
            verbose = false
        } = options;

        // Validate input file exists
        try {
            await fs.access(inputFile);
        } catch (error) {
            throw new Error(`Input file not found: ${inputFile}`);
        }

        // Create output directory if it doesn't exist
        await fs.mkdir(outputDir, { recursive: true });

        // Build command
        const args = [
            '-m', 'src.main',
            '--input', `"${inputFile}"`,
            '--output', `"${outputDir}"`,
            '--model', model,
            '--device', device
        ];

        if (!verbose) {
            args.push('--quiet');
        }

        const command = `${this.config.pythonPath} ${args.join(' ')}`;

        try {
            console.log(`🎵 Processing: ${path.basename(inputFile)}`);
            console.log(`📁 Output: ${outputDir}`);
            console.log(`🤖 Model: ${model}`);

            const { stdout, stderr } = await execAsync(command, {
                cwd: this.config.projectPath,
                timeout: this.config.timeout,
                maxBuffer: 1024 * 1024 * 10 // 10MB buffer
            });

            // Parse JSON result
            const result = JSON.parse(stdout);
            
            if (result.success) {
                console.log(`✅ Separation completed in ${result.processing_time}s`);
                
                // Add file URLs to result
                result.files = await this.getOutputFiles(outputDir, result.stems);
            }

            return result;

        } catch (error) {
            if (error.code === 'TIMEOUT') {
                throw new Error('Audio processing timed out. Try with a shorter audio file.');
            }

            // Try to parse error as JSON
            try {
                const errorResult = JSON.parse(error.stdout || error.stderr);
                return errorResult;
            } catch {
                throw new Error(`Processing failed: ${error.message}`);
            }
        }
    }

    /**
     * Get output file paths and create download URLs
     */
    async getOutputFiles(outputDir, stemNames) {
        const files = {};
        
        for (const stem of stemNames) {
            const filePath = path.join(outputDir, `${stem}.wav`);
            try {
                await fs.access(filePath);
                files[stem] = {
                    path: filePath,
                    url: `/download/${path.basename(outputDir)}/${stem}.wav`,
                    exists: true
                };
            } catch {
                files[stem] = {
                    path: filePath,
                    url: null,
                    exists: false
                };
            }
        }

        return files;
    }

    /**
     * Check if the service is available
     */
    async healthCheck() {
        try {
            const { stdout } = await execAsync(`${this.config.pythonPath} -m src.main --help`, {
                cwd: this.config.projectPath,
                timeout: 10000
            });
            return { available: true, message: 'Service is ready' };
        } catch (error) {
            return { available: false, message: error.message };
        }
    }
}

module.exports = StemSeparatorService;
```

## Express.js API Implementation

### Main Server Setup

Create `server.js`:

```javascript
const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const morgan = require('morgan');
const path = require('path');

const audioRoutes = require('./src/routes/audioRoutes');
const logger = require('./src/utils/logger');

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(helmet());
app.use(cors());
app.use(morgan('combined'));
app.use(express.json());

// Static files for downloads
app.use('/download', express.static(path.join(__dirname, 'outputs')));

// Routes
app.use('/api/audio', audioRoutes);

// Health check
app.get('/health', async (req, res) => {
    const StemSeparatorService = require('./src/services/stemSeparatorService');
    const service = new StemSeparatorService();
    
    const health = await service.healthCheck();
    
    res.status(health.available ? 200 : 503).json({
        status: health.available ? 'healthy' : 'unhealthy',
        message: health.message,
        timestamp: new Date().toISOString()
    });
});

// Error handling middleware
app.use((error, req, res, next) => {
    logger.error('Unhandled error:', error);
    res.status(500).json({
        success: false,
        error: 'Internal server error',
        message: process.env.NODE_ENV === 'development' ? error.message : undefined
    });
});

// 404 handler
app.use('*', (req, res) => {
    res.status(404).json({
        success: false,
        error: 'Endpoint not found'
    });
});

app.listen(PORT, () => {
    logger.info(`🎵 Audio Stem Separator API running on port ${PORT}`);
});

module.exports = app;
```

### Audio Routes

Create `src/routes/audioRoutes.js`:

```javascript
const express = require('express');
const upload = require('../middleware/upload');
const audioController = require('../controllers/audioController');
const validation = require('../middleware/validation');

const router = express.Router();

// Upload and process audio file
router.post('/separate', 
    upload.single('audio'),
    validation.validateAudioFile,
    audioController.separateStems
);

// Get processing status
router.get('/status/:jobId', audioController.getStatus);

// List available models
router.get('/models', audioController.getModels);

// Download separated stem
router.get('/download/:jobId/:stem', audioController.downloadStem);

module.exports = router;
```

### Audio Controller

Create `src/controllers/audioController.js`:

```javascript
const StemSeparatorService = require('../services/stemSeparatorService');
const logger = require('../utils/logger');
const path = require('path');
const fs = require('fs').promises;
const { v4: uuidv4 } = require('uuid');

// In-memory job storage (use Redis in production)
const jobs = new Map();

class AudioController {
    constructor() {
        this.stemService = new StemSeparatorService();
    }

    /**
     * Separate audio stems
     */
    async separateStems(req, res) {
        try {
            if (!req.file) {
                return res.status(400).json({
                    success: false,
                    error: 'No audio file provided'
                });
            }

            const jobId = uuidv4();
            const { model = 'demucs', device = 'auto' } = req.body;
            
            const inputFile = req.file.path;
            const outputDir = path.join(__dirname, '../../outputs', jobId);

            // Store job info
            jobs.set(jobId, {
                id: jobId,
                status: 'processing',
                inputFile: req.file.originalname,
                model,
                device,
                startTime: new Date(),
                progress: 0
            });

            // Start processing (don't wait for completion)
            this.processAudioAsync(jobId, inputFile, outputDir, { model, device })
                .catch(error => {
                    logger.error(`Job ${jobId} failed:`, error);
                    jobs.set(jobId, {
                        ...jobs.get(jobId),
                        status: 'failed',
                        error: error.message,
                        endTime: new Date()
                    });
                });

            res.json({
                success: true,
                jobId,
                message: 'Processing started',
                statusUrl: `/api/audio/status/${jobId}`
            });

        } catch (error) {
            logger.error('Error in separateStems:', error);
            res.status(500).json({
                success: false,
                error: 'Processing failed',
                message: error.message
            });
        }
    }

    /**
     * Process audio asynchronously
     */
    async processAudioAsync(jobId, inputFile, outputDir, options) {
        try {
            const result = await this.stemService.separateStems(inputFile, outputDir, options);
            
            if (result.success) {
                jobs.set(jobId, {
                    ...jobs.get(jobId),
                    status: 'completed',
                    result,
                    endTime: new Date(),
                    progress: 100
                });
            } else {
                jobs.set(jobId, {
                    ...jobs.get(jobId),
                    status: 'failed',
                    error: result.error,
                    endTime: new Date()
                });
            }

            // Cleanup input file
            await fs.unlink(inputFile).catch(() => {});

        } catch (error) {
            throw error;
        }
    }

    /**
     * Get job status
     */
    async getStatus(req, res) {
        const { jobId } = req.params;
        const job = jobs.get(jobId);

        if (!job) {
            return res.status(404).json({
                success: false,
                error: 'Job not found'
            });
        }

        res.json({
            success: true,
            job: {
                id: job.id,
                status: job.status,
                progress: job.progress,
                inputFile: job.inputFile,
                model: job.model,
                startTime: job.startTime,
                endTime: job.endTime,
                result: job.status === 'completed' ? job.result : undefined,
                error: job.error
            }
        });
    }

    /**
     * Get available models
     */
    async getModels(req, res) {
        res.json({
            success: true,
            models: [
                {
                    name: 'demucs',
                    description: 'High quality separation, slower processing',
                    default: true
                },
                {
                    name: 'openunmix',
                    description: 'Good quality, faster processing',
                    default: false
                }
            ]
        });
    }

    /**
     * Download separated stem
     */
    async downloadStem(req, res) {
        const { jobId, stem } = req.params;
        const job = jobs.get(jobId);

        if (!job || job.status !== 'completed') {
            return res.status(404).json({
                success: false,
                error: 'Job not found or not completed'
            });
        }

        const stemFile = path.join(__dirname, '../../outputs', jobId, `${stem}.wav`);
        
        try {
            await fs.access(stemFile);
            res.download(stemFile, `${stem}.wav`);
        } catch (error) {
            res.status(404).json({
                success: false,
                error: 'Stem file not found'
            });
        }
    }
}

module.exports = new AudioController();
```

## File Upload Handling

Create `src/middleware/upload.js`:

```javascript
const multer = require('multer');
const path = require('path');
const fs = require('fs');

// Ensure upload directory exists
const uploadDir = path.join(__dirname, '../../uploads');
if (!fs.existsSync(uploadDir)) {
    fs.mkdirSync(uploadDir, { recursive: true });
}

const storage = multer.diskStorage({
    destination: (req, file, cb) => {
        cb(null, uploadDir);
    },
    filename: (req, file, cb) => {
        const uniqueSuffix = Date.now() + '-' + Math.round(Math.random() * 1E9);
        cb(null, file.fieldname + '-' + uniqueSuffix + path.extname(file.originalname));
    }
});

const fileFilter = (req, file, cb) => {
    const allowedTypes = [
        'audio/mpeg',
        'audio/wav',
        'audio/flac',
        'audio/m4a',
        'audio/aac',
        'audio/ogg'
    ];

    if (allowedTypes.includes(file.mimetype)) {
        cb(null, true);
    } else {
        cb(new Error('Invalid file type. Only audio files are allowed.'), false);
    }
};

const upload = multer({
    storage,
    fileFilter,
    limits: {
        fileSize: 500 * 1024 * 1024 // 500MB limit
    }
});

module.exports = upload;
```

Create `src/middleware/validation.js`:

```javascript
const fs = require('fs').promises;
const path = require('path');

const validateAudioFile = async (req, res, next) => {
    try {
        if (!req.file) {
            return res.status(400).json({
                success: false,
                error: 'No audio file provided'
            });
        }

        const { model, device } = req.body;

        // Validate model
        const allowedModels = ['demucs', 'openunmix'];
        if (model && !allowedModels.includes(model)) {
            return res.status(400).json({
                success: false,
                error: `Invalid model. Allowed models: ${allowedModels.join(', ')}`
            });
        }

        // Validate device
        const allowedDevices = ['auto', 'cpu', 'cuda'];
        if (device && !allowedDevices.includes(device)) {
            return res.status(400).json({
                success: false,
                error: `Invalid device. Allowed devices: ${allowedDevices.join(', ')}`
            });
        }

        // Check file size
        const stats = await fs.stat(req.file.path);
        if (stats.size === 0) {
            await fs.unlink(req.file.path).catch(() => {});
            return res.status(400).json({
                success: false,
                error: 'Uploaded file is empty'
            });
        }

        next();

    } catch (error) {
        if (req.file) {
            await fs.unlink(req.file.path).catch(() => {});
        }
        
        res.status(500).json({
            success: false,
            error: 'File validation failed',
            message: error.message
        });
    }
};

module.exports = {
    validateAudioFile
};
```

## Real-time Processing with WebSockets

For real-time updates, add Socket.IO support. Install dependencies:

```bash
npm install socket.io
```

Update `server.js` to include WebSocket support:

```javascript
const { createServer } = require('http');
const { Server } = require('socket.io');

// After creating express app
const server = createServer(app);
const io = new Server(server, {
    cors: {
        origin: "*",
        methods: ["GET", "POST"]
    }
});

// WebSocket connection handling
io.on('connection', (socket) => {
    console.log('Client connected:', socket.id);

    socket.on('subscribe-job', (jobId) => {
        socket.join(`job-${jobId}`);
        console.log(`Client ${socket.id} subscribed to job ${jobId}`);
    });

    socket.on('disconnect', () => {
        console.log('Client disconnected:', socket.id);
    });
});

// Make io available to other modules
app.set('io', io);

// Update listen to use server instead of app
server.listen(PORT, () => {
    logger.info(`🎵 Audio Stem Separator API running on port ${PORT}`);
});
```

Update the audio controller to emit real-time updates:

```javascript
// In processAudioAsync method, add progress updates
async processAudioAsync(jobId, inputFile, outputDir, options) {
    const io = require('../../server').app?.get('io');
    
    try {
        // Emit processing started
        io?.to(`job-${jobId}`).emit('job-update', {
            jobId,
            status: 'processing',
            progress: 10,
            message: 'Starting audio separation...'
        });

        const result = await this.stemService.separateStems(inputFile, outputDir, options);
        
        if (result.success) {
            jobs.set(jobId, {
                ...jobs.get(jobId),
                status: 'completed',
                result,
                endTime: new Date(),
                progress: 100
            });

            // Emit completion
            io?.to(`job-${jobId}`).emit('job-update', {
                jobId,
                status: 'completed',
                progress: 100,
                message: 'Separation completed successfully!',
                result
            });
        }
    } catch (error) {
        // Emit error
        io?.to(`job-${jobId}`).emit('job-update', {
            jobId,
            status: 'failed',
            progress: 0,
            message: error.message
        });
        throw error;
    }
}
```

## Frontend Integration Example

Here's a simple HTML client to test your API:

```html
<!DOCTYPE html>
<html>
<head>
    <title>Audio Stem Separator</title>
    <script src="/socket.io/socket.io.js"></script>
</head>
<body>
    <h1>Audio Stem Separator</h1>
    
    <form id="uploadForm" enctype="multipart/form-data">
        <input type="file" id="audioFile" accept="audio/*" required>
        <select id="model">
            <option value="demucs">Demucs (High Quality)</option>
            <option value="openunmix">Open-Unmix (Fast)</option>
        </select>
        <button type="submit">Separate Stems</button>
    </form>

    <div id="status"></div>
    <div id="results"></div>

    <script>
        const socket = io();
        const form = document.getElementById('uploadForm');
        const statusDiv = document.getElementById('status');
        const resultsDiv = document.getElementById('results');

        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const formData = new FormData();
            formData.append('audio', document.getElementById('audioFile').files[0]);
            formData.append('model', document.getElementById('model').value);

            try {
                statusDiv.innerHTML = 'Uploading...';
                
                const response = await fetch('/api/audio/separate', {
                    method: 'POST',
                    body: formData
                });

                const result = await response.json();
                
                if (result.success) {
                    statusDiv.innerHTML = `Processing started. Job ID: ${result.jobId}`;
                    
                    // Subscribe to real-time updates
                    socket.emit('subscribe-job', result.jobId);
                } else {
                    statusDiv.innerHTML = `Error: ${result.error}`;
                }
            } catch (error) {
                statusDiv.innerHTML = `Error: ${error.message}`;
            }
        });

        // Handle real-time updates
        socket.on('job-update', (data) => {
            statusDiv.innerHTML = `
                Status: ${data.status}<br>
                Progress: ${data.progress}%<br>
                Message: ${data.message}
            `;

            if (data.status === 'completed' && data.result) {
                resultsDiv.innerHTML = '<h3>Download Stems:</h3>';
                Object.keys(data.result.files).forEach(stem => {
                    if (data.result.files[stem].exists) {
                        resultsDiv.innerHTML += `
                            <a href="${data.result.files[stem].url}" download>
                                Download ${stem}.wav
                            </a><br>
                        `;
                    }
                });
            }
        });
    </script>
</body>
</html>
```

## Production Deployment

### Environment Configuration

Create `.env` file:

```env
NODE_ENV=production
PORT=3000
PYTHON_PATH=python3
SEPARATOR_PROJECT_PATH=/app/audio-stem-separator
MAX_FILE_SIZE=500000000
UPLOAD_TIMEOUT=300000
LOG_LEVEL=info
```

### Docker Support

Create `Dockerfile`:

```dockerfile
FROM node:18-slim

# Install Python and system dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy and install Node.js dependencies
COPY package*.json ./
RUN npm ci --only=production

# Copy audio-stem-separator
COPY audio-stem-separator/ ./audio-stem-separator/
RUN cd audio-stem-separator && pip3 install -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p uploads outputs

EXPOSE 3000

CMD ["node", "server.js"]
```

### PM2 Configuration

Create `ecosystem.config.js`:

```javascript
module.exports = {
    apps: [{
        name: 'audio-stem-separator-api',
        script: 'server.js',
        instances: 1, // Don't use cluster mode due to file processing
        autorestart: true,
        watch: false,
        max_memory_restart: '2G',
        env: {
            NODE_ENV: 'production',
            PORT: 3000
        }
    }]
};
```

## Testing

Create `tests/api.test.js`:

```javascript
const request = require('supertest');
const app = require('../server');
const path = require('path');

describe('Audio Stem Separator API', () => {
    test('Health check should return 200', async () => {
        const response = await request(app)
            .get('/health')
            .expect(200);

        expect(response.body.status).toBe('healthy');
    });

    test('Should return available models', async () => {
        const response = await request(app)
            .get('/api/audio/models')
            .expect(200);

        expect(response.body.success).toBe(true);
        expect(response.body.models).toBeInstanceOf(Array);
    });

    test('Should reject non-audio files', async () => {
        const response = await request(app)
            .post('/api/audio/separate')
            .attach('audio', path.join(__dirname, 'fixtures/test.txt'))
            .expect(400);

        expect(response.body.success).toBe(false);
    });
});
```

## Best Practices

### 1. Error Handling
- Always validate input files
- Implement proper timeout handling
- Use structured logging
- Provide meaningful error messages

### 2. Performance
- Implement file cleanup after processing
- Use streaming for large files
- Consider implementing job queues for high load
- Monitor memory usage

### 3. Security
- Validate file types and sizes
- Sanitize file names
- Implement rate limiting
- Use HTTPS in production

### 4. Monitoring
- Log all processing events
- Monitor processing times
- Track success/failure rates
- Set up alerts for failures

## API Usage Examples

### Basic Upload and Processing

```bash
curl -X POST http://localhost:3000/api/audio/separate \
  -F "audio=@song.mp3" \
  -F "model=demucs"
```

### Check Job Status

```bash
curl http://localhost:3000/api/audio/status/job-id-here
```

### Download Stems

```bash
curl -O http://localhost:3000/api/audio/download/job-id-here/vocals
```

## Troubleshooting

### Common Issues

1. **Python not found**: Ensure Python path is correct in configuration
2. **Model download fails**: Check internet connection and disk space
3. **Processing timeout**: Increase timeout for larger files
4. **Memory issues**: Monitor RAM usage, consider processing limits

### Debug Mode

Enable debug logging:

```javascript
// In your service
console.log('Processing command:', command);
console.log('Working directory:', this.config.projectPath);
```

---

*This integration guide was created by Sergie Code for musicians and developers building AI-powered audio tools. For more programming tutorials, visit my YouTube channel!*

## Contributing

Feel free to submit issues, feature requests, and improvements. This project is designed to help musicians and developers create amazing audio applications.

## License

MIT License - Feel free to use this in your projects, both personal and commercial.