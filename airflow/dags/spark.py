import os
import logging
from datetime import date, datetime, timedelta

import pandas as pd
from airflow.decorators import task
from pyspark.sql import SparkSession
from common.hooks.cassandra_hook import CassandraHook

from airflow import DAG

logging.basicConfig(level=logging.INFO)

@task
def spark_task():
    conn = CassandraHook.get_connection(conn_id="cassandra_default")
    spark = SparkSession.builder \
                .appName("CassandraSpark") \
                .master("spark://price-oracle-spark-master-svc:7077") \
                .config("spark.jars.packages", "com.datastax.spark:spark-cassandra-connector_2.12:3.4.1") \
                .config("spark.cassandra.connection.host", conn.host) \
                .config("spark.cassandra.auth.username", conn.login) \
                .config("spark.cassandra.auth.password", conn.password) \
                .getOrCreate()
    
    df = spark.read \
        .format("org.apache.spark.sql.cassandra") \
        .options(keyspace="mykeyspace", table="price_candlestick", url=conn.get_uri()) \
        .load()

    df.show()
    # print the length of the dataframe
    logging.info("The dataframe has {} rows.".format(df.count()))

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