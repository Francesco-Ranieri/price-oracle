import logging
from datetime import datetime
from typing import List

import keras
import numpy as np
import pandas as pd
from airflow.models import DagRun
from airflow.operators.python import PythonOperator
from airflow.sensors.external_task import ExternalTaskSensor
from common.constants import FILE_NAMES
from common.entities.prediction import Prediction
from common.hooks.spark_hook import SparkHook
from common.models.models import (build_model, get_splits,
                                  mean_absolute_percentage_error_keras)
from common.tasks.cassandra import (insert_into_cassandra_metrics,
                                    insert_into_cassandra_predictions)
from common.tasks.metrics import compute_metrics
from sklearn.preprocessing import MinMaxScaler

import mlflow
from airflow import DAG

logging.basicConfig(level=logging.INFO)


def fetch_data(coin_name: str):

    spark_hook = SparkHook(app_name=f"{__name__}:fetch_data")
    spark_session = spark_hook.get_spark_cassandra_session()

    df = spark_session.read \
        .format("org.apache.spark.sql.cassandra") \
        .options(
            keyspace="price_oracle",
            table="price_candlestick",
            url=spark_hook.cassandra_connection.get_uri(),
            pushdown="true",  # Enable pushdown
        )\
        .load() \
        .filter(f"coin = '{coin_name}'")

    # serialize the dataframe with pickle
    data = df.toPandas()
    data_path = f"/tmp/{coin_name}_lstm_rnn_predict_data.pkl"
    data.to_pickle(data_path)
    return data_path


def get_best_params(
    coin: str
):
    mlflow.set_tracking_uri("http://price-oracle-mlflow-tracking:5000")

    # Mlflow search experiment by tag
    experiment = mlflow.search_experiments(filter_string="attribute.name = 'Training_LSTM_RNN'")[0]
    run = mlflow.search_runs(experiment_ids=experiment.experiment_id, filter_string=f"attributes.run_name = 'Training_best_model_close_{coin}'").iloc[0]

    # Create df from run data
    run = pd.DataFrame(run).T

    # Get only columns that start with params., then remove params. from the column name
    run = run[run.columns[run.columns.str.startswith("params.")]]
    run.columns = run.columns.str.replace("params.", "")

    # Each column has a single row. Convert the df into a dictionary
    best_params = run.to_dict(orient="records")[0]

    # Make best_params a class so we can access its attributes
    best_params = type("best_params", (object,), best_params)()

    return best_params

def train(
    data_path: str,
    coin: str
):
    mlflow.set_tracking_uri("http://price-oracle-mlflow-tracking:5000")

    # Get best params from mlflow
    best_params = get_best_params(coin)
    units_per_layer = eval(best_params.units_per_layer)
    sequence_length = int(best_params.sequence_length)
    learning_rate = float(best_params.learning_rate)
    dropout_rate = float(best_params.dropout_rate)
    layer_type = best_params.layer_type
    optimizer = best_params.optimizer
    activation = best_params.activation
    weight_decay = float(best_params.weight_decay)
    output_shape = eval(best_params.output_shape) or 1
    min_max_scaling = int(best_params.min_max_scaling)
    batch_size = int(best_params.batch_size)

    # Get the data
    spark_session = SparkHook(
        app_name=f"{__name__}:predict").get_spark_session()

    logging.info(f"Loading data from {data_path}")
    df = pd.read_pickle(data_path)
    df = spark_session.createDataFrame(df)
    df = df.select("close_price")
    data = np.array(df.collect())

    scaler = None
    if min_max_scaling == 1:
        scaler = MinMaxScaler()
        data = scaler.fit_transform(data)

    # Split the data into training and validation sets
    X_train, X_test, X_val, y_train, y_test, y_val = get_splits(
        data, sequence_length, output_shape)
    X_train = np.concatenate((X_train, X_val))
    y_train = np.concatenate((y_train, y_val))

    # Build the model
    layer_class = keras.layers.LSTM if layer_type == 'LSTM' else keras.layers.SimpleRNN

    model = build_model(
        data,
        units_per_layer,
        sequence_length,
        learning_rate,
        dropout_rate,
        layer_class,
        optimizer,
        activation,
        weight_decay,
        output_shape
    )

    # TODO: Change to 100
    model.fit(X_train, y_train, epochs=100, batch_size=batch_size)

    # Save the model on MLflow
    model_name = f"Airflow_LSTM_RNN_{coin}"
    mlflow.tensorflow.log_model(
        model,
        artifact_path="models",
        registered_model_name=model_name,
    )
    
    return model_name


def predict(
    data_path: str,
    coin: str,
    model_name: str,
):
    mlflow.set_tracking_uri("http://price-oracle-mlflow-tracking:5000")

    # Get best params from mlflow
    best_params = get_best_params(coin)
    sequence_length = int(best_params.sequence_length)
    min_max_scaling = int(best_params.min_max_scaling)
    output_shape = eval(best_params.output_shape) or 1

    # Get the data
    spark_session = SparkHook(
        app_name=f"{__name__}:predict").get_spark_session()

    logging.info(f"Loading data from {data_path}")
    df = pd.read_pickle(data_path)
    df = spark_session.createDataFrame(df)

    # Get close price as a numpy array
    close_price = np.array(df.select("close_price").collect())

    scaler = None
    if min_max_scaling == 1:
        scaler = MinMaxScaler()
        close_price = scaler.fit_transform(close_price)

    # Split the data into training and validation sets
    X_train, X_test, X_val, y_train, y_test, y_val = get_splits(
        close_price, sequence_length, output_shape)
    X_train = np.concatenate((X_train, X_val))
    y_train = np.concatenate((y_train, y_val))

    # Get the close date time as a numpy array
    close_date_time = np.array(df.select("close_time_date").collect())
    close_date_time = close_date_time.reshape((close_date_time.shape[0],))
    close_date_time = close_date_time[len(X_train):]

    # Load model as a PyFuncModel.
    keras_model_kwargs = {
        'custom_objects': {
            'mean_absolute_percentage_error_keras': mean_absolute_percentage_error_keras
        }
    }
    model_uri = f"models:/{model_name}/latest"
    loaded_model = mlflow.tensorflow.load_model(model_uri, keras_model_kwargs=keras_model_kwargs)

    # Predict on the test set and inverse transform the predictionss
    preds = loaded_model.predict(X_test)

    if min_max_scaling == 1:
        preds = scaler.inverse_transform(preds)
        y_test = scaler.inverse_transform(y_test)

    # Convert the predictions into a list of Prediction objects
    data: List[Prediction] = [Prediction.model_validate({
        "close_time_date": date,
        "close_price": float(pred),
        "coin": coin,
        "model_name": "LSTM_RNN"
    }) for (date, pred) in zip(close_date_time, preds)]

    return data


for file_name in FILE_NAMES:
    coin_name = file_name.split(".")[0]

    with DAG(
        f"lstm_rnn_training_{coin_name}",
        schedule="10 8 * * 1",
        start_date=datetime.now(),
        default_args={
            "owner": "ranierifr"
        },
        is_paused_upon_creation=True,
        tags=["spark", "prediction", coin_name]
    ) as dag:

        def get_most_recent_dag_run(dt, dag_id=coin_name):
            dag_runs = DagRun.find(dag_id=f"initial_data_loading_{dag_id}")
            dag_runs.sort(key=lambda x: x.execution_date, reverse=True)
            if dag_runs:
                return dag_runs[0].execution_date

        external_task_sensor = ExternalTaskSensor(
            task_id=f"wait_for_initial_data_loading_{coin_name}",
            external_dag_id=f"initial_data_loading_{coin_name}",
            mode="reschedule",  # Use reschedule mode to wait for the external DAG to complete
            execution_date_fn=get_most_recent_dag_run,
        )

        fetch_data_task = PythonOperator(
            task_id="fetch_data",
            python_callable=fetch_data,
            op_args=[coin_name],
        )

        train_task = PythonOperator(
            task_id="train",
            python_callable=train,
            op_args=[fetch_data_task.output, coin_name],
        )

        predict_task = PythonOperator(
            task_id="predict",
            python_callable=predict,
            op_args=[
                fetch_data_task.output,
                coin_name,
                train_task.output
            ],
        )

        insert_into_cassandra_predictions_task = PythonOperator(
            task_id="insert_into_cassandra_predictions",
            python_callable=insert_into_cassandra_predictions,
            op_args=[predict_task.output]
        )

        compute_metrics_task = PythonOperator(
            task_id="compute_metrics",
            python_callable=compute_metrics,
            op_args=[
                fetch_data_task.output,
                predict_task.output,
                coin_name,
                "LSTM_RNN"
            ],
        )

        insert_into_cassandra_metrics_task = PythonOperator(
            task_id="insert_into_cassandra_metrics",
            python_callable=insert_into_cassandra_metrics,
            op_args=[compute_metrics_task.output]
        )

        # Set up task dependencies
        # Wait for the external DAG to complete
        external_task_sensor >> fetch_data_task
        fetch_data_task >> train_task  # Fetch data before computing indicators
        train_task >> predict_task
        predict_task >> insert_into_cassandra_predictions_task
        predict_task >> compute_metrics_task
        compute_metrics_task >> insert_into_cassandra_metrics_task

    if __name__ == "__main__":
        dag.test()
