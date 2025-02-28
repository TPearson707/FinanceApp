import os
import glob
import pandas as pd

# Set the folder path containing your CSV files
folder_path = '/Users/adame/Downloads/archive/stock_market_data/nyse/csv'  # <<< Update this path

# Get a list of CSV files in the folder
csv_files = glob.glob(os.path.join(folder_path, '*.csv'))

# Define the desired output date format (ISO: YYYY-MM-DD)
output_date_format = '%Y-%m-%d'

def process_csv(file_path):
    try:
        # Read the CSV file
        df = pd.read_csv(file_path)
        # Check if the 'Date' column exists
        if 'Date' not in df.columns:
            print(f"Skipping {file_path} (no 'Date' column)")
            return
        
        # Parse the date with dayfirst=True so that e.g., 27-09-2005 and 3/10/2005 are handled correctly.
        # Any errors will result in NaT.
        df['Date'] = pd.to_datetime(df['Date'], dayfirst=True, errors='coerce')
        
        # Optionally, you can drop rows where the date could not be parsed:
        # df = df.dropna(subset=['Date'])
        
        # Convert the Date column to the desired format
        df['Date'] = df['Date'].dt.strftime(output_date_format)
        
        # Write the updated DataFrame back to CSV (overwriting the file)
        df.to_csv(file_path, index=False)
        print(f"Updated dates in: {file_path}")
    except Exception as e:
        print(f"Error processing {file_path}: {e}")

# Process each CSV file in the folder
for file in csv_files:
    process_csv(file)
