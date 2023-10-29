import logging
from datetime import datetime

import numpy as np
import pandas as pd
from airflow.models import DagRun
from airflow.operators.python import PythonOperator
from airflow.sensors.external_task import ExternalTaskSensor
from common.constants import FILE_NAMES
from common.hooks.spark_hook import SparkHook
from common.tasks.cassandra import (insert_into_cassandra_metrics,
                                    insert_into_cassandra_predictions)
from common.tasks.metrics import compute_metrics

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


def train(
    data_path: str,
    coin: str
):
    from common.models.models import build_model, get_splits
    from sklearn.preprocessing import MinMaxScaler

    import mlflow

    mlflow.set_tracking_uri("http://price-oracle-mlflow:5000")

    # Mlflow search experiment by tag
    experiment = mlflow.search_experiments(filter_string="attribute.name = 'Training BASELINE'")[0]
    print(f"experiment id: {experiment.experiment_id}")
    run = mlflow.search_runs(experiment_ids=experiment.experiment_id, filter_string=f"params.coin = 'close_{coin}'").iloc[0]

    print(run)
    print(dir(run))

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

    if best_params.min_max_scaling == 1:
        scaler = MinMaxScaler()
        data = scaler.fit_transform(data)

    # Split the data into training and validation sets
    X_train, X_test, X_val, y_train, y_test, y_val = get_splits(
        data, best_params.sequence_length, best_params.output_shape)
    X_train = np.concatenate((X_train, X_val))
    y_train = np.concatenate((y_train, y_val))

    model = build_model(
        data,
        best_params.units_per_layer,
        best_params.sequence_length,
        best_params.learning_rate,
        best_params.dropout_rate,
        best_params.layer_class,
        best_params.optimizer,
        best_params.activation,
        best_params.weight_decay,
        best_params.output_shape
    )

    # Train the model with early stopping
    model.fit(X_train, y_train, epochs=100, batch_size=best_params.batch_size)

    # Save the model on MLflow
    mlflow.keras.log_model(model, "model")

    return {
        "best_params": best_params,
        "model": model,
        "scaler": scaler,
        "X_test": X_test,
        "y_test": y_test
    }


def predict(
    best_params,
    model,
    scaler,
    X_test,
    y_test,
    **kwargs
):
    
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
                train_task.output["best_params"],
                train_task.output["model"],
                train_task.output["scaler"],
                train_task.output["X_test"],
                train_task.output["y_test"]
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
        external_task_sensor >> fetch_data_task  # Wait for the external DAG to complete
        fetch_data_task >> train_task  # Fetch data before computing indicators
        train_task >> predict_task
        predict_task >> insert_into_cassandra_predictions_task
        predict_task >> compute_metrics_task
        compute_metrics_task >> insert_into_cassandra_metrics_task

    if __name__ == "__main__":
        dag.test()
