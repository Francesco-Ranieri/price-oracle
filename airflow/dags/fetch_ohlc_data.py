import json
import logging
from datetime import datetime, timedelta
from typing import List

from airflow.decorators import task
from common.api.cryptowatch import CryptoWatchClient
from common.entities.price_candlestick import PriceCandlestick

from airflow import DAG

logging.basicConfig(level=logging.DEBUG)


@task
def fetch_data(**kwargs) -> PriceCandlestick:
    crypto_client = CryptoWatchClient(exchange="binance")
    coin_pair = "BTCUSDT"

    # after paramter should be the logical start date of the DAG
    # before parameter should be 1 hour after the logical start date of the DAG
    after = int(datetime.timestamp(kwargs["logical_date"]))
    before = int(datetime.timestamp(kwargs["logical_date"] + timedelta(weeks=1)))

    logging.info(after)
    logging.info(before)
    ohlc_data = crypto_client.fetch_ohlc_data(
        coin_pair=coin_pair, after=after, before=before
    )
    logging.info(ohlc_data)
    return ohlc_data


@task
def insert_into_cassandra(data: List[PriceCandlestick]):
    from common.hooks.cassandra_hook import CassandraHook

    cassandra_hook = CassandraHook()
    insert_query = """
        INSERT INTO 
            price_candlestick (close_time, close_time_date, open_price, high_price, low_price, close_price, volume, quote_volume, coin, period, period_name)
        VALUES 
            (
                %(close_time)s,
                %(close_time_date)s,
                %(open_price)s,
                %(high_price)s,
                %(low_price)s,
                %(close_price)s,
                %(volume)s,
                %(quote_volume)s,
                %(coin)s,
                %(period)s,
                %(period_name)s
            )
    """

    for row in data:
        cassandra_hook.run_query(
            insert_query,
            parameters={
                "close_time": row.close_time,
                "close_time_date": row.close_time_date,
                "open_price": row.open_price,
                "high_price": row.high_price,
                "low_price": row.low_price,
                "close_price": row.close_price,
                "volume": row.volume,
                "quote_volume": row.quote_volume,
                "coin": row.coin,
                "period": row.period,
                "period_name": row.period_name,
            },
        )


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
