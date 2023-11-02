import logging
from datetime import datetime, timedelta
from typing import List

import pandas as pd
from airflow.models import DagRun
from airflow.operators.python import PythonOperator
from common.constants import FILE_NAMES
from common.entities.indicators import Indicators
from common.hooks.cassandra_hook import CassandraHook
from common.hooks.spark_hook import SparkHook
from common.tasks.cassandra import insert_into_cassandra_indicators
from pyspark.sql import functions as F
from pyspark.sql.window import Window

from airflow import DAG

logging.basicConfig(level=logging.INFO)

from airflow.sensors.external_task import ExternalTaskSensor


def fetch_data(coin_name: str):
    
    conn = CassandraHook.get_connection(conn_id="cassandra_default")
    spark_session = SparkHook(app_name=__name__).get_spark_cassandra_session()
    
    df = spark_session.read \
        .format("org.apache.spark.sql.cassandra") \
        .options(
            keyspace="price_oracle",
            table="price_candlestick",
            url=conn.get_uri(),
            pushdown="true",  # Enable pushdown
        )\
        .load() \
        .filter(f"coin = '{coin_name}'")
    
    # keep only date and close_price columns
    df = df.select("close_time_date", "close_price", "coin")

    # serialize the dataframe with pickle
    data = df.toPandas()
    data_path = f"/tmp/{coin_name}_data.pkl"
    data.to_pickle(data_path)
    return data_path


def compute_indicators(data_path: str, coin_name: str):

    spark_session = SparkHook(app_name="initial_compute_indicators").get_spark_cassandra_session()

    # Load the data from a pickle file
    logging.info(f"Loading data from {data_path}")
    df = pd.read_pickle(data_path)

    # Convert the data to a Spark DataFrame
    df = spark_session.createDataFrame(df)

    # Sort the DataFrame by date
    df = df.orderBy("close_time_date")

    # Define a window specification based on the date column
    window_spec = Window.orderBy("close_time_date")
    
    # Define the window sizes for SMA
    sma_window_sizes = [5,10,20,50,100,200]

    # Calculate Simple Moving Average (SMA) for each window size
    for window_size in sma_window_sizes:
        # Define the column name for the SMA
        sma_column = f"sma_{window_size}"
        # Calculate the SMA using a window function
        df = df.withColumn(sma_column, F.avg("close_price").over(window_spec.rowsBetween(-window_size, 0)))

    # Convert the Spark DataFrame back to a Pandas DataFrame and then to a list of Indicators
    df = df.toPandas()
    df['close_time_date'] = pd.Series(df['close_time_date'].dt.to_pydatetime(), dtype = object)
    df = df.to_dict("records")
    df: List[Indicators] = [Indicators.model_validate(item) for item in df]

    return df

    
for file_name in FILE_NAMES:
    coin_name = file_name.split(".")[0]

    with DAG(
        f"compute_indicators_{coin_name}",
        schedule="@once",
        start_date=datetime.now(),
        default_args={
            "owner": "ranierifr",
            "retry_delay": timedelta(minutes=1),
            "retries": 5
        },
        is_paused_upon_creation=True,
        tags=["spark", "indicators", coin_name]
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


        compute_indicators_task = PythonOperator(
            task_id="compute_indicators",
            python_callable=compute_indicators,
            op_args=[data_path_task.output, coin_name],
        )

        insert_into_cassandra_indicators_task = PythonOperator(
            task_id="insert_into_cassandra_indicators",
            python_callable=insert_into_cassandra_indicators,
            op_args=[compute_indicators_task.output]
        )

        # Set up task dependencies
        external_task_sensor >> data_path_task  # Wait for the external DAG to complete
        data_path_task >> compute_indicators_task  # Fetch data before computing indicators
        compute_indicators_task >> insert_into_cassandra_indicators_task


    if __name__ == "__main__":
        dag.test()
