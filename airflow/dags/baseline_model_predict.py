import logging
from datetime import datetime, timedelta
from typing import List

import pandas as pd
from airflow.models import DagRun
from airflow.operators.python import PythonOperator
from common.constants import FILE_NAMES
from common.entities.prediction import Prediction
from common.hooks.spark_hook import SparkHook
from common.tasks.cassandra import insert_into_cassandra_predictions, insert_into_cassandra_metrics
from common.tasks.metrics import compute_metrics
from pyspark.sql import functions as F
from pyspark.sql.window import Window

from airflow import DAG

logging.basicConfig(level=logging.INFO)

from airflow.sensors.external_task import ExternalTaskSensor


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
    data_path = f"/tmp/{coin_name}_baseline_predict_data.pkl"
    data.to_pickle(data_path)
    return data_path


def predict(data_path: str) -> List[Prediction]:

    spark_session = SparkHook(app_name=f"{__name__}:predict").get_spark_session()

    # Load the data from a pickle file
    logging.info(f"Loading data from {data_path}")
    df = pd.read_pickle(data_path)

    # Convert the data to a Spark DataFrame
    df = spark_session.createDataFrame(df)

    # keep only date and close_price columns
    df = df.select("close_time_date", "close_price", "coin")

    # predict each day price with the price of the previous day
    df = df.withColumn("close_price", F.lag("close_price", 1).over(Window.orderBy("close_time_date")))

    # add a column with the model name
    df = df.withColumn("model_name", F.lit("BASELINE_LAG_1"))

    # Convert the Spark DataFrame back to a Pandas DataFrame and then to a list of Indicators
    df = df.toPandas()
    df['close_time_date'] = pd.Series(df['close_time_date'].dt.to_pydatetime(), dtype = object)
    data = df.to_dict("records")
    data: List[Prediction] = [Prediction.model_validate(item) for item in data]

    return data

    
for file_name in FILE_NAMES:
    coin_name = file_name.split(".")[0]

    with DAG(
        f"baseline_model_predict_{coin_name}",
        schedule="30 8 * * *",
        start_date=datetime.now(),  
        default_args={
            "owner": "gianfranco",
            "retry_delay": timedelta(minutes=1),
            "retries": 5
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


        data_path_task = PythonOperator(
            task_id="fetch_data",
            python_callable=fetch_data,
            op_args=[coin_name],
        )


        predict_task = PythonOperator(
            task_id="predict",
            python_callable=predict,
            op_args=[data_path_task.output],
        )


        insert_into_cassandra_predictions_task = PythonOperator(
            task_id="insert_into_cassandra_predictions",
            python_callable=insert_into_cassandra_predictions,
            op_args=[predict_task.output]
        )


        compute_metrics_task = PythonOperator(
            task_id="compute_metrics",
            python_callable=compute_metrics,
            op_args=[data_path_task.output, predict_task.output, coin_name],
        )


        insert_into_cassandra_metrics_task = PythonOperator(
            task_id="insert_into_cassandra_metrics",
            python_callable=insert_into_cassandra_metrics,
            op_args=[compute_metrics_task.output]
        )


        # Set up task dependencies
        external_task_sensor >> data_path_task  # Wait for the external DAG to complete
        data_path_task >> predict_task  # Fetch data before computing indicators
        predict_task >> insert_into_cassandra_predictions_task
        predict_task >> compute_metrics_task
        compute_metrics_task >> insert_into_cassandra_metrics_task

    if __name__ == "__main__":
        dag.test()
