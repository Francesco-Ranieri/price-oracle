import numpy as np
import pandas as pd
from common import register_training_experiment
from models import mean_absolute_percentage_error_keras
from pandas import DataFrame
from sklearn.preprocessing import MinMaxScaler
from statsmodels.tsa.vector_ar.var_model import VAR

import mlflow
import optuna


def objective(trial, data, coins, output_shape = None):

    with mlflow.start_run() as run:
        mlflow.statsmodels.autolog(log_models=False)
        
        trend = trial.suggest_categorical('trend', ['n','c','t','ct'])
        sequence_length = trial.suggest_int('sequence_length', 1, 5)
        min_max_scaling = trial.suggest_int('min_max_scaling', 0, 1)
               
        mlflow.log_params({
            'coin': coins,
            'trend': trend,
            'sequence_length': sequence_length,
            'min_max_scaling': min_max_scaling,
        })
        
        date_column = data['Date']
        data = data.drop(['Date'], axis=1)

        if min_max_scaling == 1:
            scaler = MinMaxScaler()
            data = scaler.fit_transform(np.array(data))

        train, valid, test = data_preparation(data, date_column)
        
        # Train the model with early stopping
        model = VAR(train)
        model_fit = model.fit(sequence_length, trend)
        
        # Make predictions on the validation set
        preds = model_fit.forecast(model_fit.endog, steps=len(valid))

        # Calculate the evaluation metric (e.g., Mean Squared Error)
        mape = mean_absolute_percentage_error_keras(np.array(valid), (np.array(preds)))
        
        # Mean the mapes for all coins
        mape = np.mean(mape)
        
        mlflow.log_param('aic', model_fit.aic)
        mlflow.log_metric('mape', mape)
        
        return mape
    

def data_preparation(cluster_data, date_column):
    
    data = DataFrame(cluster_data)
    
    # Data preparation
    data.index = pd.to_datetime(date_column, format='%Y-%m-%d')  # Modify the format as needed

    data = data.asfreq('D')  # Specify the frequency as 'D' for daily data

    # Step 3: Dealing with missing values --> already done

    # Step 4: Split the data into train and test sets
    train_size = int(len(data) * 0.7)
    test_size = (len(data) - train_size) / 2

    train = data.iloc[0:train_size] 
    valid = data.iloc[train_size:int(len(data) - test_size)]
    test = data.iloc[int(train_size + test_size):len(data)]

    assert len(data) == len(train) + len(valid) + len(test)

    return train, valid, test


def evaluate_best_coin(
    coin,
    data,
    best_params,
    output_shape = None
):
    """
    Evaluate the best model for a given coin
    
    :param coin: The coin to be used for training
    :param data: The data to be used for training
    :param best_params: The best hyperparameters found by Optuna
    """

    # Train the final model with the best hyperparameters
    # Define the search space for hyperparameters

    trend = best_params['trend']
    sequence_length = best_params['sequence_length']
    min_max_scaling = best_params['min_max_scaling']
    
    date_column = data['Date']
    data = data.drop(['Date'], axis=1)
    if min_max_scaling == 1:
        scaler = MinMaxScaler()
        data = scaler.fit_transform(np.array(data))

    train, valid, test = data_preparation(data, date_column)
    
    # concatenate train and validation sets
    train = np.concatenate((train, valid))
       

    with mlflow.start_run(
        run_name=f"Training_best_model_{coin}"
    ) as run:
    
        mlflow.log_params({
            'coin': coin,
            'trend': trend,
            'sequence_length': sequence_length,
            'min_max_scaling': min_max_scaling,
        })
        
        model = VAR(train)
        model_fit = model.fit(sequence_length, trend)

        preds = model_fit.forecast(model_fit.endog, steps=len(test))

        if min_max_scaling == 1:
            preds = scaler.inverse_transform(preds)
            test = scaler.inverse_transform(test)

        register_training_experiment(test, preds, coin = coin)