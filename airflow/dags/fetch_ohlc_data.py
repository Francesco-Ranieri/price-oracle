import logging
import os
from datetime import datetime, timedelta

import cryptowatch
from airflow.decorators import task

from airflow import DAG


@task
def fetch_data(**kwargs):
    crypto_client = cryptowatch.CryptoWatchClient(exchange="binance")
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

@task 
def upload_to_cassandra(**kwargs):

    cassandra_host = os.getenv('PRICE_ORACLE_CASSANDRA_SERVICE_HOST')
    cassandra_host = "10.96.163.75"
    cassandra_port = os.getenv('PRICE_ORACLE_CASSANDRA_SERVICE_PORT')

    if not cassandra_host or not cassandra_port:
        raise Exception('Cassandra host or port not found')



    from cassandra.cluster import Cluster
    from cassandra.auth import PlainTextAuthProvider
    auth_provider = PlainTextAuthProvider(username="cassandra", password="phaqt2dnxy")
    
    with Cluster([cassandra_host],auth_provider = auth_provider) as cluster:
        with cluster.connect('mykeyspace') as session:
            
            data = {
                'id': 1,
                'coin': 'bitcoin'
            }
            insert_query = """
            INSERT INTO price_candlestick (coin)
            VALUES (%(coin)s)
            """

            session.execute(insert_query, data)


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
    fetch_data() >> upload_to_cassandra()
