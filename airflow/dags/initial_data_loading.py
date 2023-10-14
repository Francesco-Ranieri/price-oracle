import os
import logging
from datetime import datetime
from common.tasks.fetch_data import fetch_data
from common.tasks.cassandra import insert_into_cassandra

from airflow import DAG

logging.basicConfig(level=logging.DEBUG)

file_names = [file_name for file_name in os.listdir("assets") if file_name.endswith(".csv")]
for file_name in file_names:
    coin_name = file_name.split("_")[1].lower()
    with DAG(
        f"initial_data_loading_{coin_name}",
        schedule="@once",
        start_date=datetime.now(),
        default_args={
            "owner": "ranierifr"
        },
        is_paused_upon_creation=False,
        tags=[coin_name]
    ) as dag:
        ohlc_data = fetch_data(f"assets/{file_name}")
        insert_into_cassandra(ohlc_data)
