import os
from math import sqrt

import matplotlib.pyplot as plt
import pandas as pd
from sklearn.metrics import mean_absolute_percentage_error, mean_squared_error

import mlflow


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


def register_training_experiment(
    model_name,
    coin,
    data,
    predictions,
    x_axis,
    params = {}
):
        
    mlflow.set_experiment(f'Training_{model_name}')

    plt.figure(figsize=(10, 6))
    plt.plot(x_axis, data, label='original')
    plt.plot(x_axis, predictions, label='lagged')
    plt.legend()
    plt.title(f"{coin}")
    plt.show()

    # calculate MSE, RMSE and MAPE for all data, last 90, 30 and 7 days
    with mlflow.start_run():

        for days in [len(data), 90, 30, 7]:
        
            mse = mean_squared_error(data[-days:], predictions[-days:])
            rmse = sqrt(mse)
            mape = mean_absolute_percentage_error(data[-days:], predictions[-days:])
            print(f"{coin} MSE: {mse}, RMSE: {rmse}", f"MAPE: {mape}")

            mlflow.log_params({
                'model': model_name,
                'coin': coin,
                **params
            })

            suffix = 'all' if days == len(data) else days

            mlflow.log_metrics({
                f'mse_{suffix}': mse,
                f'rmse_{suffix}': rmse,
                f'mape_{suffix}': mape
            })