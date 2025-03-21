# Data Analysis Tool

A powerful data analysis tool for scaling and normalizing data, as well as performing word frequency analysis on text.

## Features

### Data Scaling and Normalization
- Scales data within groups using MinMaxScaler
- Calculates normalized averages
- Visualizes data with interactive plots
- Supports CSV and Excel files

### Word Frequency Analysis
- Analyzes text to find word frequencies
- Combines similar words
- Normalizes word variations
- Creates visualizations of word frequencies

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/data-analysis-tool.git
cd data-analysis-tool

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Running Locally

```bash
python app.py
```

This will start a Flask server at http://localhost:5000.

### Data Scaling

1. Upload a CSV or Excel file with the required columns:
   - group
   - post
   - valence
   - arousal

2. View the scaled and normalized data in the browser.

3. Download the results as Excel files.

### Word Frequency Analysis

1. Enter text to analyze in the text area.

2. Click "Analyze" to see the most frequent words and their distribution.

3. Download the results as CSV or view the chart.

## Deployment

This application is ready for deployment on Render.com:

1. Push your code to GitHub.

2. Create a new Web Service on Render.com.

3. Select your GitHub repository.

4. Configure the following:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app`

5. Add any necessary environment variables:
   - `OUTPUT_FOLDER` - Path to store output files
   - `TEMP_FOLDER` - Path for temporary uploads

## Technical Details

The application consists of two main subprojects:

1. `subproject1` - Scaling and normalization logic
2. `subproject2` - Word frequency analysis

### Dependencies

- Flask - Web framework
- Pandas - Data manipulation
- NumPy - Numerical operations
- scikit-learn - Scaling algorithms
- Matplotlib - Plotting
- Plotly - Interactive visualizations
- gunicorn - WSGI server for production

## License

This project is licensed under the MIT License - see the LICENSE file for details.
