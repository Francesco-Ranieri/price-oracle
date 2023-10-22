import logging
import os
from datetime import datetime
from typing import List

from airflow.operators.python import PythonOperator
from common.dtos.binance_data_dto import BinanceDataDTO
from common.entities.price_candlestick import PriceCandleStick
from common.mappers.binance_data_mapper import BinanceDataMapper
from common.tasks.cassandra import insert_into_cassandra_price_candlestick
from common.constants import DATA_PATH, FILE_NAMES
from airflow import DAG

logging.basicConfig(level=logging.DEBUG)



def fetch_data(file_path: str) -> PriceCandleStick:
    """
    Load data from CSV and convert into PriceCandleStick
    """
    
    import pandas as pd

    df = pd.read_csv(file_path, skiprows=1)
    df = df.rename(columns={
        df.columns[-3]: "volume_crypto",
        df.columns[-2]: "volume_usd"
    })

    data = df.to_dict("records") 
    data: List[BinanceDataDTO] = [BinanceDataDTO.model_validate(item) for item in data]
    data: List[PriceCandleStick] = [BinanceDataMapper.to_price_candlestick(item) for item in data]

    return data


for file_name in FILE_NAMES:
    coin_name = file_name.split(".")[0]
    with DAG(
        f"initial_data_loading_{coin_name}",
        schedule="@once",
        start_date=datetime.now(),
        default_args={
            "owner": "ranierifr"
        },
        is_paused_upon_creation=True,
        tags=[coin_name]
    ) as dag:
        
        
        fetch_data_task = PythonOperator(
            task_id="fetch_data",
            python_callable=fetch_data,
            op_kwargs={
                "file_path": os.path.join(DATA_PATH, {file_name})
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