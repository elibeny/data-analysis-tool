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
    Calculate three types of values:
    1. Original values (before scaling)
    2. Scaled values (-1 to 1)
    3. Normalized values (scaled/mean)
    """
    # Calculate averages of original values per group
    original_cols = [col for col in df.columns if '_group_mean' in col]
    if original_cols:
        original_avgs = df[original_cols].groupby(df[group_col]).mean()
        original_avgs = original_avgs.rename(columns={
            'valence_group_mean': 'valence_original_mean',
            'arousal_group_mean': 'arousal_original_mean'
        })
    else:
        original_avgs = pd.DataFrame()
    
    # Calculate averages of scaled values per group
    scaled_cols = [f'valence_scaled_by_{group_col}', f'arousal_scaled_by_{group_col}']
    scaled_avgs = df[scaled_cols].groupby(df[group_col]).mean().round(3)
    scaled_avgs = scaled_avgs.rename(columns={
        f'valence_scaled_by_{group_col}': f'valence_scaled_by_{group_col}_original',
        f'arousal_scaled_by_{group_col}': f'arousal_scaled_by_{group_col}_original'
    })
    
    # Calculate means of GROUP AVERAGES (not all individual data points)
    # This is the key change - we calculate the mean of the group averages
    valence_mean = scaled_avgs[f'valence_scaled_by_{group_col}_original'].mean().round(3)
    arousal_mean = scaled_avgs[f'arousal_scaled_by_{group_col}_original'].mean().round(3)
    
    print("\n=== DEBUG INFO ===")
    print("Scaled averages per group:")
    print(scaled_avgs)
    print("\nMean of GROUP AVERAGES:")
    print(f"Valence mean: {valence_mean}")
    print(f"Arousal mean: {arousal_mean}")
    
    # Create normalized_avgs DataFrame with proper columns
    normalized_avgs = pd.DataFrame(
        index=scaled_avgs.index,
        columns=[
            f'valence_scaled_by_{group_col}_normalized',
            f'arousal_scaled_by_{group_col}_normalized'
        ]
    )
    
    # Calculate and print each normalization step
    for group in scaled_avgs.index:
        valence_original = scaled_avgs.loc[group, f'valence_scaled_by_{group_col}_original']
        
        # Use the mean of group averages, not the mean of all data points
        valence_normalized = (valence_original / valence_mean).round(3)
        
        print(f"\nGroup {group}:")
        print(f"  Valence original: {valence_original}")
        print(f"  Valence mean of GROUP AVERAGES: {valence_mean}")
        print(f"  Calculation: {valence_original} / {valence_mean} = {valence_normalized}")
        
        # Store the normalized value
        normalized_avgs.loc[group, f'valence_scaled_by_{group_col}_normalized'] = valence_normalized
    
    # Add arousal normalized values
    for group in scaled_avgs.index:
        arousal_original = scaled_avgs.loc[group, f'arousal_scaled_by_{group_col}_original']
        
        # Use the mean of group averages, not the mean of all data points
        arousal_normalized = (arousal_original / arousal_mean).round(3)
        normalized_avgs.loc[group, f'arousal_scaled_by_{group_col}_normalized'] = arousal_normalized
    
    # Combine all averages
    group_avgs = pd.concat([original_avgs, scaled_avgs, normalized_avgs], axis=1)
    
    # Print final results for verification
    print("\nFinal normalized values:")
    print(normalized_avgs)
    
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

    numeric_columns = df_scaled.select_dtypes(include=[np.number]).columns
    df_scaled[numeric_columns] = df_scaled[numeric_columns].round(3)
    
    return df_scaled

def process_file(input_file, output_dir='output'):
    """
    Main function to process input file and generate normalized averages.
    Returns a dictionary of all DataFrames created during processing.
    """
    try:
        # Create output directory if it doesn't exist
        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True)
        
        # Load and validate data
        print(f"\nLoading data from {input_file}...")
        df_original = load_data(input_file)
        print("Data loaded successfully!")
        
        # Scale data by group
        print("\nScaling data by group...")
        df_scaled_by_group = sklearn_group_scaling(df_original, ['valence', 'arousal'], 'group', MinMaxScaler(feature_range=(-1,1)))
        
        # Scale data by post (only keep post scaling, remove group scaling)
        print("Scaling data by post...")
        df_scaled_by_post = sklearn_group_scaling(df_original, ['valence', 'arousal'], 'post', MinMaxScaler(feature_range=(-1,1)))
        
        # Calculate normalized averages
        print("\nCalculating normalized averages...")
        group_averages, _ = calculate_normalized_averages(df_scaled_by_group, 'group')
        post_averages, _ = calculate_normalized_averages(df_scaled_by_post, 'post')
        
        # Reset index for averages to make group/post column visible
        group_averages = group_averages.reset_index()
        post_averages = post_averages.reset_index()
        
        # Save all DataFrames as Excel files
        with pd.ExcelWriter(output_dir / 'original_data.xlsx', engine='openpyxl') as writer:
            df_original.to_excel(writer, index=False, sheet_name='Original Data')
            
        with pd.ExcelWriter(output_dir / 'scaled_by_group.xlsx', engine='openpyxl') as writer:
            df_scaled_by_group.to_excel(writer, index=False, sheet_name='Scaled by Group')
            
        with pd.ExcelWriter(output_dir / 'scaled_by_post.xlsx', engine='openpyxl') as writer:
            df_scaled_by_post.to_excel(writer, index=False, sheet_name='Scaled by Post')
            
        with pd.ExcelWriter(output_dir / 'group_averages.xlsx', engine='openpyxl') as writer:
            group_averages.to_excel(writer, index=False, sheet_name='Group Averages')
            
        with pd.ExcelWriter(output_dir / 'post_averages.xlsx', engine='openpyxl') as writer:
            post_averages.to_excel(writer, index=False, sheet_name='Post Averages')
        
        print("\nResults saved successfully!")
        
        # Return all DataFrames in a dictionary
        return {
            'df_original': {'data': df_original, 'filename': 'original_data.xlsx'},
            'df_scaled_by_group': {'data': df_scaled_by_group, 'filename': 'scaled_by_group.xlsx'},
            'df_scaled_by_post': {'data': df_scaled_by_post, 'filename': 'scaled_by_post.xlsx'},
            'group_averages': {'data': group_averages, 'filename': 'group_averages.xlsx'},
            'post_averages': {'data': post_averages, 'filename': 'post_averages.xlsx'}
        }
        
    except Exception as e:
        print(f"\nError processing file: {str(e)}")
        raise e

def print_usage():
    """Print usage instructions."""
    print("\nUsage:")
    print("python scaling_features.py <input_file> [output_dir]")
    print("\nSupported file formats:")
    print("- Excel files (.xlsx, .xls)")
    print("- CSV files (.csv)")
    print("\nRequired columns in the input file:")
    print("- group")
    print("- post")
    print("- valence")
    print("- arousal")
    print("\nOutput files will be created in the specified output directory.")

if __name__ == "__main__":
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print("\nError: Please provide the input file path and optionally the output directory.")
        print_usage()
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) == 3 else 'output'
    result = process_file(input_file, output_dir)
    if result:
        print("\nProcessing completed successfully!")
    else:
        sys.exit(1)