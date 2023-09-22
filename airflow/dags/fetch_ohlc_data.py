import logging
from datetime import datetime, timedelta
from typing import List

from airflow.decorators import task
from common.api.cryptowatch import CryptoWatchClient
from common.entities.price_candlestick import PriceCandleStick
from common.tasks.cassandra import insert_into_cassandra

from airflow import DAG

logging.basicConfig(level=logging.DEBUG)


@task
def fetch_data(**kwargs) -> PriceCandleStick:
    crypto_client = CryptoWatchClient(exchange="binance")
    coin_pair = "BTCUSDT"

    # after paramter should be the logical start date of the DAG
    # before parameter should be 1 hour after the logical start date of the DAG
    after = int(datetime.timestamp(kwargs["logical_date"]))
    before = int(datetime.timestamp(
        kwargs["logical_date"] + timedelta(weeks=1)))

    logging.info(after)
    logging.info(before)
    ohlc_data = crypto_client.fetch_ohlc_data(
        coin_pair=coin_pair, after=after, before=before
    )
    logging.info(ohlc_data)
    return ohlc_data

with DAG(
    "bitcoin_ohlc_fetch_hourly",
    start_date=datetime(2018, 1, 1),
    # start_date=datetime(2021, 1, 1),  # Start from September 1, 2023
    schedule_interval=timedelta(weeks=1),  # Run every hour
    catchup=True,
    default_args={
        "owner": "gianfranco",
        "depends_on_past": False,
        # 'retries': 10,
        "retry_delay": timedelta(minutes=5),
    },
) as dag:
    ohlc_data = fetch_data()
    insert_into_cassandra(ohlc_data)
