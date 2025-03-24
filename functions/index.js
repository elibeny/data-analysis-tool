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
const app = express();

// Middleware
app.use(cors({ origin: true }));
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

// Handle API routing
app.post('/', async (req, res) => {
  try {
    const { endpoint, fileUrl, fileName, text } = req.body.data || {};
    
    if (endpoint === '/scaling' && fileUrl && fileName) {
      // Handle scaling request
      const { uploadDir, outputDir } = createTempDirs();
      const filePath = path.join(uploadDir, fileName);
      
      // Download the file from the provided URL
      await downloadFile(fileUrl, filePath);
      
      // Process the file
      const results = await processScalingFile(filePath, outputDir);
      
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
      
      return res.json({
        success: true,
        summary: 'Data processed successfully',
        dataframes: fileUrls
      });
    } 
    else if (endpoint === '/word-frequency' && text) {
      // Handle word frequency request
      const results = await processWordFrequency(text);
      
      return res.json({
        success: true,
        results
      });
    } 
    else {
      return res.status(400).json({ 
        success: false, 
        error: 'Invalid request parameters' 
      });
    }
  } catch (error) {
    console.error('Error processing request:', error);
    return res.status(500).json({ 
      success: false, 
      error: error.message 
    });
  }
});

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
  
  return { outputPath };
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

// Export the Express app as a Cloud Function
exports.api = functions.https.onRequest(app);
