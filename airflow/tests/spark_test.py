import logging
from datetime import timedelta, datetime

from airflow.decorators import task
from pyspark.sql import SparkSession

from airflow import DAG

logging.basicConfig(level=logging.INFO)

@task
def spark_task():
    logging.info("RUNNING SPARK TASK")
    spark = SparkSession.builder \
                .appName("CassandraSpark") \
                .master("spark://172.18.0.2:31493") \
                .getOrCreate()
    df = spark.read.format("org.apache.spark.sql.cassandra") \
            .options(table="price_candlestick", keyspace="mykeyspace") \
            .option("spark.cassandra.auth.username", "cassandra") \
            .option("spark.cassandra.auth.password", "Y2Fzc2FuZHJh") \
            .load()
    df.show()

if __name__ == "__main__":

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

        dag.test()