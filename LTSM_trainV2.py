import os
import glob
import numpy as np
import pandas as pd
import tensorflow as tf
from datetime import timedelta
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Input, Dense, LSTM, Dropout, Embedding, Flatten, concatenate, Lambda
from tensorflow.keras.regularizers import l2
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
from tensorflow.keras import mixed_precision

# ------------------------------
# GPU Setup and Mixed Precision
# ------------------------------
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
    print("No GPU detected.")

mixed_precision.set_global_policy('mixed_float16')
print("Mixed precision enabled.")
tf.config.run_functions_eagerly(True)  # For debugging
tf.config.optimizer.set_jit(True)

# ------------------------------
# Settings and CSV Paths
# ------------------------------
time_steps = 60
batch_size = 128
num_clusters = 3  # For hierarchical clustering (using stock_id % num_clusters)
csv_folder = r'C:\Users\adame\Downloads\5minutecharts'
csv_files = glob.glob(os.path.join(csv_folder, '*.csv'))
print(f"Found {len(csv_files)} CSV files in {csv_folder}")

# Mapping from ticker to a unique stock id.
ticker_to_id = {}

# ------------------------------
# Generator Function for Streaming Data (with Debugging)
# ------------------------------
def data_generator():
    total_examples = 0
    for file in csv_files:
        # Extract ticker from filename (e.g., "AAPL.csv" -> "AAPL")
        ticker = os.path.splitext(os.path.basename(file))[0]
        if ticker not in ticker_to_id:
            ticker_to_id[ticker] = len(ticker_to_id)
        stock_id = ticker_to_id[ticker]
        cluster_id = stock_id % num_clusters  # Simple clustering

        print(f"\nProcessing file: {file}, ticker: {ticker}")
        try:
            df = pd.read_csv(file)
        except Exception as e:
            print(f"Error reading {file}: {e}")
            continue

        # Standardize column names to lowercase.
        df.columns = df.columns.str.lower()
        print(f"Columns in {file}: {df.columns.tolist()}")

        # Check for required columns 'time' and 'close'
        required_columns = ['time', 'close']
        if not set(required_columns).issubset(set(df.columns)):
            print(f"File {file} missing required columns {required_columns}. Skipping.")
            continue

        # Drop rows missing 'time' or 'close'
        df = df.dropna(subset=['time', 'close'])
        print(f"{file} - rows after dropna: {df.shape[0]}")
        if df.empty:
            print(f"{file} has no valid rows after dropping missing values.")
            continue

        # Convert 'time' to datetime and sort.
        df['time'] = pd.to_datetime(df['time'], errors='coerce')
        df = df.dropna(subset=['time'])
        df.sort_values('time', inplace=True)
        print(f"{file} - rows after processing 'time': {df.shape[0]}")
        if df.empty:
            print(f"{file} has no valid datetime entries after processing.")
            continue

        # Use only the 'close' column.
        close_prices = df['close'].values.astype(np.float32).reshape(-1, 1)

        # Create a per-stock scaler and scale the close prices.
        scaler = MinMaxScaler(feature_range=(0, 1))
        scaled_close = scaler.fit_transform(close_prices)

        # Create sequences from scaled close prices.
        num_seq = len(scaled_close) - time_steps
        print(f"{file} - number of sequences: {num_seq}")
        for i in range(num_seq):
            seq = scaled_close[i:i+time_steps]       # shape: (time_steps, 1)
            label = scaled_close[i+time_steps, 0]      # next close price (normalized)
            total_examples += 1
            yield ((seq, np.array([stock_id], dtype=np.int32),
                    np.array([cluster_id], dtype=np.int32)),
                   np.array([label], dtype=np.float32))
    print(f"Total examples yielded: {total_examples}")

# Define output types and shapes.
output_types = ((tf.float32, tf.int32, tf.int32), tf.float32)
output_shapes = (((time_steps, 1), (1,), (1,)), (1,))

# ------------------------------
# Create Training and Validation Datasets
# ------------------------------
# Reinitialize dataset for training:
train_dataset = tf.data.Dataset.from_generator(data_generator, output_types=output_types, output_shapes=output_shapes)
train_dataset = train_dataset.shuffle(buffer_size=1024).batch(batch_size).prefetch(tf.data.AUTOTUNE)
# For validation, reinitialize with a different seed (if needed) or use the same generator.
val_dataset = tf.data.Dataset.from_generator(data_generator, output_types=output_types, output_shapes=output_shapes)
val_dataset = val_dataset.shuffle(buffer_size=1024).batch(batch_size).prefetch(tf.data.AUTOTUNE)

# ------------------------------
# Debug: Inspect One Batch from the Training Dataset
# ------------------------------
print("Inspecting one batch from the training dataset:")
for batch in train_dataset.take(1):
    (seq_batch, stock_id_batch, cluster_id_batch), label_batch = batch
    print("Sequence batch shape:", seq_batch.shape)       # Expected: (batch_size, time_steps, 1)
    print("Stock ID batch shape:", stock_id_batch.shape)     # Expected: (batch_size, 1)
    print("Cluster ID batch shape:", cluster_id_batch.shape) # Expected: (batch_size, 1)
    print("Label batch shape:", label_batch.shape)           # Expected: (batch_size, 1)
    break

# ------------------------------
# Build the Hierarchical LSTM Model
# ------------------------------
from tensorflow.keras.layers import Input, Dense, LSTM, Dropout, Embedding, Flatten, concatenate, Lambda

# Define model inputs.
timeseries_input = Input(shape=(time_steps, 1), name="timeseries_input")
stock_id_input = Input(shape=(1,), dtype='int32', name="stock_id_input")
cluster_id_input = Input(shape=(1,), dtype='int32', name="cluster_id_input")

# Common backbone: Stacked LSTM layers.
x = LSTM(50, return_sequences=True, kernel_regularizer=l2(1e-4))(timeseries_input)
x = Dropout(0.2)(x)
x = LSTM(30, return_sequences=False, kernel_regularizer=l2(1e-4))(x)
x = Dropout(0.2)(x)

# Process stock id with an Embedding layer.
embedding_dim = 10
s = Embedding(input_dim=max(len(ticker_to_id), 1), output_dim=embedding_dim, input_length=1)(stock_id_input)
s = Flatten()(s)

# Combine features.
common_features = concatenate([x, s])

# Build separate branches for each cluster.
branch_outputs = []
for i in range(num_clusters):
    branch = Dense(16, activation='relu')(common_features)
    branch = Dense(1)(branch)
    branch_outputs.append(branch)
branch_stack = concatenate(branch_outputs, axis=1)

# One-hot encode the cluster_id input.
one_hot_cluster = Lambda(lambda x: tf.one_hot(tf.cast(x, tf.int32), depth=num_clusters))(cluster_id_input)
one_hot_cluster = Flatten()(one_hot_cluster)

# Compute weighted sum over branch outputs.
def weighted_sum(inputs):
    one_hot, branches = inputs
    return tf.reduce_sum(one_hot * branches, axis=1, keepdims=True)
output = Lambda(weighted_sum)([one_hot_cluster, branch_stack])

model = Model(inputs=[timeseries_input, stock_id_input, cluster_id_input], outputs=output)

# Compile the model with run_eagerly=True for debugging.
base_optimizer = tf.keras.optimizers.Adam(learning_rate=5e-5, clipnorm=1.0)
optimizer = tf.keras.mixed_precision.LossScaleOptimizer(base_optimizer)
model.compile(optimizer=optimizer, loss='mean_squared_error', run_eagerly=True)
model.summary()

# ------------------------------
# Callbacks and Training
# ------------------------------
early_stop = EarlyStopping(monitor='loss', patience=5, restore_best_weights=True)
reduce_lr = ReduceLROnPlateau(monitor='loss', factor=0.5, patience=3, verbose=1)

epochs = 50
history = model.fit(train_dataset, epochs=epochs, validation_data=val_dataset, callbacks=[early_stop, reduce_lr], verbose=1)

# Evaluate on validation set.
val_loss = model.evaluate(val_dataset, verbose=1)
print("Validation loss:", val_loss)

# Save model weights.
weights_file = 'hierarchical_5min_weights.h5'
model.save_weights(weights_file)
print("Weights saved to", weights_file)
