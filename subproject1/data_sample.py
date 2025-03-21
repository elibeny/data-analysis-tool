import pandas as pd
import numpy as np

# Create sample data
data = {
    'group': [1, 1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3],
    'post': ['1MS', '1MF', '1MC', '1MCa', '1MD', '2ILa', '2ILb', '2ILc', '2ILD', '3Oa', '3Ob', '30Oc', '3OD'],
    'valence': [-0.042, -0.036, -0.043, -0.034, -0.07, -0.026, -0.052, -0.035, -0.046, -0.041, -0.029, -0.032, -0.056],
    'arousal': [0.018, 0.027, 0.044, 0.025, 0.049, 0.03, 0.036, 0.029, 0.054, 0.025, 0.04, 0.032, 0.035]
}

# Create DataFrame
df = pd.DataFrame(data)

# Save to CSV
df.to_csv('sample_data.csv', index=False)
print("Sample data has been saved to 'sample_data.csv'")

# created simulated data for testing where it expanded to at least three different values in arousal and valance per each post
# Create expanded sample data with multiple measurements per post
expanded_data = {
    'group': [],
    'post': [],
    'valence': [],
    'arousal': []
}

# For each original row, create 3 measurements with some random variation
np.random.seed(42)  # For reproducibility
for group, post, val, aro in zip(data['group'], data['post'], data['valence'], data['arousal']):
    for _ in range(3):  # Create 3 measurements per post
        expanded_data['group'].append(group)
        expanded_data['post'].append(post)
        # Add random variation to valence and arousal (±20%)
        expanded_data['valence'].append(val + np.random.uniform(-0.2 * abs(val), 0.2 * abs(val)))
        expanded_data['arousal'].append(aro + np.random.uniform(-0.2 * abs(aro), 0.2 * abs(aro)))

# Create expanded DataFrame
df_expanded = pd.DataFrame(expanded_data)

# Round values to 3 decimal places
df_expanded['valence'] = df_expanded['valence'].round(3)
df_expanded['arousal'] = df_expanded['arousal'].round(3)

# Save expanded data to CSV
df_expanded.to_csv('sample_data_expanded.csv', index=False)
print("Expanded sample data has been saved to 'sample_data_expanded.csv'")
