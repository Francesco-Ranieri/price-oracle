import logging
from datetime import datetime
from typing import List

from airflow.decorators import task
from pyspark.sql import SparkSession
from tqdm import tqdm

from airflow import DAG


@task
def spark_task():
    logging.info("RUNNING SPARK TASK")
    spark = SparkSession.builder \
                .appName("CassandraSpark")  \
                .master("spark://price-oracle-spark-master-svc:7077")    \
                .getOrCreate()
    df = spark.read.format("org.apache.spark.sql.cassandra") \
            .options(table="price_candlestick", keyspace="mykeyspace") \
            .option("spark.cassandra.auth.username", "cassandra") \
            .option("spark.cassandra.auth.password", "Y2Fzc2FuZHJh") \
            .load()
    df.show()

logging.basicConfig(level=logging.INFO)

with DAG(
    "spark_load_data_from_cassandra",
    schedule="@once",
    start_date=datetime.now(),
    default_args={
        "owner": "ranierifr"
    },
    is_paused_upon_creation=False,
    tags=["spark"]
) as dag:
  spark_task()
