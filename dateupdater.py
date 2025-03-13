import os
import glob
import pandas as pd

# Set the folder path containing your CSV files.
folder_path = r'C:\Users\adame\Downloads\5minutecharts'  # <<< Update this path if needed

# Get a list of CSV files in the folder.
csv_files = glob.glob(os.path.join(folder_path, '*.csv'))

# Define the desired output datetime format.
output_datetime_format = '%Y-%m-%d %H:%M:%S'

def process_csv(file_path):
    try:
        # Read the CSV file.
        df = pd.read_csv(file_path)
        # Check if the 'timestamp' column exists.
        if 'time' not in df.columns:
            print(f"Skipping {file_path} (no 'timestamp' column)")
            return
        
        # Convert UNIX timestamp (assumed to be in seconds) to datetime.
        # If your timestamps are in milliseconds, use unit='ms'
        df['time'] = pd.to_datetime(df['time'], unit='s', errors='coerce')
        
        # Convert the datetime column to the desired format.
        df['time'] = df['time'].dt.strftime(output_datetime_format)
        
        # Write the updated DataFrame back to CSV (overwriting the file).
        df.to_csv(file_path, index=False)
        print(f"Updated timestamps in: {file_path}")
    except Exception as e:
        print(f"Error processing {file_path}: {e}")

# Process each CSV file in the folder.
for file in csv_files:
    process_csv(file)
