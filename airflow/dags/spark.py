import os
import logging
from datetime import date, datetime, timedelta

import pandas as pd
from airflow.decorators import task
from pyspark.sql import SparkSession

from airflow import DAG

logging.basicConfig(level=logging.INFO)

@task
def spark_task():
    logging.info("RUNNING SPARK TASK")
    # Specify the SparkSubmitOperator to run your Spark job
    # spark_task = SparkSubmitOperator(
    #     task_id='spark_job_task',
    #     application='test.py',  # Path to your Spark job script
    #     conn_id='spark_default',  # The connection ID for your Spark cluster
    #     verbose=True,  # Set to True for debugging
    # ).execute(context=None)

    os.environ['PYSPARK_SUBMIT_ARGS'] = '--packages com.datastax.spark:spark-cassandra-connector_2.11:2.3.0'
    
    spark = SparkSession.builder \
                .appName("CassandraSpark") \
                .master("spark://price-oracle-spark-master-svc:7077") \
                .getOrCreate()
    
    # connect to cassandra and read table
    df = spark.read.format("org.apache.spark.sql.cassandra") \
            .options(table="price_candlestick", keyspace="mykeyspace") \
            .option("spark.cassandra.auth.username", "cassandra") \
            .option("spark.cassandra.auth.password", "Y2Fzc2FuZHJh") \
            .load()
    
    # pandas_df = pd.DataFrame({
    # 'a': [1, 2, 3],
    # 'b': [2., 3., 4.],
    # 'c': ['string1', 'string2', 'string3'],
    # 'd': [date(2000, 1, 1), date(2000, 2, 1), date(2000, 3, 1)],
    # 'e': [datetime(2000, 1, 1, 12, 0), datetime(2000, 1, 2, 12, 0), datetime(2000, 1, 3, 12, 0)]
    # })
    # df = spark.createDataFrame(pandas_df)

    # All DataFrames above result same.
    df.show()
    df.printSchema()
    df.show(1)

    # logging.info("Full dataframe:")
    # df.show()

    # df = spark.read.format("org.apache.spark.sql.cassandra") \
    #         .options(table="price_candlestick", keyspace="mykeyspace") \
    #         .option("spark.cassandra.auth.username", "cassandra") \
    #         .option("spark.cassandra.auth.password", "Y2Fzc2FuZHJh") \
    #         .load()
    # df.show()

with DAG(
    "spark_load_data_from_cassandra",
    schedule="@once",
    start_date=datetime.now() - timedelta(days=1),
    default_args={
        "owner": "ranierifr"
    },
    is_paused_upon_creation=False,
    tags=["spark"]
) as dag:
  spark_task()

if __name__ == "__main__":
    dag.test()