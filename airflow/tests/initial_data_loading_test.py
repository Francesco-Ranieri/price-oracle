import os
import sys
from datetime import datetime, timedelta

from airflow import DAG

root_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
dags_folder = os.path.join(root_folder, 'dags')
sys.path.append(dags_folder)

from initial_data_loading import fetch_data, insert_into_cassandra

if __name__ == "__main__":
    with DAG(
        "initial_data_loading_btcusdt",
        start_date=datetime.now() - timedelta(days=1),
        default_args={
            "owner": "ranierifr"
        }
    ) as test_dag:
        ohlc_data = fetch_data("airflow/assets/Gemini_BTCUSD_1h.csv")
        insert_into_cassandra(ohlc_data)

    test_dag.test()