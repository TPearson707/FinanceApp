import os
from datetime import timedelta

# Enable XLA JIT compilation for potential speed-ups
os.environ["TF_XLA_FLAGS"] = "--tf_xla_auto_jit=2"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"  # Reduce verbosity

import glob
import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Input, Dense, LSTM, Dropout, Embedding, Flatten, concatenate
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras import mixed_precision

# GPU Setup and Optimization 
gpus = tf.config.list_physical_devices('GPU')
if gpus:
    print("GPUs detected:")
    for gpu in gpus:
        print(" -", gpu)
    try:
        tf.config.experimental.set_virtual_device_configuration(
            gpus[0],
            [tf.config.experimental.VirtualDeviceConfiguration(memory_limit=5000)]
        )
        logical_gpus = tf.config.experimental.list_logical_devices('GPU')
        print(f"Set GPU memory limit to 5000 MB. {len(logical_gpus)} logical GPU(s) configured.")
    except RuntimeError as e:
        print(e)
else:
    print("No GPU detected. Please check your installation.")

mixed_precision.set_global_policy('mixed_float16')
print("Mixed precision enabled.")
tf.config.optimizer.set_jit(True)

# Define the number of previous time steps for sequence creation.
time_steps = 60

# Data Aggregation from CSV Files 
folder_path = '/Users/adame/Downloads/archive/stock_market_data/sp500/csv'  # Update with your folder path
csv_files = glob.glob(os.path.join(folder_path, '*.csv'))

# build lists for each stock's closing prices, dates, and assign a stock id from the ticker
all_X, all_y, all_stock_ids = [], [], []
all_close_prices_list = []  # For scaling later
all_tickers = []           # To keep track of tickers

# Build a mapping: each CSV file gets a unique stock id based on its ticker
ticker_to_id = {}
current_id = 0

def create_dataset_per_stock(data, stock_ids, time_steps):
    X, y, sid = [], [], []
    for i in range(len(data) - time_steps):
        X.append(data[i:i+time_steps, 0])        # sequence of close prices
        y.append(data[i+time_steps, 0])           # label: next day's close price
        sid.append(stock_ids[i+time_steps])       # stock id for the label
    return np.array(X), np.array(y), np.array(sid)

for file in csv_files:
    # Extract the stock ticker from the file name  "AAPL.csv" -> "AAPL"
    ticker = os.path.splitext(os.path.basename(file))[0]
    if ticker not in ticker_to_id:
        ticker_to_id[ticker] = current_id
        current_id += 1

    df = pd.read_csv(file)
    # Drop rows where 'Close' or 'Date' is missing
    df = df.dropna(subset=['Close', 'Date'])
    if 'Close' not in df.columns:
        print(f"Skipping {file} as it does not contain a 'Close' column.")
        continue

    # Convert dates assumed consistent and sort
    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df = df.dropna(subset=['Date'])
        df.sort_values('Date', inplace=True)
    close_prices = df['Close'].values.reshape(-1, 1)
    all_close_prices_list.append(close_prices)
    
    # Create an array of stock ids for this file.
    stock_ids = np.full((close_prices.shape[0],), ticker_to_id[ticker], dtype=int)
    
    X_stock, y_stock, sid_stock = create_dataset_per_stock(close_prices, stock_ids, time_steps)
    all_X.append(X_stock)
    all_y.append(y_stock)
    all_stock_ids.append(sid_stock)
    all_tickers.append(np.full((close_prices.shape[0],), ticker))
    
print("Ticker to ID mapping:", ticker_to_id)

if not all_X:
    raise ValueError("No CSV files with a 'Close' column were found.")

# Concatenate data from all stocks.
X_all = np.concatenate(all_X, axis=0)
y_all = np.concatenate(all_y, axis=0)
stock_ids_all = np.concatenate(all_stock_ids, axis=0)

# Build a global scaler on all closing prices from all stocks.
all_close_prices = np.concatenate(all_close_prices_list, axis=0)
scaler = MinMaxScaler(feature_range=(0, 1))
scaler.fit(all_close_prices)

# Scale the sequences and labels.
X_all_scaled = scaler.transform(X_all.reshape(-1, 1)).reshape(X_all.shape)
y_all_scaled = scaler.transform(y_all.reshape(-1, 1))

# Reshape X for LSTM: (samples, time_steps, 1)
X_all_scaled = X_all_scaled.reshape((X_all_scaled.shape[0], X_all_scaled.shape[1], 1))

print(f"Total sequences: {X_all_scaled.shape[0]}")
print(f"Number of stocks: {len(ticker_to_id)}")

# Create an Optimized Data Pipeline Using tf.data 
batch_size = 128  # Adjust based on your GPU memory.
dataset_tf = tf.data.Dataset.from_tensor_slices(((X_all_scaled, stock_ids_all), y_all_scaled))
dataset_tf = dataset_tf.cache().shuffle(buffer_size=1024).batch(batch_size).prefetch(tf.data.AUTOTUNE)

train_size = int(0.8 * X_all_scaled.shape[0])
train_dataset = dataset_tf.take(train_size // batch_size)
val_dataset = dataset_tf.skip(train_size // batch_size)

# Build and Compile the Multi-Task LSTM Model 
# Two inputs: one for the timeseries and one for the stock id.
timeseries_input = Input(shape=(time_steps, 1), name="timeseries_input")
stock_id_input = Input(shape=(1,), dtype='int32', name="stock_id_input")

# Process the timeseries input with an LSTM.
x = LSTM(50, return_sequences=False)(timeseries_input)
x = Dropout(0.2)(x)

# Process the stock id input with an Embedding layer.
embedding_dim = 10  # Adjust embedding dimension as needed.
s = Embedding(input_dim=len(ticker_to_id), output_dim=embedding_dim, input_length=1)(stock_id_input)
s = Flatten()(s)

# Concatenate the LSTM output with the stock embedding.
combined = concatenate([x, s])
output = Dense(1, name="closing_price")(combined)

model = tf.keras.Model(inputs=[timeseries_input, stock_id_input], outputs=output)

# Use a lower learning rate and add gradient clipping for stability.
base_optimizer = tf.keras.optimizers.Adam(learning_rate=5e-5, clipnorm=1.0)
optimizer = tf.keras.mixed_precision.LossScaleOptimizer(base_optimizer)
model.compile(optimizer=optimizer, loss='mean_squared_error')
model.summary()

# --- (Optional) Load Previous Weights if They Exist ---
weights_file = 'pretrained_weights.h5'
if os.path.exists(weights_file):
    model.load_weights(weights_file)
    print("Loaded previous weights from", weights_file)
else:
    print("No previous weights found. Training from scratch.")

# --- Train the Model ---
epochs = 50
history = model.fit(train_dataset,
                    epochs=epochs,
                    validation_data=val_dataset,
                    verbose=1)

model.save_weights(weights_file)
print("Weights saved to", weights_file)

# Predict the Next Day's Closing Price 
# For testing, use the last sequence from the global scaled data.
last_sequence = X_all_scaled[-1].reshape(1, time_steps, 1)
last_stock_id = stock_ids_all[-1].reshape(1, 1)
next_day_prediction = model.predict([last_sequence, last_stock_id])
predicted_price = scaler.inverse_transform(next_day_prediction)

# Retrieve the last date from the corresponding stock's data.
# For simplicity, using the global dates; ideally, you track per-stock dates.
all_dates = []
for file in csv_files:
    df = pd.read_csv(file)
    df = df.dropna(subset=['Date'])
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df = df.dropna(subset=['Date'])
    df.sort_values('Date', inplace=True)
    all_dates.extend(df['Date'].values)
all_dates = np.array(all_dates)
last_date = pd.to_datetime(all_dates[-1])
next_date = last_date + timedelta(days=1)  # Adjust for trading days if needed

print(f"Predicted closing price for stock {last_stock_id[0,0]} on {next_date.date()} is: {predicted_price[0, 0]:.2f}")
