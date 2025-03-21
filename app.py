from flask import Flask, render_template, request, send_file, jsonify
import os
from pathlib import Path
import pandas as pd
import sys
from werkzeug.utils import secure_filename
import shutil
from datetime import datetime
import numpy as np
import tempfile

# Import functions from subprojects
sys.path.append(str(Path(__file__).parent / 'subproject1'))
sys.path.append(str(Path(__file__).parent / 'subproject2'))

from subproject2.word_frequency import WordFrequencyAnalyzer
import subproject1.scaling_features as scaling

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = tempfile.gettempdir()  # Use system temp directory
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Add security headers
@app.after_request
def add_security_headers(response):
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval' cdn.plot.ly unpkg.com cdnjs.cloudflare.com; style-src 'self' 'unsafe-inline' cdn.jsdelivr.net cdnjs.cloudflare.com; img-src 'self' data:; font-src cdnjs.cloudflare.com;"
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    return response

# Add CSP headers to allow Plotly
@app.after_request
def add_plotly_headers(response):
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval' cdn.plot.ly; style-src 'self' 'unsafe-inline';"
    return response

# Ensure upload and output directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs('output', exist_ok=True)

def get_color_palette(n):
    """Generate a color palette with n distinct colors"""
    colors = [
        '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
        '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'
    ]
    return (colors * (n // len(colors) + 1))[:n]

def prepare_plot_data(df, group_col, use_post_scaling=False, use_normalized=False, is_group_data=True):
    """Prepare data for scatter plot"""
    try:
        if is_group_data:
            # For group plot, use the group averages
            groups = df['group'].unique()
            colors = get_color_palette(len(groups))
            traces = []
            
            for group, color in zip(groups, colors):
                group_data = df[df['group'] == group]
                if use_normalized:
                    valence = group_data[f'valence_scaled_by_{group_col}_normalized'].iloc[0]
                    arousal = group_data[f'arousal_scaled_by_{group_col}_normalized'].iloc[0]
                else:
                    valence = group_data[f'valence_scaled_by_{group_col}_original'].iloc[0]
                    arousal = group_data[f'arousal_scaled_by_{group_col}_original'].iloc[0]
                
                group_name = f"Group {group}"
                traces.append({
                    'x': [valence],
                    'y': [arousal],
                    'name': group_name,
                    'text': [group_name],
                    'hovertext': [f"Valence: {valence:.3f}<br>Arousal: {arousal:.3f}"],
                    'color': color
                })
            return traces
        else:
            # For post plot, show all points
            groups = df[group_col].unique()
            colors = get_color_palette(len(groups))
            traces = []
            
            valence_col = f'valence_scaled_by_{group_col}_normalized' if use_normalized else f'valence_scaled_by_{group_col}'
            arousal_col = f'arousal_scaled_by_{group_col}_normalized' if use_normalized else f'arousal_scaled_by_{group_col}'
            
            for group, color in zip(groups, colors):
                group_data = df[df[group_col] == group]
                trace_name = f"Post {group}"
                traces.append({
                    'x': group_data[valence_col].tolist(),
                    'y': group_data[arousal_col].tolist(),
                    'name': trace_name,
                    'text': [trace_name] * len(group_data),
                    'hovertext': [f"Valence: {v:.3f}<br>Arousal: {a:.3f}" 
                               for v, a in zip(group_data[valence_col], group_data[arousal_col])],
                    'color': color
                })
            return traces
    except Exception as e:
        print(f"Error in prepare_plot_data: {str(e)}")
        raise e

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        project_type = request.form.get('project_type')
        
        if project_type == 'word_counter':
            if 'text' not in request.form:
                return jsonify({'error': 'No text provided'}), 400
                
            text = request.form['text']
            if not text.strip():
                return jsonify({'error': 'Empty text provided'}), 400
            
            # Create timestamp for unique file names
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            text_file = os.path.join(app.config['UPLOAD_FOLDER'], f'text_{timestamp}.txt')
            
            try:
                # Save text to file
                with open(text_file, 'w', encoding='utf-8') as f:
                    f.write(text)
                
                # Analyze text
                analyzer = WordFrequencyAnalyzer()
                analyzer.analyze_text(text)
                
                # Ensure output directory exists
                os.makedirs('output', exist_ok=True)
                
                # Save results
                analyzer.save_results()
                
                # Read results
                results_file = 'output/word_frequencies.csv'
                if os.path.exists(results_file):
                    df = pd.read_csv(results_file)
                    if len(df) == 0:
                        return jsonify({'error': 'No words found in text'}), 400
                        
                    total_words = int(df['frequency'].sum())  # Convert to int
                    unique_words = len(df)
                    
                    # Convert frequencies to int for JSON serialization
                    frequencies = df.to_dict('records')
                    for item in frequencies:
                        item['frequency'] = int(item['frequency'])
                        item['percentage'] = float(item['percentage'])  # Convert to float
                    
                    return jsonify({
                        'success': True,
                        'frequencies': frequencies,
                        'total_words': total_words,
                        'unique_words': unique_words,
                        'plot_url': '/output/word_frequencies_plot.png',
                        'summary': f"Analysis complete! Found {unique_words} unique words out of {total_words} total words. The most frequent word was '{df.iloc[0]['word']}' appearing {int(df.iloc[0]['frequency'])} times ({float(df.iloc[0]['percentage']):.1f}% of total)."
                    })
                else:
                    return jsonify({'error': 'Analysis failed - no results file generated'}), 500
            except Exception as e:
                print(f"Error in word counter analysis: {str(e)}")
                return jsonify({'error': f'Analysis failed: {str(e)}'}), 500
            finally:
                # Clean up temporary file
                if os.path.exists(text_file):
                    os.remove(text_file)
                    
        elif project_type == 'scaling':
            if 'file' not in request.files:
                return jsonify({'error': 'No file uploaded'}), 400
                
            file = request.files['file']
            if file.filename == '':
                return jsonify({'error': 'No file selected'}), 400
                
            if not allowed_file(file.filename, {'csv', 'xlsx', 'xls'}):
                return jsonify({'error': 'Invalid file type'}), 400
                
            # Create timestamp for unique file names
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = secure_filename(f"{timestamp}_{file.filename}")
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            
            # Save uploaded file
            file.save(filepath)
            
            try:
                # Process the file and get all DataFrames
                dfs = scaling.process_file(filepath)
                
                # Debug prints
                print("\nAvailable DataFrames:")
                for name, df_info in dfs.items():
                    print(f"{name}: {df_info['data'].columns.tolist()}")
                
                # Prepare previews and file information
                df_files = {}
                friendly_names = {
                    'df_original': 'Original Data',
                    'df_scaled_by_group': 'Data Scaled by Group',
                    'df_scaled_by_post': 'Data Scaled by Post',
                    'group_averages': 'Group Averages',
                    'post_averages': 'Post Averages'
                }
                
                for df_name, df_info in dfs.items():
                    df = df_info['data']
                    output_filename = df_info['filename']
                    
                    # Get all columns for preview
                    preview_data = df.head().to_dict('records')
                    
                    # Add row numbers to preview
                    for i, row in enumerate(preview_data):
                        row['#'] = i + 1
                    
                    df_files[friendly_names[df_name]] = {
                        'url': f'/output/{output_filename}',
                        'preview': preview_data,
                        'shape': df.shape,
                        'columns': df.columns.tolist(),
                        'filename': output_filename
                    }
                
                # Prepare plot data for all 4 plots
                print("\nPreparing plot data...")
                group_plot_data = prepare_plot_data(dfs['group_averages']['data'], 'group', use_normalized=False, is_group_data=True)
                group_plot_normalized_data = prepare_plot_data(dfs['group_averages']['data'], 'group', use_normalized=True, is_group_data=True)
                post_plot_data = prepare_plot_data(dfs['df_scaled_by_post']['data'], 'post', use_normalized=False, is_group_data=False)
                post_plot_normalized_data = prepare_plot_data(dfs['df_scaled_by_post']['data'], 'post', use_normalized=True, is_group_data=False)
                
                # Create summary
                summary = (
                    f"Data scaling complete! Processed {dfs['df_original']['data'].shape[0]} rows and "
                    f"{dfs['df_original']['data'].shape[1]} columns. Created {len(dfs)} different scaled "
                    f"and normalized versions of your data. All files are saved in Excel format (.xlsx) "
                    f"for easy viewing and editing."
                )
                
                return jsonify({
                    'success': True,
                    'dataframes': df_files,
                    'group_plot': group_plot_data,
                    'group_plot_normalized': group_plot_normalized_data,
                    'post_plot': post_plot_data,
                    'post_plot_normalized': post_plot_normalized_data,
                    'summary': summary
                })
            except Exception as e:
                print(f"Error processing file: {str(e)}")
                return jsonify({'error': str(e)}), 500
            finally:
                # Clean up uploaded file
                if os.path.exists(filepath):
                    os.remove(filepath)
        else:
            return jsonify({'error': 'Invalid project type'}), 400
    except Exception as e:
        print(f"Error in analyze route: {str(e)}")
        return jsonify({'error': str(e)}), 500

def allowed_file(filename, allowed_extensions):
    """Check if file has an allowed extension"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

@app.route('/output/<path:filename>')
def download_file(filename):
    """Download a file from the output directory"""
    return send_file(os.path.join('output', filename), as_attachment=True)

@app.errorhandler(404)
def not_found_error(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

@app.errorhandler(413)
def too_large(error):
    return jsonify({'error': 'File too large. Maximum size is 16MB'}), 413

if __name__ == '__main__':
    # Development
    app.run(debug=True)
else:
    # Production
    app.run(debug=False)
