import logging
from datetime import datetime, timedelta
from typing import List

from airflow.operators.python import PythonOperator
from common.api.kraken import KrakenClient
from common.constants import FILE_NAMES
from common.dtos.kraken_dto import KrakenDTO
from common.entities.price_candlestick import PriceCandleStick
from common.mappers.kraken_mapper import KrakenMapper
from common.tasks.cassandra import insert_into_cassandra_price_candlestick

from airflow import DAG

logging.basicConfig(level=logging.DEBUG)


def fetch_data(
    coin_name: str,
    **kwargs
) -> [PriceCandleStick]:
    # This task is requesting data starting from the logical date.
    # The API returns all data between the logical date and now. (with a limit of a certain number of data points).
    # However, we still schedule this task to run every day at 8am.

    since = int(datetime.timestamp(kwargs["logical_date"]))
    
    data: KrakenDTO = KrakenClient().fetch_ohlc_data(
        coin_pair=coin_name, since=since
    )
    
    # Dirty trick to handle the fact that Kraken uses XBT instead of BTC
    kraken_coin_pair = coin_name
    if coin_name == "BTCUSDT":
        kraken_coin_pair = "XBTUSDT"

    ohlc_data: List[PriceCandleStick] = KrakenMapper.to_price_candlestick(
        data.result[kraken_coin_pair],
        coin_name,
        "1440"
    )

    return ohlc_data


for file_name in FILE_NAMES:
    coin_name = file_name.split(".")[0]

    with DAG(
        f"fetch_daily_ohlc_{coin_name}",
        start_date=datetime(2023, 10, 18),
        schedule_interval="0 8 * * *",
        catchup=True,
        default_args={
            "owner": "gianfranco",
            "depends_on_past": False,
            "retry_delay": timedelta(minutes=1),
            "retries": 5,
        },
        tags=["fetch_data", coin_name]
    ) as dag:

        fetch_data_task = PythonOperator(
            task_id="fetch_data",
            python_callable=fetch_data,
            op_args=[coin_name],
        )

        insert_into_cassandra_price_candlestick_task = PythonOperator(
            task_id="insert_into_cassandra_price_candlestick",
            python_callable=insert_into_cassandra_price_candlestick,
            op_args=[fetch_data_task.output],
        )
