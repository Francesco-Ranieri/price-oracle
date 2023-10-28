from typing import List

from common.entities.price_candlestick import PriceCandleStick
from common.entities.indicators import Indicators
from common.entities.prediction import Prediction
from common.entities.metrics import Metrics
from common.hooks.cassandra_hook import CassandraHook


def insert_into_cassandra_price_candlestick(data: List[PriceCandleStick]):

    cassandra_hook = CassandraHook()
    insert_query = """
        INSERT INTO 
            price_candlestick (close_time, close_time_date, open_price, high_price, low_price, close_price, volume, quote_volume, coin, period, period_name)
        VALUES 
            (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """
    params = [
        (
            row.close_time,
            row.close_time_date,
            row.open_price,
            row.high_price,
            row.low_price,
            row.close_price,
            row.volume,
            row.quote_volume,
            row.coin,
            row.period,
            row.period_name
        ) for row in data
    ]
    cassandra_hook.run_batch_query(insert_query, params)


def insert_into_cassandra_indicators(data: List[Indicators]):

    cassandra_hook = CassandraHook()
    insert_query = """
        INSERT INTO
            indicators (close_time_date, coin, sma_5, sma_10, sma_20, sma_50, sma_100, sma_200)
        VALUES
            (?, ?, ?, ?, ?, ?, ?, ?)
    """
    params = [
        (
            row.close_time_date,
            row.coin,
            row.sma_5,
            row.sma_10,
            row.sma_20,
            row.sma_50,
            row.sma_100,
            row.sma_200
        ) for row in data
    ]
    cassandra_hook.run_batch_query(insert_query, params)


def insert_into_cassandra_predictions(data: List[Prediction]):

    cassandra_hook = CassandraHook()
    insert_query = """
        INSERT INTO
            prediction (close_time_date, close_price, coin, model_name)
        VALUES
            (?, ?, ?, ?);
    """
    params = [
        (
            row.close_time_date,
            row.close_price,
            row.coin,
            row.model_name
        ) for row in data
    ]
    cassandra_hook.run_batch_query(insert_query, params)


def insert_into_cassandra_metrics(data: List[Metrics]):

    cassandra_hook = CassandraHook()
    insert_query = """
        INSERT INTO
            metrics (metric_name, date, target, metric_all, metric_90_d, metric_30_d, metric_7_d, model_name)
        VALUES
            (?, ?, ?, ?, ?, ?, ?, ?);
    """
    params = [
        (
            row.metric_name,
            row.date,
            row.target,
            row.metric_all,
            row.metric_90_d,
            row.metric_30_d,
            row.metric_7_d,
            row.model_name
        ) for row in data
    ]
    cassandra_hook.run_batch_query(insert_query, params)
