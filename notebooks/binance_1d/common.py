import os
from math import sqrt

import keras.backend as K
import matplotlib.pyplot as plt
import optuna
import pandas as pd
from sklearn.metrics import mean_absolute_percentage_error, mean_squared_error
from keras.callbacks import Callback
import numpy as np

import mlflow

# Create sequences of data to be used for training
def create_sequences(data, sequence_length):
    sequences = []
    target = []
    for i in range(len(data) - sequence_length):
        sequences.append(data[i:i+sequence_length])
        target.append(data[i+sequence_length])
    return np.array(sequences), np.array(target)


def mean_absolute_percentage_error_keras(y_true, y_pred):
    diff = K.abs((y_true - y_pred) / K.clip(K.abs(y_true), K.epsilon(), None))
    return 100.0 * K.mean(diff, axis=-1)

class OptunaPruneCallback(Callback):
    def __init__(self, trial):
        super(Callback, self).__init__()
        self.trial = trial

    def on_epoch_end(self, epoch, logs={}):
        if self.trial:
            self.trial.report(logs["val_mean_absolute_percentage_error_keras"], epoch)
            if self.trial.should_prune():
                raise optuna.TrialPruned()


def get_dataframe():
        
    folder = os.path.join("../../airflow/assets/binance_1d")
    dfs = []
    for file in os.listdir(folder):
        if file.endswith(".csv"):
            dfs.append(pd.read_csv(os.path.join(folder, file), skiprows=1, parse_dates=['Date']))

    # Step 1: Convert "date" column to datetime in all dataframes
    for df in dfs:
        df['Date'] = pd.to_datetime(df['Date'], format='%Y-%m-%d', errors="coerce")

    # Step 2: Find the oldest and newest dates across all dataframes
    all_dates = [df['Date'] for df in dfs]
    all_dates_flat = [date for sublist in all_dates for date in sublist if not pd.isnull(date)]

    oldest_date = '2019-01-01'
    newest_date = max(all_dates_flat)

    # Step 3: Create a new dataframe with the date range
    date_range = pd.date_range(start=oldest_date, end=newest_date, freq='D')  # Daily frequency
    merged_df = pd.DataFrame({'Date': date_range})

    # Step 4: Add "close" and "Volume USDT" columns from each dataframe to the merged_df using list comprehension
    for df in dfs:
        try:
            ticker = df['Symbol'].iloc[0]  # Assuming each dataframe has a "symbol" column
            close_col_name = f'close_{ticker}'
            volume_col_name = f'Volume USDT_{ticker}'  # Replace with the actual column name if it's different in your data

            df = df.set_index('Date').sort_index()

            # Create DataFrames with the "date" and "close" columns
            close_data = df[df.index.isin(date_range)][['Close']]
            close_data.rename(columns={'Close': close_col_name}, inplace=True)

            # Merge the "close_data" into the "merged_df"
            merged_df = pd.merge(merged_df, close_data, left_on='Date', right_index=True, how='left')

        except ValueError as e:
            print(f'Error on coin {ticker}: {e}')

    return merged_df


def get_clustered_dataframes():

    merged_df = get_dataframe()
    experiment = _get_experiments_from_mlflow()

    # Use eval() to convert the string to a list of tuples
    data_list = eval(experiment["params.Cluster_Labels"].tolist()[0])

    # Convert the list of tuples to a dictionary
    data_dict = dict(data_list)

    # Create a map where keys are the values from the original dictionary
    cripto_clusters = {}
    for key, value in data_dict.items():
        if value in cripto_clusters:
            cripto_clusters[value].append(key)
        else:
            cripto_clusters[value] = [key]

    clusters_data = {}

    # loop on key and value of cripto_clusters
    for cluster, criptos in cripto_clusters.items():
        _criptos = criptos + ['Date']
        clusters_data[cluster] = merged_df[_criptos]
    
    return clusters_data


def _get_experiments_from_mlflow(experiment_id: str = "110357928989408424", run_id: str = "35f1bb80732f433297fda78e6638feab"):
    experiments = mlflow.search_runs(experiment_ids=experiment_id)
    return experiments.loc[experiments['run_id'] == run_id]


def register_training_experiment(
    data,
    predictions,
    model_name = None,
    coin = None,
    x_axis = None,
    params = {},
):

    if x_axis is None:
        x_axis = range(len(data))
        
    plt.figure(figsize=(10, 6))
    plt.plot(x_axis, data, label='original')
    plt.plot(x_axis, predictions, label='predicted')
    plt.legend()
    plt.title(f"{coin}")
    plt.show()

    with mlflow.start_run(run_name='Evaluation', nested=True):
        mlflow.log_params({
            'model': model_name,
            'coin': coin,
            **params
        })

        for days in [len(data), 90, 30, 7]:
            mse = mean_squared_error(data[-days:], predictions[-days:])
            rmse = sqrt(mse)
            mape = mean_absolute_percentage_error(data[-days:], predictions[-days:])
            print(f"Metrics for {days} days: {coin} MSE: {mse}, RMSE: {rmse}", f"MAPE: {mape}")

            suffix = 'all' if days == len(data) else days
            mlflow.log_metrics({
                f'mse_{suffix}': mse,
                f'rmse_{suffix}': rmse,
                f'mape_{suffix}': mape
            })