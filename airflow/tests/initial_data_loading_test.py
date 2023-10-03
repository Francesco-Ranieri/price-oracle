import os
import sys
from datetime import datetime, timedelta

from airflow import DAG

root_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
dags_folder = os.path.join(root_folder, 'dags')
sys.path.append(dags_folder)

from common.tasks.fetch_data import fetch_data
from common.tasks.cassandra import insert_into_cassandra

if __name__ == "__main__":

    file_names = os.listdir("airflow/assets")
    
    for file_name in file_names:
        coin_name = file_name.split("_")[1].lower()
        
        with DAG(
            f"initial_data_loading_{coin_name}",
            start_date=datetime.now() - timedelta(days=1)
        ) as test_dag:
            ohlc_data = fetch_data(f"airflow/assets/{file_name}")
            insert_into_cassandra(ohlc_data)

        test_dag.test()
