import logging
from datetime import datetime, timedelta

from airflow.decorators import task
from common.api.cryptowatch import CryptoWatchClient
from common.dtos.price_candlestick import PriceCandlestick

from airflow import DAG


@task
def fetch_data(**kwargs) -> PriceCandlestick:
    crypto_client = CryptoWatchClient(exchange="binance")
    coin_pair = "BTCUSDT"

    # after paramter should be the logical start date of the DAG
    # before parameter should be 1 hour after the logical start date of the DAG
    after = int(datetime.timestamp(kwargs["logical_date"]))
    before = int(datetime.timestamp(kwargs["logical_date"] + timedelta(hours=1)))

    logging.info(after)
    logging.info(before)
    ohlc_data = crypto_client.fetch_ohlc_data(
        coin_pair=coin_pair, after=after, before=before
    )
    logging.info(ohlc_data)
    return ohlc_data[0].__dict__


@task
def insert_into_cassandra(data: dict):
    from common.hooks.cassandra_hook import CassandraHook

    cassandra_hook = CassandraHook()

    # convert timestamp to datetime
    data["close_time_date"] = datetime.fromtimestamp(data["close_time"])

    insert_query = """
    INSERT INTO price_candlestick (close_time, close_time_date, open_price, high_price, low_price, close_price, volume, quote_volume, coin)
    VALUES (%(close_time)s, %(close_time_date)s, %(open_price)s, %(high_price)s, %(low_price)s, %(close_price)s, %(volume)s, %(quote_volume)s, %(coin)s)
    """

    cassandra_hook.run_query(insert_query, parameters=data)


with DAG(
    "bitcoin_ohlc_fetch_hourly",
    start_date=datetime(2023, 9, 19, 22),  # Start from September 1, 2023
    schedule_interval=timedelta(hours=1),  # Run every hour
    catchup=True,
    default_args={
        "owner": "gianfranco",
        "depends_on_past": False,
        #'retries': 10,
        "retry_delay": timedelta(minutes=5),
    },
) as dag:
    ohlc_data = fetch_data()
    insert_into_cassandra(ohlc_data)
