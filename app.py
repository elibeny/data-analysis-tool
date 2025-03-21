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
app.config['UPLOAD_FOLDER'] = os.environ.get('TEMP_FOLDER', tempfile.gettempdir())  # Use system temp directory or environment variable
app.config['OUTPUT_FOLDER'] = os.environ.get('OUTPUT_FOLDER', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output'))
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
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

# Set permissions for output directory (ignored on Windows)
try:
    if sys.platform != 'win32':
        import stat
        os.chmod(app.config['OUTPUT_FOLDER'], 
                 stat.S_IRWXU | stat.S_IRWXG | stat.S_IROTH | stat.S_IXOTH)  # 0775
except Exception as e:
    print(f"Warning: Could not set permissions on output directory: {str(e)}")

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
            
            try:
                # Analyze text
                analyzer = WordFrequencyAnalyzer()
                analyzer.output_dir = app.config['OUTPUT_FOLDER']
                analyzer.analyze_text(text)
                analyzer.save_results()
                
                # Get results safely
                try:
                    frequencies = analyzer.get_top_words(10)
                except:
                    frequencies = []
                    
                try:
                    total_words = analyzer.get_total_words()
                except:
                    total_words = 0
                    
                try:
                    unique_words = analyzer.get_unique_words()
                except:
                    unique_words = 0
                
                # Prepare summary
                if total_words > 0:
                    summary = f"Analysis complete! Found {unique_words} unique words out of {total_words} total words."
                else:
                    summary = "No words found in the provided text. Please check your input."
                
                return jsonify({
                    'success': True,
                    'frequencies': frequencies,
                    'summary': summary,
                    'plot_url': '/output/word_frequencies_plot.png'
                })
            except Exception as e:
                print(f"Error in word counter: {str(e)}")
                return jsonify({
                    'error': f"Error processing text: {str(e)}"
                }), 500
            
        elif project_type == 'scaling':
            if 'file' not in request.files:
                return jsonify({'error': 'No file uploaded'}), 400
                
            file = request.files['file']
            if file.filename == '':
                return jsonify({'error': 'No file selected'}), 400
                
            # Save uploaded file
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            try:
                # Process the file
                dfs = scaling.process_file(filepath, app.config['OUTPUT_FOLDER'])
                
                # Debug: Print group averages and calculations
                group_avgs = dfs['group_averages']['data']
                print("\nDEBUG - Group Averages:")
                print(group_avgs)
                
                # Calculate manually for verification
                if 'valence_scaled_by_group_original' in group_avgs.columns:
                    print("\nDEBUG - Manual Calculation:")
                    for idx, row in group_avgs.iterrows():
                        group = row['group']
                        val = row['valence_scaled_by_group_original']
                        if 'valence_scaled_by_group_normalized' in group_avgs.columns:
                            norm = row['valence_scaled_by_group_normalized']
                            print(f"Group {group}: {val} / ? = {norm}")
                
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
                    'summary': summary
                })
                
            except Exception as e:
                return jsonify({'error': str(e)}), 500
            finally:
                # Clean up uploaded file
                if os.path.exists(filepath):
                    os.remove(filepath)
                
        else:
            return jsonify({'error': 'Invalid project type'}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def allowed_file(filename, allowed_extensions):
    """Check if file has an allowed extension"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

@app.route('/output/<path:filename>')
def download_file(filename):
    """Download a file from the output directory"""
    return send_file(os.path.join(app.config['OUTPUT_FOLDER'], filename), as_attachment=True)

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
    # Production - debug should be false and host should listen on all interfaces
    # These settings will be overridden by gunicorn in production
    app.run(debug=False, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
