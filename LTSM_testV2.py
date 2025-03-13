import os
from datetime import timedelta
import glob
import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Input, Dense, LSTM, Dropout, Embedding, Flatten, concatenate
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras import mixed_precision

# GPU Setup and Optimization
os.environ["TF_XLA_FLAGS"] = "--tf_xla_auto_jit=2"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

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

#  User Parameters
# Specify the stock ticker you want to test 
ticker = "AMZN"  # Change this ticker as needed

# Folder containing the CSV files (assumes one file per stock)
folder_path = '/Users/adame/Downloads/archive/stock_market_data/sp500/csv'
csv_file = glob.glob(os.path.join(folder_path, f'{ticker}.csv'))
if not csv_file:
    raise ValueError(f"No CSV file found for ticker {ticker}")
csv_file = csv_file[0]

# Data Aggregation for the Specific Stock
df = pd.read_csv(csv_file)
# Drop rows with missing values in 'Close' or 'Date'
df = df.dropna(subset=['Close', 'Date'])
if 'Close' not in df.columns:
    raise ValueError(f"CSV file {csv_file} does not contain a 'Close' column.")

# Convert the date column and sort the data
df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
df = df.dropna(subset=['Date'])
df.sort_values('Date', inplace=True)

# Extract closing prices and dates
close_prices = df['Close'].values.reshape(-1, 1)
dates = df['Date'].values

# Global Scaling Setup 
# For testing, we use a scaler that is fit on this stock's closing prices.
scaler = MinMaxScaler(feature_range=(0, 1))
scaler.fit(close_prices)
scaled_data = scaler.transform(close_prices)

# Create Sequences 
def create_dataset(dataset, time_steps=60):
    X, y = [], []
    for i in range(len(dataset) - time_steps):
        X.append(dataset[i:i + time_steps, 0])
        y.append(dataset[i + time_steps, 0])
    return np.array(X), np.array(y)

time_steps = 60
X_seq, y_seq = create_dataset(scaled_data, time_steps)
X_seq = X_seq.reshape((X_seq.shape[0], X_seq.shape[1], 1))

# For prediction, we use the last sequence from the dataset.
last_sequence = scaled_data[-time_steps:]
last_sequence = last_sequence.reshape((1, time_steps, 1))

# Model Architecture 
# The embedding layer must have the same input_dim as used during training.
# Suppose during training, the model was built on 409 stocks.
embedding_input_dim = 409  # Adjust to match your training configuration

# For testing a single stock, we need its stock id.
# You must use the same mapping that was used during training.
# For this example, we assume the mapping was persisted and ticker "AAPL" was assigned id 0.
# In practice, load your saved mapping.
stock_id_mapping = {ticker: 0}
stock_id = stock_id_mapping[ticker]

# Model architecture: Two inputs (timeseries and stock id).
timeseries_input = Input(shape=(time_steps, 1), name="timeseries_input")
stock_id_input = Input(shape=(1,), dtype='int32', name="stock_id_input")

# Timeseries branch
x = LSTM(50, return_sequences=False)(timeseries_input)
x = Dropout(0.2)(x)

# Stock id branch using embedding
s = Embedding(input_dim=embedding_input_dim, output_dim=10, input_length=1)(stock_id_input)
s = Flatten()(s)

# Concatenate the LSTM output and stock embedding
combined = concatenate([x, s])
output = Dense(1, name="closing_price")(combined)

model = tf.keras.Model(inputs=[timeseries_input, stock_id_input], outputs=output)

# Compile the model with the same optimizer settings as training
base_optimizer = tf.keras.optimizers.Adam(learning_rate=5e-5, clipnorm=1.0)
optimizer = tf.keras.mixed_precision.LossScaleOptimizer(base_optimizer)
model.compile(optimizer=optimizer, loss='mean_squared_error')
model.summary()

# Load Pretrained Weights 
weights_file = 'test_models/LTSM_stockIDS.h5'
if os.path.exists(weights_file):
    model.load_weights(weights_file)
    print("Loaded pretrained weights from", weights_file)
else:
    raise ValueError("Pretrained weights file not found.")

# Predict the Next Day's Closing Price 
import numpy as np
stock_id_array = np.array([stock_id]).reshape(1, 1)
next_day_prediction = model.predict([last_sequence, stock_id_array])
predicted_price = scaler.inverse_transform(next_day_prediction)

# Retrieve the last date from the data and compute the next date.
last_date = pd.to_datetime(dates[-1])
next_date = last_date + timedelta(days=1)  # Adjust for trading days if necessary.

print(f"Predicted closing price for stock {ticker} on {next_date.date()} is: {predicted_price[0, 0]:.2f}")
