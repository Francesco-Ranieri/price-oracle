import logging
import os
from datetime import datetime
from typing import List

from airflow.operators.python import PythonOperator
from common.dtos.crypto_data_dto import CryptoDataDTO
from common.entities.price_candlestick import PriceCandleStick
from common.mappers.crypto_data_mapper import CryptoDataMapper
from common.tasks.cassandra import insert_into_cassandra_price_candlestick

from airflow import DAG

logging.basicConfig(level=logging.DEBUG)



def fetch_data(file_path: str) -> PriceCandleStick:
    """
    Load data from CSV and convert into PriceCandleStick
    """
    
    import pandas as pd

    df = pd.read_csv(file_path, skiprows=1)
    df = df.rename(columns={
        df.columns[-2]: "volume_crypto",
        df.columns[-1]: "volume_usd"
    })

    data = df.to_dict("records") 
    data: List[CryptoDataDTO] = [CryptoDataDTO.model_validate(item) for item in data]
    data: List[PriceCandleStick] = [CryptoDataMapper.to_price_candlestick(item) for item in data]

    return data


file_names = [file_name for file_name in os.listdir("assets") if file_name.endswith(".csv")]
for file_name in file_names:
    coin_name = file_name.split("_")[1]
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
        
        
        fetch_data_task = PythonOperator(
            task_id="fetch_data",
            python_callable=fetch_data,
            op_kwargs={
                "file_path": f"assets/{file_name}"
            }
        )

        insert_into_cassandra_price_candlestick_task = PythonOperator(
            task_id="insert_into_cassandra_price_candlestick",
            python_callable=insert_into_cassandra_price_candlestick,
            op_kwargs={
                "data": fetch_data_task.output
            }
        )

        fetch_data_task >> insert_into_cassandra_price_candlestick_task