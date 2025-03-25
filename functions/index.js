const functions = require('firebase-functions');
const admin = require('firebase-admin');
const express = require('express');
const cors = require('cors');
const XLSX = require('xlsx');
const fs = require('fs');
const path = require('path');
const os = require('os');
const https = require('https');

admin.initializeApp();

// Create Express app for HTTP functions with proper CORS handling
const app = express();

// Configure CORS with specific options
const corsOptions = {
  origin: '*', // Allow all origins for testing
  methods: ['GET', 'POST', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization', 'Accept'],
  credentials: true,
  preflightContinue: false,
  optionsSuccessStatus: 204
};

// Apply CORS middleware with options
app.use(cors(corsOptions));

// Add explicit OPTIONS handler for preflight requests
app.options('*', cors(corsOptions));

// Add JSON parsing middleware
app.use(express.json());

// Temporary directories
const createTempDirs = () => {
  const tempDir = os.tmpdir();
  const uploadDir = path.join(tempDir, 'uploads');
  const outputDir = path.join(tempDir, 'output');
  
  if (!fs.existsSync(uploadDir)) {
    fs.mkdirSync(uploadDir, { recursive: true });
  }
  
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }
  
  return { uploadDir, outputDir };
};

// Download file from URL
const downloadFile = (url, destination) => {
  return new Promise((resolve, reject) => {
    const file = fs.createWriteStream(destination);
    https.get(url, (response) => {
      response.pipe(file);
      file.on('finish', () => {
        file.close(resolve);
      });
    }).on('error', (err) => {
      fs.unlink(destination, () => {});
      reject(err);
    });
  });
};

// Simulated scaling processing function
async function processScalingFile(filePath, outputDir) {
  // This is a placeholder for the actual Python logic
  // In a real implementation, you would rewrite the Python logic in JavaScript
  
  // Read the Excel file
  const workbook = XLSX.readFile(filePath);
  const sheetName = workbook.SheetNames[0];
  const worksheet = workbook.Sheets[sheetName];
  const data = XLSX.utils.sheet_to_json(worksheet);
  
  // Process data (simplified version of your Python logic)
  const processedData = data.map(row => ({
    ...row,
    normalized_valence: (row.valence - 1) / 4,
    normalized_arousal: (row.arousal - 1) / 4
  }));
  
  // Create output workbook
  const outputWorkbook = XLSX.utils.book_new();
  const outputWorksheet = XLSX.utils.json_to_sheet(processedData);
  XLSX.utils.book_append_sheet(outputWorkbook, outputWorksheet, 'Processed Data');
  
  // Save to output directory
  const outputPath = path.join(outputDir, 'processed_data.xlsx');
  XLSX.writeFile(outputWorkbook, outputPath);
  
  // Upload results to Firebase Storage
  const bucket = admin.storage().bucket();
  const fileUrls = {};
  
  for (const file of fs.readdirSync(outputDir)) {
    const filePath = path.join(outputDir, file);
    await bucket.upload(filePath, {
      destination: `output/${file}`,
      metadata: {
        contentType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
      }
    });
    
    // Get download URL
    const [url] = await bucket.file(`output/${file}`).getSignedUrl({
      action: 'read',
      expires: '03-01-2500' // Far future expiration
    });
    
    fileUrls[file] = url;
  }
  
  return { rowCount: processedData.length, dataframes: fileUrls };
}

// Simulated word frequency processing function
async function processWordFrequency(text) {
  // This is a placeholder for the actual Python logic
  // In a real implementation, you would rewrite the Python logic in JavaScript
  
  // Simple word frequency calculation
  const words = text.toLowerCase().match(/\b(\w+)\b/g) || [];
  const frequency = {};
  
  words.forEach(word => {
    frequency[word] = (frequency[word] || 0) + 1;
  });
  
  // Sort by frequency
  const sortedWords = Object.entries(frequency)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 20)
    .map(([word, count]) => ({ word, count }));
  
  return sortedWords;
}

// Keep the original callable function
exports.api = functions.https.onCall(async (data, context) => {
  try {
    // Handle different endpoints
    const { endpoint, fileUrl, fileName, text } = data;
    
    if (endpoint === '/scaling' && fileUrl && fileName) {
      // Process scaling request
      const { uploadDir, outputDir } = createTempDirs();
      const filePath = path.join(uploadDir, fileName);
      
      // Download the file from the URL
      await downloadFile(fileUrl, filePath);
      
      // Process the file
      const results = await processScalingFile(filePath, outputDir);
      
      return {
        success: true,
        summary: `File processed successfully. ${results.rowCount} rows processed.`,
        dataframes: results.dataframes
      };
    } 
    else if (endpoint === '/word-frequency' && text) {
      // Process word frequency request
      const results = processWordFrequency(text);
      
      return {
        success: true,
        results: results
      };
    } 
    else {
      return {
        success: false,
        error: 'Invalid request parameters'
      };
    }
  } catch (error) {
    console.error('Error processing request:', error);
    return {
      success: false,
      error: error.message || 'An error occurred while processing your request'
    };
  }
});

// Create HTTP endpoints for scaling with explicit CORS handling
app.post('/scaling', async (req, res) => {
  // Set CORS headers manually for additional safety
  res.set('Access-Control-Allow-Origin', '*');
  res.set('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.set('Access-Control-Allow-Headers', 'Content-Type, Authorization, Accept');
  
  try {
    const { fileUrl, fileName } = req.body;
    
    if (!fileUrl || !fileName) {
      return res.status(400).json({
        success: false,
        error: 'Missing required parameters'
      });
    }
    
    // Process scaling request
    const { uploadDir, outputDir } = createTempDirs();
    const filePath = path.join(uploadDir, fileName);
    
    // Download the file from the URL
    await downloadFile(fileUrl, filePath);
    
    // Process the file
    const results = await processScalingFile(filePath, outputDir);
    
    return res.json({
      success: true,
      summary: `File processed successfully. ${results.rowCount} rows processed.`,
      dataframes: results.dataframes
    });
  } catch (error) {
    console.error('Error processing scaling request:', error);
    return res.status(500).json({
      success: false,
      error: error.message || 'An error occurred while processing your request'
    });
  }
});

// Create HTTP endpoints for word frequency with explicit CORS handling
app.post('/word-frequency', async (req, res) => {
  // Set CORS headers manually for additional safety
  res.set('Access-Control-Allow-Origin', '*');
  res.set('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.set('Access-Control-Allow-Headers', 'Content-Type, Authorization, Accept');
  
  try {
    const { text } = req.body;
    
    if (!text) {
      return res.status(400).json({
        success: false,
        error: 'Missing required parameters'
      });
    }
    
    // Process word frequency request
    const results = processWordFrequency(text);
    
    return res.json({
      success: true,
      results: results
    });
  } catch (error) {
    console.error('Error processing word frequency request:', error);
    return res.status(500).json({
      success: false,
      error: error.message || 'An error occurred while processing your request'
    });
  }
});

// Export a new HTTP function with a different name and explicit CORS handling
exports.httpApi = functions.https.onRequest((req, res) => {
  // Set CORS headers for preflight requests
  if (req.method === 'OPTIONS') {
    res.set('Access-Control-Allow-Origin', '*');
    res.set('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
    res.set('Access-Control-Allow-Headers', 'Content-Type, Authorization, Accept');
    res.set('Access-Control-Max-Age', '3600');
    res.status(204).send('');
    return;
  }
  
  // Pass the request to the Express app
  return app(req, res);
});
