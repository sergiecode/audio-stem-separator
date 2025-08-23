// Node.js Integration Examples for Audio Stem Separator
// 
// This file demonstrates how to integrate the Python audio stem separator
// with Node.js applications, including Express.js APIs.
//
// Created by Sergie Code - Software Engineer & Programming Educator

const { exec, spawn } = require('child_process');
const fs = require('fs').promises;
const path = require('path');
const util = require('util');

// Promisify exec for async/await usage
const execAsync = util.promisify(exec);

/**
 * Configuration for the audio stem separator
 */
const SEPARATOR_CONFIG = {
    pythonPath: 'python',  // or 'python3' on some systems
    projectPath: path.join(__dirname, '..'),  // Path to audio-stem-separator project
    defaultModel: 'demucs',
    timeout: 300000,  // 5 minutes timeout
    maxFileSize: 500 * 1024 * 1024  // 500MB max file size
};

/**
 * Basic function to separate audio stems
 * @param {string} inputFile - Path to input audio file
 * @param {string} outputDir - Directory for output stems
 * @param {object} options - Processing options
 * @returns {Promise<object>} Processing results
 */
async function separateAudioStems(inputFile, outputDir, options = {}) {
    const {
        model = SEPARATOR_CONFIG.defaultModel,
        device = 'auto',
        verbose = false
    } = options;

    // Validate input file
    try {
        await fs.access(inputFile);
    } catch (error) {
        throw new Error(`Input file not found: ${inputFile}`);
    }

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

    const command = `${SEPARATOR_CONFIG.pythonPath} ${args.join(' ')}`;

    console.log(`🎵 Processing: ${path.basename(inputFile)}`);
    console.log(`📁 Output: ${outputDir}`);
    console.log(`🤖 Model: ${model}`);

    try {
        const { stdout, stderr } = await execAsync(command, {
            cwd: SEPARATOR_CONFIG.projectPath,
            timeout: SEPARATOR_CONFIG.timeout,
            maxBuffer: 1024 * 1024 * 10  // 10MB buffer
        });

        // Parse JSON result
        const result = JSON.parse(stdout);
        
        if (result.success) {
            console.log(`✅ Separation completed in ${result.processing_time}s`);
        } else {
            console.error(`❌ Separation failed: ${result.error}`);
        }

        return result;

    } catch (error) {
        if (error.code === 'TIMEOUT') {
            throw new Error('Audio processing timed out. Try with a shorter audio file.');
        }

        // Try to parse error output as JSON
        try {
            const errorResult = JSON.parse(error.stdout || error.stderr);
            return errorResult;
        } catch {
            throw new Error(`Processing failed: ${error.message}`);
        }
    }
}

/**
 * Advanced function with progress tracking using spawn
 * @param {string} inputFile - Path to input audio file
 * @param {string} outputDir - Directory for output stems
 * @param {object} options - Processing options
 * @param {function} onProgress - Progress callback function
 * @returns {Promise<object>} Processing results
 */
function separateAudioStemsWithProgress(inputFile, outputDir, options = {}, onProgress = null) {
    return new Promise((resolve, reject) => {
        const {
            model = SEPARATOR_CONFIG.defaultModel,
            device = 'auto'
        } = options;

        const args = [
            '-m', 'src.main',
            '--input', inputFile,
            '--output', outputDir,
            '--model', model,
            '--device', device,
            '--verbose'
        ];

        const pythonProcess = spawn(SEPARATOR_CONFIG.pythonPath, args, {
            cwd: SEPARATOR_CONFIG.projectPath
        });

        let stdout = '';
        let stderr = '';

        pythonProcess.stdout.on('data', (data) => {
            const text = data.toString();
            stdout += text;

            // Extract progress information if callback provided
            if (onProgress) {
                // Look for progress indicators in the output
                const progressMatch = text.match(/(\d+)%/);
                if (progressMatch) {
                    onProgress({
                        type: 'progress',
                        percentage: parseInt(progressMatch[1]),
                        message: text.trim()
                    });
                } else {
                    onProgress({
                        type: 'info',
                        message: text.trim()
                    });
                }
            }
        });

        pythonProcess.stderr.on('data', (data) => {
            stderr += data.toString();
            
            if (onProgress) {
                onProgress({
                    type: 'warning',
                    message: data.toString().trim()
                });
            }
        });

        pythonProcess.on('close', (code) => {
            if (code === 0) {
                try {
                    // Extract JSON result from stdout
                    const jsonMatch = stdout.match(/\{[\s\S]*\}/);
                    if (jsonMatch) {
                        const result = JSON.parse(jsonMatch[0]);
                        resolve(result);
                    } else {
                        reject(new Error('No valid JSON result found in output'));
                    }
                } catch (error) {
                    reject(new Error('Failed to parse processing result'));
                }
            } else {
                reject(new Error(`Process exited with code ${code}: ${stderr}`));
            }
        });

        pythonProcess.on('error', (error) => {
            reject(new Error(`Failed to start Python process: ${error.message}`));
        });
    });
}

/**
 * Express.js middleware for file upload validation
 */
function validateAudioFile(req, res, next) {
    if (!req.file) {
        return res.status(400).json({
            success: false,
            error: 'No audio file uploaded'
        });
    }

    const allowedMimes = [
        'audio/mpeg',
        'audio/wav', 
        'audio/x-wav',
        'audio/flac',
        'audio/x-flac',
        'audio/mp4',
        'audio/aac'
    ];

    if (!allowedMimes.includes(req.file.mimetype)) {
        return res.status(400).json({
            success: false,
            error: 'Unsupported audio format. Supported: MP3, WAV, FLAC, M4A, AAC'
        });
    }

    if (req.file.size > SEPARATOR_CONFIG.maxFileSize) {
        return res.status(400).json({
            success: false,
            error: 'File too large. Maximum size: 500MB'
        });
    }

    next();
}

/**
 * Express.js API route handler
 */
async function handleStemSeparation(req, res) {
    try {
        const { model = 'demucs', device = 'auto' } = req.body;
        const uploadedFile = req.file;

        // Create unique output directory
        const sessionId = Date.now().toString();
        const outputDir = path.join(__dirname, '..', 'output', 'api', sessionId);

        // Ensure output directory exists
        await fs.mkdir(outputDir, { recursive: true });

        // Process audio
        const result = await separateAudioStems(uploadedFile.path, outputDir, {
            model,
            device,
            verbose: false
        });

        if (result.success) {
            // Add download URLs for each stem
            result.download_urls = result.stems.map(stemFile => ({
                stem: stemFile.replace('.wav', ''),
                filename: stemFile,
                url: `/api/download/${sessionId}/${stemFile}`
            }));

            res.json({
                success: true,
                message: 'Audio separation completed successfully',
                session_id: sessionId,
                data: result
            });
        } else {
            res.status(500).json({
                success: false,
                message: 'Audio separation failed',
                error: result.error
            });
        }

        // Clean up uploaded file
        try {
            await fs.unlink(uploadedFile.path);
        } catch (error) {
            console.warn('Failed to clean up uploaded file:', error.message);
        }

    } catch (error) {
        console.error('Error in stem separation:', error);
        res.status(500).json({
            success: false,
            message: 'Internal server error',
            error: error.message
        });
    }
}

/**
 * Complete Express.js application example
 */
function createExpressApp() {
    const express = require('express');
    const multer = require('multer');
    const cors = require('cors');

    const app = express();

    // Middleware
    app.use(cors());
    app.use(express.json());
    app.use(express.static('public'));

    // Configure multer for file uploads
    const upload = multer({
        dest: 'uploads/',
        limits: {
            fileSize: SEPARATOR_CONFIG.maxFileSize
        }
    });

    // Routes
    app.post('/api/separate-stems', 
        upload.single('audio'), 
        validateAudioFile, 
        handleStemSeparation
    );

    app.get('/api/download/:sessionId/:filename', async (req, res) => {
        try {
            const { sessionId, filename } = req.params;
            const filePath = path.join(__dirname, '..', 'output', 'api', sessionId, filename);
            
            await fs.access(filePath);
            res.download(filePath);
        } catch (error) {
            res.status(404).json({
                success: false,
                error: 'File not found'
            });
        }
    });

    app.get('/api/models', (req, res) => {
        res.json({
            success: true,
            models: {
                demucs: {
                    name: 'Demucs',
                    description: 'High-quality separation, slower processing',
                    variants: ['htdemucs', 'htdemucs_ft', 'mdx_extra']
                },
                openunmix: {
                    name: 'Open-Unmix',
                    description: 'Good quality separation, faster processing',
                    variants: ['umxhq', 'umx']
                }
            }
        });
    });

    // Health check endpoint
    app.get('/api/health', (req, res) => {
        res.json({
            success: true,
            message: 'Audio Stem Separator API is running',
            timestamp: new Date().toISOString()
        });
    });

    return app;
}

/**
 * WebSocket integration for real-time progress updates
 */
function setupWebSocketProgress(io) {
    io.on('connection', (socket) => {
        console.log('Client connected for progress updates');

        socket.on('start-separation', async (data) => {
            try {
                const { inputFile, outputDir, options = {} } = data;

                await separateAudioStemsWithProgress(
                    inputFile,
                    outputDir,
                    options,
                    (progressData) => {
                        socket.emit('progress', progressData);
                    }
                );

                socket.emit('completed', { success: true });
            } catch (error) {
                socket.emit('error', { 
                    success: false, 
                    error: error.message 
                });
            }
        });

        socket.on('disconnect', () => {
            console.log('Client disconnected');
        });
    });
}

/**
 * Batch processing function
 */
async function processBatch(files, outputBaseDir, options = {}) {
    const results = [];
    const { model = 'demucs', device = 'auto', maxConcurrent = 2 } = options;

    // Process files in batches to avoid overwhelming the system
    for (let i = 0; i < files.length; i += maxConcurrent) {
        const batch = files.slice(i, i + maxConcurrent);
        
        const batchPromises = batch.map(async (file, index) => {
            const outputDir = path.join(outputBaseDir, `file_${i + index + 1}`);
            
            try {
                const result = await separateAudioStems(file, outputDir, {
                    model,
                    device,
                    verbose: false
                });
                
                return {
                    file,
                    outputDir,
                    result,
                    index: i + index
                };
            } catch (error) {
                return {
                    file,
                    outputDir,
                    result: {
                        success: false,
                        error: error.message
                    },
                    index: i + index
                };
            }
        });

        const batchResults = await Promise.all(batchPromises);
        results.push(...batchResults);

        console.log(`Batch ${Math.floor(i / maxConcurrent) + 1} completed`);
    }

    return results;
}

// Example usage functions
async function basicExample() {
    try {
        const result = await separateAudioStems(
            './examples/sample.mp3',
            './output/basic_example'
        );

        console.log('Processing result:', result);
    } catch (error) {
        console.error('Error:', error.message);
    }
}

async function progressExample() {
    try {
        const result = await separateAudioStemsWithProgress(
            './examples/sample.mp3',
            './output/progress_example',
            { model: 'demucs' },
            (progress) => {
                console.log('Progress:', progress);
            }
        );

        console.log('Final result:', result);
    } catch (error) {
        console.error('Error:', error.message);
    }
}

// Export functions for use in other modules
module.exports = {
    separateAudioStems,
    separateAudioStemsWithProgress,
    validateAudioFile,
    handleStemSeparation,
    createExpressApp,
    setupWebSocketProgress,
    processBatch,
    SEPARATOR_CONFIG
};

// Example server startup
if (require.main === module) {
    const app = createExpressApp();
    const port = process.env.PORT || 3000;

    app.listen(port, () => {
        console.log(`🚀 Audio Stem Separator API running on port ${port}`);
        console.log(`📖 Documentation: http://localhost:${port}/api/health`);
    });
}
