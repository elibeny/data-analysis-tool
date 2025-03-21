# Import Libraries
import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler, StandardScaler
import os
import sys
from pathlib import Path

def load_data(filename):
    """
    Load data from Excel or CSV file.
    Supports .xlsx, .xls, and .csv files.
    """
    file_extension = Path(filename).suffix.lower()
    try:
        if file_extension in ['.xlsx', '.xls']:
            df = pd.read_excel(filename)
        elif file_extension == '.csv':
            df = pd.read_csv(filename)
        else:
            raise ValueError(f"Unsupported file format: {file_extension}. Please use Excel (.xlsx, .xls) or CSV (.csv) files.")
        
        # Ensure required columns exist
        required_columns = ['group', 'post', 'valence', 'arousal']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"Missing required columns: {', '.join(missing_columns)}")
        
        # Round numeric columns to 3 decimal places
        numeric_columns = df.select_dtypes(include=[np.number]).columns
        df[numeric_columns] = df[numeric_columns].round(3)
        return df
    
    except Exception as e:
        print(f"Error loading file: {str(e)}")
        sys.exit(1)

def calculate_normalized_averages(df, group_col):
    """
    Calculate two types of averages:
    1. Regular averages (scaled between -1 and 1)
    2. Relative averages (divided by mean of scaled values)
    """
    # Calculate averages per group for scaled values
    group_avgs = df.groupby(group_col).agg({
        f'valence_scaled_by_{group_col}': 'mean',
        f'arousal_scaled_by_{group_col}': 'mean'
    }).round(3)
    
    # Keep original scaled averages
    group_avgs[f'valence_scaled_by_{group_col}_original'] = group_avgs[f'valence_scaled_by_{group_col}']
    group_avgs[f'arousal_scaled_by_{group_col}_original'] = group_avgs[f'arousal_scaled_by_{group_col}']
    
    # Calculate relative averages (divided by mean of scaled values)
    total_avg_valence = df[f'valence_scaled_by_{group_col}'].mean()
    total_avg_arousal = df[f'arousal_scaled_by_{group_col}'].mean()
    
    # Divide by mean to get relative values
    group_avgs[f'valence_scaled_by_{group_col}_normalized'] = (group_avgs[f'valence_scaled_by_{group_col}'] / total_avg_valence).round(3)
    group_avgs[f'arousal_scaled_by_{group_col}_normalized'] = (group_avgs[f'arousal_scaled_by_{group_col}'] / total_avg_arousal).round(3)
    
    # Also add normalized columns to original dataframe
    df[f'valence_scaled_by_{group_col}_normalized'] = (df[f'valence_scaled_by_{group_col}'] / total_avg_valence).round(3)
    df[f'arousal_scaled_by_{group_col}_normalized'] = (df[f'arousal_scaled_by_{group_col}'] / total_avg_arousal).round(3)
    
    return group_avgs, df

def sklearn_group_scaling(df, cols, group_col, scaler):
    """
    Scale data within groups using the specified scaler.
    """
    df_scaled = df.copy()
    
    for col in cols:
        scaled_values = []
        for group in df[group_col].unique():
            mask = df[group_col] == group
            data_to_scale = df.loc[mask, col].values.reshape(-1, 1)
            scaled = scaler.fit_transform(data_to_scale).flatten()
            scaled_values.extend(scaled)
        
        # Use the correct column name format
        df_scaled[f'{col}_scaled_by_{group_col}'] = np.round(scaled_values, 3)

    # Copy over any existing scaled columns
    for col in df.columns:
        if 'scaled_by' in col and col not in df_scaled.columns:
            df_scaled[col] = df[col]

    numeric_columns = df_scaled.select_dtypes(include=[np.number]).columns
    df_scaled[numeric_columns] = df_scaled[numeric_columns].round(3)
    
    return df_scaled

def process_file(input_file):
    """
    Main function to process input file and generate normalized averages.
    Returns a dictionary of all DataFrames created during processing.
    """
    try:
        # Create output directory if it doesn't exist
        output_dir = Path('output')
        output_dir.mkdir(exist_ok=True)
        
        # Load and validate data
        print(f"\nLoading data from {input_file}...")
        df_original = load_data(input_file)
        print("Data loaded successfully!")
        
        # Scale data by group
        print("\nScaling data by group...")
        df_scaled_by_group = sklearn_group_scaling(df_original, ['valence', 'arousal'], 'group', MinMaxScaler(feature_range=(-1,1)))
        
        # Scale data by post
        print("Scaling data by post...")
        df_scaled_by_post = sklearn_group_scaling(df_scaled_by_group, ['valence', 'arousal'], 'post', MinMaxScaler(feature_range=(-1,1)))
        
        # Calculate normalized averages
        print("\nCalculating normalized averages...")
        group_averages, df_scaled_by_group_normalized = calculate_normalized_averages(df_scaled_by_group, 'group')
        post_averages, df_scaled_by_post_normalized = calculate_normalized_averages(df_scaled_by_post, 'post')
        
        # Reset index for averages to make group/post column visible
        group_averages = group_averages.reset_index()
        post_averages = post_averages.reset_index()
        
        # Save all DataFrames as Excel files
        with pd.ExcelWriter(output_dir / 'original_data.xlsx', engine='openpyxl') as writer:
            df_original.to_excel(writer, index=False, sheet_name='Original Data')
            
        with pd.ExcelWriter(output_dir / 'scaled_by_group.xlsx', engine='openpyxl') as writer:
            df_scaled_by_group_normalized.to_excel(writer, index=False, sheet_name='Scaled by Group')
            
        with pd.ExcelWriter(output_dir / 'scaled_by_post.xlsx', engine='openpyxl') as writer:
            df_scaled_by_post_normalized.to_excel(writer, index=False, sheet_name='Scaled by Post')
            
        with pd.ExcelWriter(output_dir / 'group_averages.xlsx', engine='openpyxl') as writer:
            group_averages.to_excel(writer, index=False, sheet_name='Group Averages')
            
        with pd.ExcelWriter(output_dir / 'post_averages.xlsx', engine='openpyxl') as writer:
            post_averages.to_excel(writer, index=False, sheet_name='Post Averages')
        
        print("\nResults saved successfully!")
        
        # Return all DataFrames in a dictionary
        return {
            'df_original': {'data': df_original, 'filename': 'original_data.xlsx'},
            'df_scaled_by_group': {'data': df_scaled_by_group_normalized, 'filename': 'scaled_by_group.xlsx'},
            'df_scaled_by_post': {'data': df_scaled_by_post_normalized, 'filename': 'scaled_by_post.xlsx'},
            'group_averages': {'data': group_averages, 'filename': 'group_averages.xlsx'},
            'post_averages': {'data': post_averages, 'filename': 'post_averages.xlsx'}
        }
        
    except Exception as e:
        print(f"\nError processing file: {str(e)}")
        raise e

def print_usage():
    """Print usage instructions."""
    print("\nUsage:")
    print("python scaling_features.py <input_file>")
    print("\nSupported file formats:")
    print("- Excel files (.xlsx, .xls)")
    print("- CSV files (.csv)")
    print("\nRequired columns in the input file:")
    print("- group")
    print("- post")
    print("- valence")
    print("- arousal")
    print("\nOutput files will be created in the 'output' directory.")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("\nError: Please provide the input file path.")
        print_usage()
        sys.exit(1)
    
    input_file = sys.argv[1]
    result = process_file(input_file)
    if result:
        print("\nProcessing completed successfully!")
    else:
        sys.exit(1)