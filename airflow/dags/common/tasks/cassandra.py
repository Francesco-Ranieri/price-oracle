from typing import List

from airflow.decorators import task
from common.entities.price_candlestick import PriceCandleStick
from common.entities.indicators import Indicators
from tqdm import tqdm


@task
def insert_into_cassandra_price_candlestick(data: List[PriceCandleStick]):
    
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
    
    for row in tqdm(data):
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
                "period_name": row.period_name
            }
        )


@task
def insert_into_cassandra_indicators(data: List[Indicators]):
    from common.hooks.cassandra_hook import CassandraHook

    cassandra_hook = CassandraHook()
    insert_query = """
        INSERT INTO
            indicators (close_time_date, coin, ema_12, ema_26, ema_50, ema_100, ema_200, sma_5, sma_10, sma_20, sma_50, sma_100, sma_200)
        VALUES
            (
                %(close_time_date)s,
                %(coin)s,
                %(ema_12)s,
                %(ema_26)s,
                %(ema_50)s,
                %(ema_100)s,
                %(ema_200)s,
                %(sma_5)s,
                %(sma_10)s,
                %(sma_20)s,
                %(sma_50)s,
                %(sma_100)s,
                %(sma_200)s
            )
    """

    for row in tqdm(data):
        cassandra_hook.run_query(
            insert_query,
            parameters={
                "close_time_date": row.close_time_date,
                "coin": row.coin,
                "ema_12": row.ema_12,
                "ema_26": row.ema_26,
                "ema_50": row.ema_50,
                "ema_100": row.ema_100,
                "ema_200": row.ema_200,
                "sma_5": row.sma_5,
                "sma_10": row.sma_10,
                "sma_20": row.sma_20,
                "sma_50": row.sma_50,
                "sma_100": row.sma_100,
                "sma_200": row.sma_200
            }
        )