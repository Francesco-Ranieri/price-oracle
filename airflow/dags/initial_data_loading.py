import logging
from datetime import datetime
from typing import List

from airflow.decorators import task
from common.dtos.crypto_data_dto import CryptoDataDTO
from common.entities.price_candlestick import PriceCandleStick
from common.mapper.crypto_data_mapper import CryptoDataMapper
from common.tasks.cassandra import insert_into_cassandra

from airflow import DAG

logging.basicConfig(level=logging.DEBUG)


@task
def fetch_data(file_path: str) -> PriceCandleStick:
    """
    Load data from CSV and convert into PriceCandleStick
    """
    
    import pandas as pd

    df = pd.read_csv(file_path)
    data = df.to_dict("records") 
    data: List[CryptoDataDTO] = [CryptoDataDTO.model_validate(item) for item in data]
    data: List[PriceCandleStick] = [CryptoDataMapper.to_price_candlestick(item) for item in data]

    return data

with DAG(
    "initial_data_loading_btcusdt",
    schedule="@once",
    catchup=True,
    start_date=datetime.now(),
    default_args={
        "owner": "ranierifr"
    },
) as dag:
    ohlc_data = fetch_data("assets/Gemini_BTCUSD_1h.csv")
    insert_into_cassandra(ohlc_data)


with DAG(
    "initial_data_loading_ethusdt",
    schedule="@once",
    catchup=True,
    start_date=datetime.now(),
    default_args={
        "owner": "ranierifr"
    },
) as dag:
    ohlc_data = fetch_data("assets/Gemini_BTCUSD_1h.csv")
    insert_into_cassandra(ohlc_data)