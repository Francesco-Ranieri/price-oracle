import logging
from datetime import datetime

import keras
import numpy as np
import pandas as pd
from airflow.models import DagRun
from airflow.operators.python import PythonOperator
from airflow.sensors.external_task import ExternalTaskSensor
from common.constants import FILE_NAMES
from common.hooks.spark_hook import SparkHook
from common.models.models import build_model, get_splits
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


def get_data(
    data_path: str,
    sequence_length: int,
    output_shape: int,
    min_max_scaling: int = 1
):

    spark_session = SparkHook(
        app_name=f"{__name__}:predict").get_spark_session()

    # Load the data from a pickle file
    logging.info(f"Loading data from {data_path}")
    df = pd.read_pickle(data_path)

    # Convert the data to a Spark DataFrame
    df = spark_session.createDataFrame(df)

    # keep only date and close_price columns
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

    return data, scaler, X_train, X_test, y_train, y_test


def train(
    data_path: str,
    coin: str
):
    mlflow.set_tracking_uri("http://price-oracle-mlflow:5000")

    # Mlflow search experiment by tag
    experiment = mlflow.search_experiments(
        filter_string="attribute.name = 'Training_LSTM_RNN'")[0]
    run = mlflow.search_runs(experiment_ids=experiment.experiment_id,
                             filter_string=f"attributes.run_name = 'Training_best_model_close_{coin}'").iloc[0]

    # Create df from run data
    run = pd.DataFrame(run).T

    # Get only columns that start with params., then remove params. from the column name
    run = run[run.columns[run.columns.str.startswith("params.")]]
    run.columns = run.columns.str.replace("params.", "")

    # Each column has a single row. Convert the df into a dictionary
    best_params = run.to_dict(orient="records")[0]

    # Make best_params a class so we can access its attributes
    best_params = type("best_params", (object,), best_params)()

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

    data, scaler, X_train, X_test, y_train, y_test = get_data(
        data_path, sequence_length, output_shape,
        min_max_scaling=min_max_scaling
    )

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

    # Train the model with early stopping
    model.fit(X_train, y_train, epochs=1, batch_size=batch_size)

    # Save the model on MLflow
    model_name = f"Airflow_LSTM_RNN_{coin}"
    mlflow.keras.log_model(
        model,
        artifact_path="models",
        registered_model_name=model_name,
    )

    return {
        "sequence_length": sequence_length,
        "output_shape": output_shape,
        "model_name": model_name,
        "min_max_scaling": min_max_scaling,
    }


def predict(
    data_path: str,
    train_output,
):

    print(train_output)

    data, scaler, X_train, X_test, y_train, y_test = get_data(
        data_path,
        train_output["sequence_length"],
        train_output["output_shape"],
        train_output["min_max_scaling"]
    )

    # Load the model from MlFlow
    model_name = train_output["model_name"]
    model = mlflow.pyfunc.load_model(model_uri=f"mlflow-artifacts:/{model_name}/latest")

    preds = model.predict([X_test])

    if best_params.min_max_scaling == 1:
        preds = scaler.inverse_transform(preds)
        y_test = scaler.inverse_transform(y_test)

    return preds


for file_name in FILE_NAMES:
    coin_name = file_name.split(".")[0]

    with DAG(
        f"lstm_rnn_training_{coin_name}",
        schedule="@once",
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
                train_task.output
                # train_task.output["sequence_length"],
                # train_task.output["output_shape"],
                # train_task.output["model_name"],
                # train_task.output["min_max_scaling"],
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
            op_args=[fetch_data_task.output, predict_task.output, coin_name],
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
